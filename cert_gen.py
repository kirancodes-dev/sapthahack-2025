from PIL import Image, ImageDraw, ImageFont
import io
import requests

def create_certificate(student_name, team_name):
    # --- 1. SETUP CANVAS ---
    width, height = 1200, 850
    # Create White Background
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Define Colors
    uni_blue = (0, 51, 102)   # #003366
    uni_gold = (255, 204, 0)  # #FFCC00
    grey_text = (80, 80, 80)

    # --- 2. DRAW PROFESSIONAL BORDERS ---
    # Thick Blue Outer Border
    draw.rectangle([20, 20, width-20, height-20], outline=uni_blue, width=15)
    # Thin Gold Inner Border
    draw.rectangle([45, 45, width-45, height-45], outline=uni_gold, width=5)
    # Corner Accents (Decorative)
    draw.rectangle([15, 15, 100, 100], fill=uni_blue) # Top Left
    draw.rectangle([width-100, 15, width-15, 100], fill=uni_blue) # Top Right
    draw.rectangle([15, height-100, 100, height-15], fill=uni_blue) # Bottom Left
    draw.rectangle([width-100, height-100, width-15, height-15], fill=uni_blue)

    # --- 3. ADD UNIVERSITY LOGO ---
    try:
        # Fetch the logo dynamically from the URL you provided
        logo_url = "https://snpsu.edu.in/wp-content/uploads/2024/03/asjfghdasid-1.png"
        logo_response = requests.get(logo_url, stream=True)
        logo = Image.open(logo_response.raw).convert("RGBA")
        
        # Resize logo to fit nicely
        logo.thumbnail((400, 120))
        
        # Calculate center position
        logo_w, logo_h = logo.size
        img.paste(logo, ((width - logo_w) // 2, 80), logo)
    except Exception as e:
        print(f"Logo Error: {e}")
        # Fallback text if logo fails
        draw.text((width/2, 100), "SAPTHAGIRI NPS UNIVERSITY", fill=uni_blue, anchor="mm")

    # --- 4. TEXT CONTENT ---
    # Helper to load fonts safely (Linux paths for PythonAnywhere)
    def get_font(size, bold=False):
        try:
            path = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            return ImageFont.truetype(path, size)
        except:
            return ImageFont.load_default()

    # Titles
    draw.text((width/2, 230), "CERTIFICATE OF ACHIEVEMENT", fill=uni_gold, anchor="mm", font=get_font(50, bold=True))
    draw.text((width/2, 280), "PROUDLY PRESENTED TO", fill=grey_text, anchor="mm", font=get_font(20))

    # Student Name (Big & Blue)
    draw.text((width/2, 350), student_name.upper(), fill=uni_blue, anchor="mm", font=get_font(60, bold=True))
    
    # Underline Name
    draw.line((300, 390, 900, 390), fill=uni_gold, width=3)

    # Context
    body_text = f"For active participation and excellence as a member of Team '{team_name}'"
    draw.text((width/2, 440), body_text, fill=grey_text, anchor="mm", font=get_font(24))
    
    draw.text((width/2, 490), "during the National Level Hackathon", fill=grey_text, anchor="mm", font=get_font(20))
    draw.text((width/2, 540), "SAPTHAHACK 2025", fill=uni_blue, anchor="mm", font=get_font(40, bold=True))
    draw.text((width/2, 590), "Held on May 15th - 16th, 2025 at Bengaluru Campus", fill=grey_text, anchor="mm", font=get_font(18))

    # --- 5. SIGNATURES ---
    # Left Signature (Registrar)
    draw.line((200, 720, 450, 720), fill=uni_blue, width=2)
    draw.text((325, 740), "Prof. Gurucharan Singh", fill=uni_blue, anchor="mm", font=get_font(20, bold=True))
    draw.text((325, 765), "Registrar", fill=grey_text, anchor="mm", font=get_font(16))
    
    # Fake Script Signature (Visual trick)
    draw.text((325, 690), "Gurucharan. S", fill=(0, 51, 102), anchor="mm", font=get_font(25)) # Placeholder for signature image

    # Right Signature (Vice Chancellor)
    draw.line((750, 720, 1000, 720), fill=uni_blue, width=2)
    draw.text((875, 740), "Dr. Jayanthi V", fill=uni_blue, anchor="mm", font=get_font(20, bold=True))
    draw.text((875, 765), "Vice Chancellor", fill=grey_text, anchor="mm", font=get_font(16))
    
    # Fake Script Signature
    draw.text((875, 690), "Jayanthi. V", fill=(0, 51, 102), anchor="mm", font=get_font(25)) 

    # --- 6. SAVE ---
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output