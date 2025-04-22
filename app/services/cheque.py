import io
import random
import string
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register standard fonts to ensure availability
def register_standard_fonts():
    # We're intentionally not doing anything here. ReportLab's base 14 fonts
    # should be available, but we'll handle fallbacks in our code
    pass

def generate_cheque_number(prefix=""):
    """Generate a unique cheque number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{timestamp}{random_chars}"


def generate_deposit_cheque_pdf(username: str, amount: float, cheque_number: str) -> bytes:
    """Generate a PDF for a deposit cheque"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Set up styles
    styles = getSampleStyleSheet()
    
    # Add bank title
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 50, "Secure Bank")
    
    # Add cheque details
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 100, "DEPOSIT CHEQUE")
    
    # Add decorative border
    c.setStrokeColor(colors.navy)
    c.setLineWidth(2)
    c.rect(50, 100, width - 100, height - 200, stroke=1, fill=0)
    
    # Add fancy pattern
    c.setStrokeColor(colors.lightblue)
    c.setLineWidth(1)
    for i in range(10):
        c.line(70, 120 + i*20, width - 70, 120 + i*20)
    
    # Add cheque details
    c.setFont("Helvetica", 12)
    c.drawString(70, height - 150, f"Cheque No: {cheque_number}")
    c.drawString(70, height - 180, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(70, height - 210, f"Account Holder: {username}")
    
    # Add amount with fancy display
    c.setFont("Helvetica-Bold", 16)
    c.drawString(70, height - 260, "Amount:")
    
    # Draw amount box
    c.setStrokeColor(colors.black)
    c.rect(170, height - 270, 150, 30, stroke=1, fill=0)
    c.setFont("Courier-Bold", 16)
    c.drawRightString(310, height - 250, f"${amount:.2f}")
    
    # Add amount in words
    c.setFont("Helvetica", 12)
    c.drawString(70, height - 300, "This deposit is subject to verification by Secure Bank")
    
    # Add security features text - using Helvetica instead of Helvetica-Italic which may not be available
    c.setFont("Helvetica", 8)  # Changed from Helvetica-Italic to Helvetica
    c.drawString(70, 150, "This document contains security features. Hold up to light to verify watermark.")
    
    # Add signature line
    c.setFont("Helvetica", 12)
    c.line(width - 200, 180, width - 70, 180)
    c.drawCentredString(width - 135, 165, "Authorized Signature")
    
    # Add a reminder
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, 130, "DEPOSIT PENDING APPROVAL")
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def generate_withdraw_cheque_pdf(username: str, amount: float, cheque_number: str) -> bytes:
    """Generate a PDF for a withdrawal cheque"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Set up styles
    styles = getSampleStyleSheet()
    
    # Add bank title
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 50, "Secure Bank")
    
    # Add cheque details
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, height - 100, "WITHDRAWAL CHEQUE")
    
    # Add decorative border
    c.setStrokeColor(colors.darkred)
    c.setLineWidth(2)
    c.rect(50, 100, width - 100, height - 200, stroke=1, fill=0)
    
    # Add fancy pattern
    c.setStrokeColor(colors.pink)
    c.setLineWidth(1)
    for i in range(10):
        c.line(70, 120 + i*20, width - 70, 120 + i*20)
    
    # Add cheque details
    c.setFont("Helvetica", 12)
    c.drawString(70, height - 150, f"Cheque No: {cheque_number}")
    c.drawString(70, height - 180, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(70, height - 210, f"Pay to the order of: {username}")
    
    # Add amount with fancy display
    c.setFont("Helvetica-Bold", 16)
    c.drawString(70, height - 260, "Amount:")
    
    # Draw amount box
    c.setStrokeColor(colors.black)
    c.rect(170, height - 270, 150, 30, stroke=1, fill=0)
    c.setFont("Courier-Bold", 16)
    c.drawRightString(310, height - 250, f"${amount:.2f}")
    
    # Add security features text - using Helvetica instead of Helvetica-Italic
    c.setFont("Helvetica", 8)  # Changed from Helvetica-Italic to Helvetica
    c.drawString(70, 150, "This document contains security features. Hold up to light to verify watermark.")
    
    # Add signature line
    c.setFont("Helvetica", 12)
    c.line(width - 200, 180, width - 70, 180)
    c.drawCentredString(width - 135, 165, "Authorized Signature")
    
    # Add a reminder
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, 130, "WITHDRAWAL PENDING APPROVAL")
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue() 