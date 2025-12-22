import smtplib
import ssl
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from firebase_config import db

# --- 🔒 SECURITY CREDENTIALS ---
SMTP_EMAIL = "sapthhack@gmail.com" 
SMTP_PASSWORD = "bbcw iimk ghvu pvof"  # <--- UPDATED PASSWORD

# --- 💾 MEMORY STORAGE (For OTPs) ---
otp_storage = {} 

# --- FIREBASE HELPERS ---
def get_all_events():
    try:
        docs = db.collection('events').stream()
        return [doc.to_dict() for doc in docs]
    except: return []

def get_all_teams():
    try:
        docs = db.collection('teams').stream()
        return {doc.id: doc.to_dict() for doc in docs}
    except: return {}

def get_all_judges():
    try:
        docs = db.collection('judges').stream()
        return {doc.id: doc.to_dict() for doc in docs}
    except: return {}

def get_all_scores():
    try:
        docs = db.collection('scores').stream()
        return {doc.id: doc.to_dict().get('score', 0) for doc in docs}
    except: return {}

def get_all_submissions():
    try:
        docs = db.collection('submissions').stream()
        return {doc.id: doc.to_dict() for doc in docs}
    except: return {}

# --- EMAIL LOGIC (Secure SSL) ---
def generate_otp():
    """Generates a 6-digit string OTP"""
    return str(random.randint(100000, 999999))

def send_email(to_email, subject, body_html):
    """Sends HTML email using secure SSL connection"""
    try:
        # 1. Create Message
        msg = MIMEMultipart()
        msg['From'] = f"SapthaHack Security <{SMTP_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body_html, 'html'))
        
        # 2. Create Secure SSL Context
        context = ssl.create_default_context()

        # 3. Connect using SSL (Port 465)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        
        print(f"✅ EMAIL SUCCESS: Sent to {to_email}")
        return True

    except Exception as e:
        print(f"❌ EMAIL FAILED: {str(e)}")
        if "Username and Password not accepted" in str(e):
            print("⚠️ CHECK: 1. Correct Email Spelling? 2. Correct App Password?")
        return False