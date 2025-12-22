import io
import qrcode
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def generate_qr(data):
    """Generates a QR Code and returns it as a base64 string for HTML"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to memory buffer
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def generate_certificate(name, team_name, event_name="SapthaHack 2025"):
    """Generates a PDF Certificate in memory"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- DESIGN ---
    # Background (Dark Cyber Theme) - Simple rectangle simulation
    c.setFillColorRGB(0.05, 0.05, 0.1) # Dark Blue/Black
    c.rect(0, 0, width, height, fill=1)
    
    # Border
    c.setStrokeColorRGB(0, 0.9, 1) # Neon Cyan
    c.setLineWidth(5)
    c.rect(20, 20, width-40, height-40)

    # Title
    c.setFillColorRGB(0, 0.9, 1) # Neon Cyan
    c.setFont("Helvetica-Bold", 40)
    c.drawCentredString(width/2, height - 150, "CERTIFICATE")
    c.setFont("Helvetica", 20)
    c.drawCentredString(width/2, height - 190, "OF PARTICIPATION")

    # Content
    c.setFillColorRGB(1, 1, 1) # White
    c.setFont("Helvetica", 15)
    c.drawCentredString(width/2, height - 250, "This is to certify that")
    
    # Name
    c.setFont("Helvetica-Bold", 30)
    c.setFillColorRGB(1, 0.5, 0) # Orange/Gold
    c.drawCentredString(width/2, height - 300, name)
    
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica", 15)
    c.drawCentredString(width/2, height - 340, f"of Team '{team_name}'")
    c.drawCentredString(width/2, height - 370, f"has successfully participated in {event_name}.")

    # Signature Area
    c.setLineWidth(2)
    c.line(width/2 - 100, 150, width/2 + 100, 150)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, 135, "EVENT DIRECTOR")

    c.save()
    buffer.seek(0)
    return buffer