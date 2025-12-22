from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from firebase_config import db
from cert_gen import create_certificate
# Import utilities
from utils import send_email, generate_otp, otp_storage, get_all_events
import qrcode
import io
import base64
import random

student_bp = Blueprint('student_bp', __name__)

# --- HELPER: QR GENERATOR ---
def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return base64.b64encode(img_io.getvalue()).decode('utf-8')

# --- ROUTE: STUDENT PORTAL (AUTH) ---
@student_bp.route('/participant', methods=['GET', 'POST'])
def auth():
    # Fetch current event settings for the form
    event_doc = db.collection('settings').document('current_event').get()
    event_settings = event_doc.to_dict() if event_doc.exists else {}
    
    # Default settings if none exist
    if not event_settings.get('team_config'):
        event_settings['team_config'] = {"max_students": 4, "max_staff": 1}
        
    return render_template('participant.html', event=event_settings)

# --- ROUTE: SEND OTP ---
@student_bp.route('/participant/send-otp', methods=['POST'])
def send_otp_route():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"message": "Email is required"}), 400

    # 1. Generate & Store OTP
    otp = generate_otp()
    otp_storage[email] = otp
    
    # 2. Send Email
    subject = "Your Verification Code - SapthaHack '25"
    body = f"""
    <h3>Email Verification</h3>
    <p>Your OTP code is: <b style="font-size: 24px; color: #003366;">{otp}</b></p>
    <p>Use this to verify your team registration.</p>
    """
    
    success = send_email(email, subject, body)
    
    if success:
        return jsonify({"message": "OTP Sent Successfully!", "debug_otp": otp})
    else:
        return jsonify({"message": "Failed to send email. Check Server Logs."}), 500

# --- ROUTE: HANDLE REGISTRATION (WITH UNIQUE ID & WHATSAPP LINK) ---
@student_bp.route('/participant/register', methods=['POST'])
def register():
    try:
        # 1. Verify OTP
        email = request.form.get('lead_email')
        user_otp = request.form.get('otp')
        
        if otp_storage.get(email) != user_otp:
            flash("Invalid or Expired OTP!", "error")
            return redirect(url_for('student_bp.auth'))

        # 2. Fetch Event Settings (To get the WhatsApp Link)
        event_doc = db.collection('settings').document('current_event').get()
        event_data = event_doc.to_dict() if event_doc.exists else {}
        wa_link = event_data.get('whatsapp_link', '#')

        # 3. GENERATE UNIQUE TEAM ID
        rand_id = random.randint(1000, 9999)
        team_id = f"SH-{rand_id}"

        # 4. Gather Data
        team_data = {
            "team_id": team_id,
            "team_name": request.form.get('team_name'),
            "problem_statement": request.form.get('problem_statement'),
            "lead_name": request.form.get('lead_name'),
            "lead_email": email,
            "lead_phone": request.form.get('lead_phone'),
            "lead_srn": request.form.get('lead_srn'),
            "password": request.form.get('password'),
            "students": [],
            "staff": [],
            "payment_status": "Pending",
            "ppt_file": ""
        }
        
        # Add Students
        for i in range(2, 6):
            name = request.form.get(f'student_name_{i}')
            if name:
                team_data['students'].append({
                    "name": name,
                    "email": request.form.get(f'student_email_{i}'),
                    "role": "Member"
                })

        # Add Staff/Mentors
        for i in range(1, 3):
            name = request.form.get(f'staff_name_{i}')
            if name:
                team_data['staff'].append({
                    "name": name,
                    "email": request.form.get(f'staff_email_{i}')
                })

        # 5. Save to Firebase
        db.collection('teams').document(email).set(team_data)
        
        # 6. Clear OTP
        if email in otp_storage: del otp_storage[email]
        
        # 7. Send Confirmation Email WITH TEAM ID & WHATSAPP LINK
        subject = f"Registration Confirmed - Team {team_data['team_name']}"
        body = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd;">
            <h2 style="color: #003366;">Welcome to {event_data.get('event_name', 'SapthaHack')}!</h2>
            <p>Dear {team_data['lead_name']},</p>
            <p>Your team <b>{team_data['team_name']}</b> has been successfully registered.</p>
            
            <div style="background: #f4f6f9; padding: 15px; margin: 20px 0; border-left: 5px solid #FFCC00;">
                <h3 style="margin: 0; color: #333;">Your Unique Team ID:</h3>
                <h1 style="margin: 10px 0; color: #003366; letter-spacing: 2px;">{team_id}</h1>
                <p style="margin: 0; font-size: 0.9em; color: #666;">Keep this ID safe for reference.</p>
            </div>
            
            <div style="background: #d4edda; padding: 15px; border-radius: 5px; border: 1px solid #c3e6cb; margin-top: 20px;">
                <h3 style="color: #155724; margin:0 0 10px 0;">📢 JOIN THE OFFICIAL GROUP</h3>
                <p style="margin: 0 0 15px 0;">Click below to join the WhatsApp group for updates:</p>
                <a href="{wa_link}" style="background:#25D366; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; font-weight:bold; display: inline-block;">Join WhatsApp Group</a>
            </div>
            
            <br>
            <p>Please login to your dashboard to track your status.</p>
            <br>
            <p>Best Regards,<br><b>SapthaHack Organizing Team</b></p>
        </div>
        """
        
        send_email(email, subject, body)
        
        flash(f"Registration Successful! Check your email for Team ID & Group Link.", "success")
        return redirect(url_for('student_bp.auth'))

    except Exception as e:
        print(f"Reg Error: {e}")
        flash(f"Registration Failed: {e}", "error")
        return redirect(url_for('student_bp.auth'))

# --- ROUTE: LOGIN ---
@student_bp.route('/participant/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    try:
        doc = db.collection('teams').document(email).get()
        if doc.exists:
            data = doc.to_dict()
            if data.get('password') == password:
                session['student_email'] = email
                return redirect(url_for('student_bp.dashboard'))
            else:
                flash("Incorrect Password", "error")
        else:
            flash("Email not registered", "error")
    except Exception as e:
        flash(f"Login Error: {e}", "error")
        
    return redirect(url_for('student_bp.auth'))

# --- ROUTE: DASHBOARD ---
@student_bp.route('/participant/dashboard')
def dashboard():
    if 'student_email' not in session: return redirect(url_for('student_bp.auth'))
    
    email = session['student_email']
    doc = db.collection('teams').document(email).get()
    
    if not doc.exists:
        session.pop('student_email', None)
        return redirect(url_for('student_bp.auth'))
        
    team = doc.to_dict()
    # Updated QR Code to use the new Team ID if available, otherwise fallback to Email
    qr_data = team.get('team_id', f"SAPTHA-TEAM-{email}")
    qr_b64 = f"data:image/png;base64,{generate_qr(qr_data)}"

    return render_template('participant.html', view='dashboard', team=team, qr_code=qr_b64)

# --- ROUTE: LOGOUT ---
@student_bp.route('/participant/logout')
def logout():
    session.pop('student_email', None)
    return redirect(url_for('student_bp.auth'))