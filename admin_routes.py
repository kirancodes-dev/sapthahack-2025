from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response, send_file
from firebase_config import db
from utils import send_email, generate_otp, otp_storage
import csv
import io
import random

admin_bp = Blueprint('admin_bp', __name__)

# --- MAIN ADMIN ROUTE (Login + Dashboard) ---
@admin_bp.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    # 1. HANDLE LOGIN (If not logged in)
    if 'admin_user' not in session:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            admin_id = request.form.get('admin_id') # <--- SECURE ID CHECK
            
            try:
                # Find admin with matching email
                admins = db.collection('admins').where('email', '==', email).stream()
                admin_found = False
                
                for admin in admins:
                    data = admin.to_dict()
                    # VERIFY PASSWORD AND ADMIN ID
                    if data.get('password') == password and data.get('admin_id') == admin_id:
                        session['admin_user'] = email
                        admin_found = True
                        break
                
                if admin_found:
                    return redirect(url_for('admin_bp.admin_panel'))
                else:
                    flash("⛔ Access Denied: Invalid Credentials or Secure ID", "error")
            except Exception as e:
                print(f"Login Error: {e}")
                flash("System Error during login", "error")

        # Show Login Page
        return render_template('admin_login.html') 

    # 2. HANDLE DASHBOARD (If logged in)
    try:
        # A. Fetch All Data
        teams_ref = db.collection('teams').stream()
        judges_ref = db.collection('judges').stream()
        
        # Convert to Dictionaries
        teams = {doc.id: doc.to_dict() for doc in teams_ref}
        judges = {doc.id: doc.to_dict() for doc in judges_ref}
        
        # B. Calculate Stats
        submission_count = sum(1 for t in teams.values() if t.get('ppt_file'))
        
        stats = {
            "total_teams": len(teams),
            "total_judges": len(judges),
            "total_subs": submission_count
        }

        # C. Fetch Current Event Settings
        event_doc = db.collection('settings').document('current_event').get()
        event_data = event_doc.to_dict() if event_doc.exists else {}

        # Render Dashboard
        return render_template('admin.html', 
                             mode='dashboard', 
                             stats=stats, 
                             teams=teams, 
                             judges=judges, 
                             event=event_data)

    except Exception as e:
        print(f"Dashboard Error: {e}")
        return f"Dashboard Error: {e} <br><a href='/admin/logout'>Logout</a>"

# --- ROUTE: CREATE / UPDATE EVENT ---
@admin_bp.route('/admin/create_event', methods=['POST'])
def create_event():
    if 'admin_user' not in session: return redirect(url_for('admin_bp.admin_panel'))

    event_data = {
        "event_name": request.form.get('event_name'),
        "event_type": request.form.get('event_type'),
        "event_date": request.form.get('event_date'),
        "rules": request.form.get('rules'),
        "whatsapp_link": request.form.get('whatsapp_link'),
        "team_config": {
            "max_students": int(request.form.get('max_students')),
            "max_staff": int(request.form.get('max_staff')),
            "allow_mixed": request.form.get('allow_mixed') == 'on'
        }
    }

    # Save to Firebase 'settings' collection
    db.collection('settings').document('current_event').set(event_data)
    
    flash("✅ Event Created! Registration rules and WhatsApp link updated.", "success")
    return redirect(url_for('admin_bp.admin_panel'))

