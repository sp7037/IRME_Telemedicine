from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Consultation, ConsultationEvent


class TransitionError(Exception):
    pass


ALLOWED_TRANSITIONS = {
    Consultation.StatusChoices.PENDING: {
        Consultation.StatusChoices.ACCEPTED,
        Consultation.StatusChoices.POSTPONED,
        Consultation.StatusChoices.REJECTED,
        Consultation.StatusChoices.CANCELED,
    },
    Consultation.StatusChoices.ACCEPTED: {
        Consultation.StatusChoices.QUEUED,
        Consultation.StatusChoices.IN_PROGRESS,
        Consultation.StatusChoices.CANCELED,
    },
    Consultation.StatusChoices.QUEUED: {
        Consultation.StatusChoices.IN_PROGRESS,
        Consultation.StatusChoices.CANCELED,
    },
    Consultation.StatusChoices.IN_PROGRESS: {
        Consultation.StatusChoices.COMPLETED,
    },
    Consultation.StatusChoices.POSTPONED: {
        Consultation.StatusChoices.PENDING,
        Consultation.StatusChoices.REJECTED_BY_PATIENT,
        Consultation.StatusChoices.CANCELED,
    },
    Consultation.StatusChoices.REJECTED_BY_PATIENT: set(),
    Consultation.StatusChoices.REJECTED: set(),
    Consultation.StatusChoices.CANCELED: set(),
    Consultation.StatusChoices.COMPLETED: set(),
}


def _create_event(
    consultation,
    event_type,
    actor=None,
    from_status=None,
    to_status=None,
    note=None,
    suggested_time=None,
    metadata=None,
):
    ConsultationEvent.objects.create(
        consultation=consultation,
        event_type=event_type,
        actor=actor,
        from_status=from_status,
        to_status=to_status,
        note=note,
        suggested_time=suggested_time,
        metadata=metadata or {},
    )


def _reindex_queue(doctor):
    queued = (
        Consultation.objects.select_for_update()
        .filter(doctor=doctor, status=Consultation.StatusChoices.QUEUED)
        .order_by("queue_number", "created_at")
    )
    for idx, item in enumerate(queued, start=1):
        if item.queue_number != idx:
            item.queue_number = idx
            item.save(update_fields=["queue_number"])


def add_to_queue(consultation):
    doctor = consultation.doctor
    queued = (
        Consultation.objects.select_for_update()
        .filter(doctor=doctor, status=Consultation.StatusChoices.QUEUED)
        .exclude(id=consultation.id)
    )
    next_position = queued.count() + 1
    consultation.status = Consultation.StatusChoices.QUEUED
    consultation.queue_number = next_position
    consultation.last_status_changed_at = timezone.now()
    consultation.save(update_fields=["status", "queue_number", "last_status_changed_at"])


@transaction.atomic
def transition_consultation(
    consultation_id,
    to_status,
    actor=None,
    note=None,
    suggested_time=None,
    metadata=None,
):
    consultation = Consultation.objects.select_for_update().get(id=consultation_id)
    from_status = consultation.status

    if to_status not in ALLOWED_TRANSITIONS.get(from_status, set()):
        raise TransitionError(f"Invalid transition from {from_status} to {to_status}.")

    consultation.status = to_status
    consultation.status_changed_by = actor
    consultation.last_status_changed_at = timezone.now()
    consultation.terminal_reason = note if to_status in {
        Consultation.StatusChoices.CANCELED,
        Consultation.StatusChoices.REJECTED,
        Consultation.StatusChoices.REJECTED_BY_PATIENT,
    } else consultation.terminal_reason

    clear_suggested_time = to_status in {
        Consultation.StatusChoices.PENDING,
        Consultation.StatusChoices.REJECTED_BY_PATIENT,
        Consultation.StatusChoices.CANCELED,
        Consultation.StatusChoices.REJECTED,
        Consultation.StatusChoices.COMPLETED,
    }

    if suggested_time is not None:
        consultation.new_suggested_time = suggested_time
    elif clear_suggested_time:
        consultation.new_suggested_time = None

    if to_status in {
        Consultation.StatusChoices.CANCELED,
        Consultation.StatusChoices.REJECTED,
        Consultation.StatusChoices.COMPLETED,
        Consultation.StatusChoices.IN_PROGRESS,
        Consultation.StatusChoices.REJECTED_BY_PATIENT,
    }:
        consultation.queue_number = None

    if to_status == Consultation.StatusChoices.COMPLETED:
        consultation.is_completed = True

    fields = [
        "status",
        "status_changed_by",
        "last_status_changed_at",
        "queue_number",
        "terminal_reason",
        "is_completed",
    ]
    if suggested_time is not None or clear_suggested_time:
        fields.append("new_suggested_time")
    consultation.save(update_fields=list(set(fields)))

    if to_status in {
        Consultation.StatusChoices.CANCELED,
        Consultation.StatusChoices.REJECTED,
        Consultation.StatusChoices.COMPLETED,
        Consultation.StatusChoices.IN_PROGRESS,
    }:
        _reindex_queue(consultation.doctor)

    event_map = {
        Consultation.StatusChoices.ACCEPTED: ConsultationEvent.EventType.ACCEPTED,
        Consultation.StatusChoices.QUEUED: ConsultationEvent.EventType.QUEUED,
        Consultation.StatusChoices.IN_PROGRESS: ConsultationEvent.EventType.STARTED,
        Consultation.StatusChoices.POSTPONED: ConsultationEvent.EventType.POSTPONED,
        Consultation.StatusChoices.REJECTED: ConsultationEvent.EventType.REJECTED,
        Consultation.StatusChoices.CANCELED: ConsultationEvent.EventType.CANCELED,
        Consultation.StatusChoices.COMPLETED: ConsultationEvent.EventType.COMPLETED,
        Consultation.StatusChoices.REJECTED_BY_PATIENT: ConsultationEvent.EventType.POSTPONE_REJECTED,
    }
    event_type = event_map.get(to_status)
    if event_type:
        _create_event(
            consultation,
            event_type,
            actor=actor,
            from_status=from_status,
            to_status=to_status,
            note=note,
            suggested_time=suggested_time,
            metadata=metadata,
        )

    return consultation

