from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_sample_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Security Audit Report")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, "Finding 1: high_risk_vulnerability")
    c.drawString(50, height - 100, "Severity: Critical")
    c.drawString(50, height - 120, "Status: Open")
    c.drawString(50, height - 140, "Description: Found a critical vulnerability in the authentication module.")
    c.drawString(50, height - 160, "Recommendation: Update the auth library to version 2.0.")
    
    c.drawString(50, height - 200, "Finding 2: low_risk_warning")
    c.drawString(50, height - 220, "Severity: Low")
    c.drawString(50, height - 240, "Status: Closed")
    c.drawString(50, height - 260, "Description: Minor configuration issue.")
    
    c.save()

if __name__ == "__main__":
    create_sample_pdf("inputs/Audit_Work_PDFs/sample_report_1.pdf")
    create_sample_pdf("inputs/Audit_Work_PDFs/sample_report_2.pdf")
