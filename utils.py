import smtplib
import ssl
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CREDENTIALS ---
SMTP_EMAIL = "sapthhack@gmail.com"
SMTP_PASSWORD = "bbcw iimk ghvu pvof"

# Memory Storage for OTPs (Clears on restart)
otp_storage = {}

def generate_otp():
    """Generates a 6-digit numeric OTP"""
    return str(random.randint(100000, 999999))

def send_email(to_email, subject, body_html):
    """
    Sends an email with automatic fallback handling.
    Strategy 1: TLS (Port 587) - Modern standard
    Strategy 2: SSL (Port 465) - Legacy fallback
    """
    print(f"📧 Sending email to: {to_email}...")
    
    msg = MIMEMultipart()
    msg['From'] = f"SapthaHack Admin <{SMTP_EMAIL}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body_html, 'html'))
    
    # --- ATTEMPT 1: TLS (Port 587) ---
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
        print(f"✅ EMAIL SUCCESS (TLS)")
        return True
    except Exception as e1:
        print(f"⚠️ TLS Failed ({e1}). Retrying with SSL...")

        # --- ATTEMPT 2: SSL (Port 465) ---
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
            print(f"✅ EMAIL SUCCESS (SSL)")
            return True
        except Exception as e2:
            print(f"❌ CRITICAL EMAIL FAILURE: {e2}")
            return False