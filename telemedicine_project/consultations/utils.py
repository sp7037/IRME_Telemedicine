from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from io import BytesIO
from consultations.models import Prescription

def generate_prescription_pdf(prescription_id):
    """Generate a PDF prescription file"""
    prescription = Prescription.objects.get(id=prescription_id)
    
    # Create a PDF buffer
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    # PDF Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "Medical Prescription")

    # Doctor Information
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 720, f"Doctor: {prescription.doctor.user.get_full_name()}")
    pdf.drawString(50, 700, f"Patient: {prescription.patient.user.get_full_name()}")

    # Prescription Details
    pdf.drawString(50, 660, "Medicines:")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(70, 640, prescription.medicines)

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 600, "Instructions:")
    pdf.setFont("Helvetica", 11)
    pdf.drawString(70, 580, prescription.instructions if prescription.instructions else "No special instructions.")

    # Save PDF
    pdf.showPage()
    pdf.save()
    
    buffer.seek(0)
    
    # Return PDF as response
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="prescription_{prescription.id}.pdf"'
    
    return response
