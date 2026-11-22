import json

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from io import BytesIO
from consultations.models import Prescription


def _format_medicines_for_pdf(medicines):
    if medicines is None:
        return "—"
    if isinstance(medicines, list):
        lines = []
        for i, item in enumerate(medicines, 1):
            if isinstance(item, dict):
                lines.append(json.dumps(item, ensure_ascii=False))
            else:
                lines.append(str(item))
        return "\n".join(lines) if lines else "—"
    return str(medicines)


def _medicine_value(item, *keys):
    if not isinstance(item, dict):
        return str(item or "")
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def _wrap_cell_text(value, col_width, max_lines=3):
    text = str(value or "-").strip() or "-"
    max_chars = max(6, int(col_width / 4.8))
    lines = []
    for raw in text.splitlines() or [""]:
        current = ""
        for word in raw.split():
            if len(current) + len(word) + 1 > max_chars:
                lines.append(current)
                current = word
            else:
                current = f"{current} {word}".strip()
        lines.append(current or raw)
    return lines[:max_lines]


def _draw_medicines_table(pdf, medicines, x, y, width, min_y=160):
    rows = medicines if isinstance(medicines, list) else []
    if not rows:
        rows = ["No medicines recorded."]

    fixed_width = 24 + 38 + 115 + 60 + 66 + 34
    columns = [
        ("Sr.", 24),
        ("Type", 38),
        ("Medicine", 115),
        ("Strength", 60),
        ("Frequency", 66),
        ("Days", 34),
        ("Notes", width - fixed_width),
    ]

    pdf.setFillColor(colors.HexColor("#eaf3fc"))
    pdf.rect(x, y - 17, width, 20, fill=True, stroke=False)
    pdf.setFillColor(colors.HexColor("#123a6f"))
    pdf.setFont("Helvetica-Bold", 8)
    cursor = x
    for title, col_width in columns:
        pdf.drawString(cursor + 4, y - 10, title)
        cursor += col_width

    pdf.setStrokeColor(colors.HexColor("#b9cce2"))
    pdf.line(x, y - 18, x + width, y - 18)
    y -= 32
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.black)

    for index, item in enumerate(rows[:18], 1):
        if y < min_y:
            break
        values = [
            str(index),
            _medicine_value(item, "medicine_type", "type"),
            _medicine_value(item, "name"),
            _medicine_value(item, "strength", "dosage", "power"),
            _medicine_value(item, "frequency"),
            _medicine_value(item, "duration_days", "days", "duration"),
            _medicine_value(item, "notes", "instructions"),
        ]
        wrapped_values = [
            _wrap_cell_text(value, col_width, max_lines=3 if title == "Notes" else 2)
            for value, (title, col_width) in zip(values, columns)
        ]
        row_height = max(20, max(len(lines) for lines in wrapped_values) * 10 + 8)
        cursor = x
        for lines, (_, col_width) in zip(wrapped_values, columns):
            line_y = y
            for line in lines:
                pdf.drawString(cursor + 4, line_y, line)
                line_y -= 10
            cursor += col_width
        pdf.setStrokeColor(colors.HexColor("#e1ebf6"))
        pdf.line(x, y - row_height + 6, x + width, y - row_height + 6)
        y -= row_height
    return y


def _draw_wrapped(pdf, text, x, y, max_chars=96, line_height=14, min_y=90):
    text = str(text or "")
    lines = []
    for raw in text.splitlines() or [""]:
        current = ""
        for word in raw.split():
            if len(current) + len(word) + 1 > max_chars:
                lines.append(current)
                current = word
            else:
                current = f"{current} {word}".strip()
        lines.append(current or raw)
    for line in lines:
        if y < min_y:
            break
        pdf.drawString(x, y, line[:max_chars])
        y -= line_height
    return y


def generate_prescription_pdf(prescription_id):
    """Generate a branded PDF prescription for download."""
    prescription = Prescription.objects.select_related(
        "doctor__user", "patient__user", "consultation"
    ).get(id=prescription_id)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    doctor = prescription.doctor
    patient = prescription.patient
    doctor_name = doctor.user.get_full_name() or doctor.user.email
    patient_name = patient.user.get_full_name() or patient.user.email

    # Header
    pdf.setFillColor(colors.HexColor("#0b3b68"))
    pdf.rect(0, height - 92, width, 92, fill=True, stroke=False)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(42, height - 44, "IRME Telemedicine")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(42, height - 62, "Rural India Deserves Best Medical Health Services")
    pdf.drawString(42, height - 76, "support@irme.in | www.irme.in")
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawRightString(width - 42, height - 44, "Medical Prescription")
    pdf.setFont("Helvetica", 9)
    pdf.drawRightString(width - 42, height - 62, f"Prescription ID: RX-{prescription.id}")

    # Doctor branding block
    y = height - 122
    pdf.setFillColor(colors.HexColor("#123a6f"))
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(42, y, f"Dr. {doctor_name}")
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 10)
    y -= 16
    pdf.drawString(42, y, f"Qualification: {doctor.degree or doctor.qualification or '-'}")
    y -= 14
    pdf.drawString(42, y, f"Specialty: {doctor.specialty or 'General Physician'}")
    y -= 14
    pdf.drawString(42, y, f"Registration No: {doctor.registration_number or doctor.license_number or '-'}")
    y -= 14
    location = ", ".join(filter(None, [doctor.city, f"({doctor.state})" if doctor.state else ""]))
    clinic_line = " - ".join(filter(None, [doctor.hospital_or_clinic_name, location]))
    pdf.drawString(42, y, f"Hospital/Clinic: {clinic_line or '-'}")

    # Patient/date block
    y = height - 122
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(330, y, "Patient")
    pdf.setFont("Helvetica", 10)
    y -= 16
    gender = patient.get_gender_display() if getattr(patient, "gender", None) else "-"
    age = f"{patient.age} yrs" if patient.age is not None else "-"
    pdf.drawString(330, y, f"{patient_name} ({gender}, {age})")
    y -= 14
    pdf.drawString(330, y, f"Email: {patient.user.email}")
    y -= 14
    pdf.drawString(330, y, f"Issued: {prescription.updated_at.strftime('%d %b %Y, %I:%M %p')}")

    # Divider
    y = height - 230
    pdf.setStrokeColor(colors.HexColor("#b9cce2"))
    pdf.line(42, y, width - 42, y)

    # Medicines
    y -= 28
    pdf.setFillColor(colors.HexColor("#123a6f"))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(42, y, "Medicines")
    y -= 18
    y = _draw_medicines_table(pdf, prescription.medicines, 42, y, width - 84)

    # Instructions
    y -= 10
    pdf.setFillColor(colors.HexColor("#123a6f"))
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(42, y, "Instructions")
    y -= 18
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 10)
    _draw_wrapped(
        pdf,
        prescription.instructions or "No special instructions.",
        58,
        y,
        max_chars=92,
        line_height=14,
        min_y=100,
    )

    # Footer
    pdf.setStrokeColor(colors.HexColor("#b9cce2"))
    pdf.line(42, 72, width - 42, 72)
    pdf.setFillColor(colors.HexColor("#4c6480"))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(42, 54, "Generated by IRME Telemedicine. This prescription is valid only for the named patient and consultation.")
    pdf.drawString(42, 40, "For emergencies, seek immediate in-person medical care.")
    pdf.drawRightString(width - 42, 40, f"Doctor registration: {doctor.registration_number or doctor.license_number or '-'}")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="IRME_prescription_RX-{prescription.id}.pdf"'

    return response
