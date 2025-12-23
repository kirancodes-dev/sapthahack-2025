from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from firebase_config import db
from utils import send_email
import random, datetime

admin_bp = Blueprint('admin_bp', __name__)

# =====================================================
#  1. ADMIN LOGIN & DASHBOARD
# =====================================================
@admin_bp.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    # Persistent Login Check
    if 'admin_user' not in session:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            admin_id = request.form.get('admin_id')
            
            # Master Bypass (For Emergency)
            if email == 'admin' and password == 'admin' and admin_id == 'MASTER':
                session['admin_user'] = 'MasterAdmin'
                session.permanent = True
                return redirect(url_for('admin_bp.admin_panel'))

            # Standard Admin Check from DB
            try:
                doc = db.collection('admins').document(email).get()
                if doc.exists:
                    data = doc.to_dict()
                    if data.get('password') == password and data.get('admin_id') == admin_id:
                        session['admin_user'] = email
                        session.permanent = True
                        return redirect(url_for('admin_bp.admin_panel'))
            except: pass
            
            flash("Invalid Credentials", "error")
        return render_template('admin_login.html')

    # Load Dashboard Data for Authenticated Admin
    try:
        # Get Event Settings
        event_doc = db.collection('settings').document('current_event').get()
        event = event_doc.to_dict() if event_doc.exists else {}

        # Get Teams, Scores & Rankings
        teams = []
        for t in db.collection('teams').stream():
            d = t.to_dict()
            # Fetch Score for this specific team
            score_doc = db.collection('scores').document(f"{d['lead_email']}_score").get()
            if score_doc.exists:
                s_data = score_doc.to_dict()
                d['score'] = s_data.get('total', 0)
                d['rank'] = s_data.get('rank', '-')
                d['status'] = 'Evaluated'
            else:
                d['score'] = 0
                d['rank'] = '-'
                d['status'] = 'Pending'
            teams.append(d)
            
        # Sort Teams by Score for the Live Monitoring Board
        teams.sort(key=lambda x: x['score'], reverse=True)

        return render_template('admin.html', event=event, teams=teams)
    
    except Exception as e:
        return f"Dashboard Error: {e}"

# =====================================================
#  2. INITIALIZE NEW ADMIN (FIXES 404 ERROR)
# =====================================================
@admin_bp.route('/admin/register', methods=['GET', 'POST'])
def register_admin():
    """Matches the 'Initialize New Admin' link in admin_login.html"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        master_key = request.form.get('secret_key')
        
        # Security: Verify Master Key
        if master_key != "SAPTHA_ADMIN_2025":
            flash("⛔ Incorrect Master Key Authorization!", "error")
            return redirect(url_for('admin_bp.register_admin'))
        
        # Generate Unique Secure ID
        new_admin_id = f"ADM-{random.randint(1000, 9999)}"
        
        try:
            # Save to Database
            db.collection('admins').document(email).set({
                "email": email,
                "password": password,
                "admin_id": new_admin_id,
                "role": "SuperAdmin",
                "created_at": str(datetime.datetime.now())
            })
            
            # Send Secure ID to Admin Email
            subject = "Admin Access Granted - SapthaHack '25"
            body = f"<h2>Admin Access Credentials</h2><p>Your Secure Access ID is: <b>{new_admin_id}</b></p>"
            
            # ⚡ CRITICAL: Use the real email from the form
            send_email(email, subject, body)

            # Debugging for terminal if email fails
            print(f"👉 NEW ADMIN CREATED: {email} | SECURE ID: {new_admin_id}")

            flash(f"✅ Admin Created! Secure ID sent to {email}", "success")
            return redirect(url_for('admin_bp.admin_panel'))
            
        except Exception as e:
            flash(f"Database Error: {e}", "error")
            
    return render_template('admin_register.html')

# =====================================================
#  3. CREATE / UPDATE EVENT
# =====================================================
@admin_bp.route('/admin/create_event', methods=['POST'])
def create_event():
    if 'admin_user' not in session: return redirect(url_for('admin_bp.admin_panel'))

    try:
        data = {
            "event_name": request.form.get('event_name'),
            "event_mode": request.form.get('event_mode'), # 'hackathon' or 'general'
            "date": request.form.get('date'),
            "rules": request.form.get('rules'),
            "social_link": request.form.get('social_link'),
            "team_config": {
                "composition": request.form.get('composition'), # 'student', 'staff', 'both'
            },
            "updated_at": str(datetime.datetime.now())
        }
        
        db.collection('settings').document('current_event').set(data)
        flash("✅ Event Configuration Updated Successfully!", "success")
    except Exception as e:
        flash(f"Error updating event: {e}", "error")
        
    return redirect(url_for('admin_bp.admin_panel'))

# =====================================================
#  4. JUDGE MANAGEMENT
# =====================================================
@admin_bp.route('/admin/add_judge', methods=['POST'])
def add_judge():
    if 'admin_user' not in session: return redirect(url_for('admin_bp.admin_panel'))

    try:
        email = request.form.get('email')
        name = request.form.get('name')
        password = f"Judge{random.randint(1000,9999)}"
        
        judge_data = {
            "name": name,
            "email": email,
            "password": password,
            "role_id": request.form.get('role_id'),
            "domain": request.form.get('domain')
        }
        
        db.collection('judges').document(email).set(judge_data)
        
        # Email Credentials
        body = f"<h2>Judge Appointment</h2><p>Login: {email}</p><p>Password: {password}</p>"
        send_email(email, "Judge Credentials", body)
        
        flash(f"✅ Judge {name} Added & Emailed!", "success")
    except Exception as e:
        flash(f"Error adding judge: {e}", "error")

    return redirect(url_for('admin_bp.admin_panel'))

# =====================================================
#  5. ANNOUNCE RESULTS & RANKING
# =====================================================
@admin_bp.route('/admin/announce', methods=['POST'])
def announce():
    if 'admin_user' not in session: return redirect(url_for('admin_bp.admin_panel'))
    
    try:
        # 1. Fetch all scores from database
        scores = []
        for s in db.collection('scores').stream():
            scores.append(s.to_dict())
            
        # 2. Sort by score total descending
        scores.sort(key=lambda x: x.get('total', 0), reverse=True)
        
        # 3. Assign Ranks and Email Participants
        for i, s in enumerate(scores):
            rank = i + 1
            team_email = s.get('team_email')
            
            # Update Rank in Database
            db.collection('scores').document(f"{team_email}_score").update({"rank": rank})
            
            # Send Notification Emails
            if rank == 1:
                subject = "🏆 YOU WON SAPTHAHACK!"
                msg = f"<h1>Congratulations!</h1><p>You secured 1st Place with {s.get('total')} points!</p>"
            else:
                subject = "Event Results Announced"
                msg = f"<p>You secured Rank #{rank} with {s.get('total')} points.</p>"
                
            send_email(team_email, subject, msg)
            
        flash("📢 Results Announced & Emails Sent!", "success")
        
    except Exception as e:
        flash(f"Error announcing results: {e}", "error")
        
    return redirect(url_for('admin_bp.admin_panel'))

@admin_bp.route('/admin/logout')
def logout():
    session.pop('admin_user', None)
    return redirect(url_for('admin_bp.admin_panel'))