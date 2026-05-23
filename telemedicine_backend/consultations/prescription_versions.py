"""Helpers for audit-safe prescription snapshots."""

import copy

from django.db.models import Max

from .models import PrescriptionVersion


def record_initial_version(prescription, user):
    """Call after creating a Prescription row (version 1 = issued state)."""
    return PrescriptionVersion.objects.create(
        prescription=prescription,
        version_number=1,
        medicines=copy.deepcopy(prescription.medicines) if prescription.medicines is not None else [],
        instructions=prescription.instructions or "",
        created_by=user,
    )


def archive_current_before_update(prescription, user):
    """
    Store the current prescription row as the next version number; caller then updates the row.
    If no versions exist yet (data anomaly), this creates version 1 from the current row.
    Call only when a content change is confirmed (see prescription_content_changed).
    """
    max_v = prescription.versions.aggregate(m=Max("version_number"))["m"] or 0
    next_num = max_v + 1
    meds = copy.deepcopy(prescription.medicines) if prescription.medicines is not None else []
    instr = prescription.instructions or ""
    return PrescriptionVersion.objects.create(
        prescription=prescription,
        version_number=next_num,
        medicines=meds,
        instructions=instr,
        created_by=user,
    )


def prescription_content_changed(
    prescription, *, medicines=None, instructions=None, touch_medicines=False, touch_instructions=False
):
    """Whether PUT changes stored content; use touch_* to indicate the field was sent in the body."""
    if touch_medicines and medicines != prescription.medicines:
        return True
    if touch_instructions and (instructions or "") != (prescription.instructions or ""):
        return True
    return False
