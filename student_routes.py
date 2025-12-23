from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from firebase_config import db
from utils import send_email, generate_otp, otp_storage
from werkzeug.utils import secure_filename
import random, datetime, os

student_bp = Blueprint('student_bp', __name__)

# --- AUTH PAGE ---
@student_bp.route('/participant', methods=['GET', 'POST'])
def auth():
    try:
        event_doc = db.collection('settings').document('current_event').get()
        settings = event_doc.to_dict() if event_doc.exists else {}
    except:
        settings = {}
    return render_template('participant.html', event=settings)

# --- OTP ---
@student_bp.route('/participant/send-otp', methods=['POST'])
def send_otp_route():
    data = request.get_json()
    email = data.get('email')
    
    if not email: return jsonify({"message": "Email Required"}), 400

    otp = generate_otp()
    otp_storage[email] = otp
    
    body = f"""
    <div style="font-family: Arial; padding: 20px; border: 1px solid #ddd;">
        <h2 style="color: #003366;">Verification Code</h2>
        <h1 style="color: #d9534f; letter-spacing: 5px;">{otp}</h1>
        <p>Use this code to complete your registration.</p>
    </div>
    """
    send_email(email, "Verify Email", body)
    return jsonify({"message": "OTP Sent!"})

# --- REGISTER (WITH OPTIONAL FILES & DYNAMIC ROLES) ---
@student_bp.route('/participant/register', methods=['POST'])
def register():
    try:
        email = request.form.get('lead_email')
        otp = request.form.get('otp')
        
        # 1. Verify OTP
        if otp_storage.get(email) != otp:
            flash("Invalid OTP", "error")
            return redirect(url_for('student_bp.auth'))

        # 2. Handle File Uploads (MODIFIED TO BE OPTIONAL)
        ppt_file = request.files.get('ppt_file')
        report_file = request.files.get('report_file')
        ppt_path = "Not Uploaded"
        report_path = "Not Uploaded"

        # Check if UPLOAD_FOLDER is configured to avoid KeyError
        if 'UPLOAD_FOLDER' not in current_app.config:
            flash("Server Configuration Error: Upload folder not found.", "error")
            return redirect(url_for('student_bp.auth'))

        if ppt_file and ppt_file.filename != '':
            fname = secure_filename(f"{email}_PPT_{ppt_file.filename}")
            ppt_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fname))
            ppt_path = fname
            
        if report_file and report_file.filename != '':
            fname = secure_filename(f"{email}_REPORT_{report_file.filename}")
            report_file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fname))
            report_path = fname

        # 3. Get Event Mode
        event_doc = db.collection('settings').document('current_event').get()
        event = event_doc.to_dict() if event_doc.exists else {}
        
        # 4. Create Team Data
        team_id = f"TM-{random.randint(1000,9999)}"
        ps = request.form.get('problem_statement', 'N/A')
        if event.get('event_mode') == 'general': ps = "General Entry"

        team_data = {
            "team_id": team_id,
            "team_name": request.form.get('team_name'),
            "problem_statement": ps,
            "lead_name": request.form.get('lead_name'),
            "lead_email": email,
            "password": request.form.get('password'),
            "registered_at": str(datetime.datetime.now()),
            "ppt_file": ppt_path,
            "report_file": report_path,
            "members": []
        }
        
        # 5. Add Members
        for i in range(1, 6):
            m_name = request.form.get(f'member_name_{i}')
            m_id = request.form.get(f'member_id_{i}')
            m_role = request.form.get(f'member_role_{i}')
            
            if m_name:
                team_data['members'].append({
                    "name": m_name, 
                    "id": m_id if m_id else "N/A", 
                    "role": m_role if m_role else "Student"
                })

        db.collection('teams').document(email).set(team_data)
        if email in otp_storage: del otp_storage[email]
        
        flash(f"Success! Team ID: {team_id}", "success")
        return redirect(url_for('student_bp.auth'))

    except Exception as e:
        flash(f"Error during registration: {str(e)}", "error")
        return redirect(url_for('student_bp.auth'))

# --- LOGIN & DASHBOARD ---
@student_bp.route('/participant/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        doc = db.collection('teams').document(email).get()
        if doc.exists and doc.to_dict().get('password') == password:
            session['user_email'] = email
            return redirect(url_for('student_bp.dashboard'))
        flash("Invalid Credentials", "error")
    except Exception as e: 
        flash(f"Login Error: {str(e)}", "error")
    return redirect(url_for('student_bp.auth'))

@student_bp.route('/participant/dashboard')
def dashboard():
    if 'user_email' not in session: return redirect(url_for('student_bp.auth'))
    
    doc = db.collection('teams').document(session['user_email']).get()
    if not doc.exists: return redirect(url_for('student_bp.auth'))
    team = doc.to_dict()
    
    # Fetch Score & Rank for Dashboard
    score_doc = db.collection('scores').document(f"{team['lead_email']}_score").get()
    if score_doc.exists:
        s_data = score_doc.to_dict()
        team['score'] = s_data.get('total', 0)
        team['rank'] = s_data.get('rank', 'Calculating...')
        team['status'] = "Evaluated"
    else:
        team['score'] = "Pending"
        team['rank'] = "-"
        team['status'] = "Pending"
        
    return render_template('participant.html', view='dashboard', team=team)

@student_bp.route('/participant/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('student_bp.auth'))