# --- ROUTE: REGISTER NEW ADMIN (With Master Key) ---
@admin_bp.route('/admin/register', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        secret_key = request.form.get('secret_key')
        
        # 1. SECURITY CHECK (Master Key)
        if secret_key != "SAPTHA_ADMIN_2025":
            flash("⛔ SECURITY ALERT: INVALID MASTER KEY", "error")
            return redirect(url_for('admin_bp.register_admin'))
        
        # 2. GENERATE ADMIN ID
        rand_num = random.randint(1000, 9999)
        new_admin_id = f"ADM-{rand_num}"
        
        # 3. SAVE TO DATABASE
        try:
            db.collection('admins').document(email).set({
                "name": name,
                "email": email,
                "password": password,
                "admin_id": new_admin_id,
                "role": "SuperAdmin"
            })
            
            flash(f"✅ Admin Created! Your Secure ID is: {new_admin_id}", "success")
            return redirect(url_for('admin_bp.admin_panel'))
            
        except Exception as e:
            flash(f"Error creating admin: {e}", "error")
            
    return render_template('admin_register.html')

# --- ACTION: APPROVE PAYMENT ---
@admin_bp.route('/admin/approve_payment', methods=['POST'])
def approve_payment():
    if 'admin_user' not in session: return redirect(url_for('admin_bp.admin_panel'))
    
    email = request.form.get('team_email')
    
    # Update Status in Firebase
    db.collection('teams').document(email).update({"payment_status": "Approved"})
    
    # Send Notification Email
    send_email(email, "Payment Approved - SapthaHack '25", 
               "<h3>Congratulations!</h3><p>Your team status has been updated to <b>Approved</b>.</p>")
    
    flash("Team Approved & Email Sent!", "success")
    return redirect(url_for('admin_bp.admin_panel'))

# --- ACTION: ADD JUDGE (Updated with ID & Post) ---
@admin_bp.route('/admin/add_judge', methods=['POST'])
def add_judge():
    if 'admin_user' not in session: return redirect(url_for('admin_bp.admin_panel'))

    name = request.form.get('name')
    email = request.form.get('email')
    role_id = request.form.get('role_id') # SRN or Staff ID
    post = request.form.get('post')       # Asst Prof, Student, etc.
    domain = request.form.get('domain', 'General')
    
    # Auto-generate password
    password = "judge" + str(random.randint(1000,9999))

    judge_data = {
        "name": name,
        "email": email,
        "role_id": role_id,
        "post": post,
        "domain": domain,
        "password": password,
        "role": "Judge"
    }
    
    db.collection('judges').document(email).set(judge_data)
    
    # Send Login Credentials to Judge
    send_email(email, "Judge Selection - SapthaHack '25", 
               f"<p>Dear {name},<br>You are selected as a Judge/Jury.<br><b>Login:</b> {email}<br><b>Password:</b> {password}</p>")

    flash(f"Judge {name} added and emailed!", "success")
    return redirect(url_for('admin_bp.admin_panel'))

# --- ROUTE: DELETE TEAM ---
@admin_bp.route('/admin/delete_team', methods=['POST'])
def delete_team():
    if 'admin_user' not in session: return redirect(url_for('admin_bp.admin_panel'))
    
    email = request.form.get('email')
    db.collection('teams').document(email).delete()
    # Also delete associated score
    db.collection('scores').document(email).delete()
    
    flash("Team deleted successfully.", "success")
    return redirect(url_for('admin_bp.admin_panel'))

# --- ROUTE: DELETE JUDGE ---
@admin_bp.route('/admin/delete_judge', methods=['POST'])
def delete_judge():
    if 'admin_user' not in session: return redirect(url_for('admin_bp.admin_panel'))
    
    email = request.form.get('email')
    db.collection('judges').document(email).delete()
    flash("Judge deleted.", "success")
    return redirect(url_for('admin_bp.admin_panel'))

# --- ROUTE: EXPORT DATA (CSV Method) ---
@admin_bp.route('/admin/export_csv')
def export_csv():
    if 'admin_user' not in session: return redirect(url_for('admin_bp.admin_panel'))

    # Fetch fresh data
    teams_ref = db.collection('teams').stream()
    teams = {doc.id: doc.to_dict() for doc in teams_ref}

    # 1. Create CSV in Memory
    si = io.StringIO()
    cw = csv.writer(si)
    
    # 2. Write Headers
    cw.writerow(['Team Name', 'Lead Name', 'Email', 'Phone', 'Problem Statement', 'Status'])

    # 3. Write Data Rows
    for t in teams.values():
        cw.writerow([
            t.get('team_name', ''),
            t.get('lead_name', ''),
            t.get('lead_email', ''),
            t.get('lead_phone', ''),
            t.get('problem_statement', ''),
            t.get('payment_status', 'Pending')
        ])

    # 4. Prepare Response as File Download
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=SapthaHack_Teams.csv"
    output.headers["Content-type"] = "text/csv"
    return output
# --- ROUTE: NUCLEAR RESET (DELETE EVERYTHING) ---
@admin_bp.route('/admin/nuclear_reset', methods=['POST'])
def nuclear_reset():
    if 'admin_user' not in session: return redirect(url_for('admin_bp.admin_panel'))
    
    confirm_code = request.form.get('confirm_code')
    
    # 1. HARD SECURITY CHECK
    # You must type this exact code to trigger the wipe
    if confirm_code != "DELETE_EVERYTHING_2025":
        flash("⛔ WRONG CONFIRMATION CODE! Data was NOT deleted.", "error")
        return redirect(url_for('admin_bp.admin_panel'))
    
    try:
        # 2. DELETE ALL TEAMS
        teams = db.collection('teams').stream()
        for doc in teams:
            db.collection('teams').document(doc.id).delete()
            
        # 3. DELETE ALL JUDGES
        judges = db.collection('judges').stream()
        for doc in judges:
            db.collection('judges').document(doc.id).delete()
            
        # 4. DELETE ALL SCORES
        scores = db.collection('scores').stream()
        for doc in scores:
            db.collection('scores').document(doc.id).delete()

        flash("☢️ NUCLEAR RESET SUCCESSFUL. All event data has been wiped.", "success")
        
    except Exception as e:
        flash(f"Error during wipe: {e}", "error")
        
    return redirect(url_for('admin_bp.admin_panel'))
# --- ROUTE: LOGOUT ---
@admin_bp.route('/admin/logout')
def logout():
    session.pop('admin_user', None)
    return redirect(url_for('admin_bp.admin_panel'))