from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from firebase_config import db

judge_bp = Blueprint('judge_bp', __name__)

# --- JUDGE LOGIN ---
@judge_bp.route('/judge', methods=['GET', 'POST'])
def login():
    # If already logged in, go to dashboard
    if 'judge_user' in session:
        return redirect(url_for('judge_bp.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Verify Creds
        doc = db.collection('judges').document(email).get()
        if doc.exists:
            data = doc.to_dict()
            if data.get('password') == password:
                session['judge_user'] = email
                session['judge_name'] = data.get('name')
                session['judge_domain'] = data.get('domain', 'General')
                return redirect(url_for('judge_bp.dashboard'))
            else:
                flash("Incorrect Password", "error")
        else:
            flash("Judge email not found. Contact Admin.", "error")
            
    return render_template('judge.html', mode='login')

# --- JUDGE DASHBOARD ---
@judge_bp.route('/judge/dashboard')
def dashboard():
    if 'judge_user' not in session: return redirect(url_for('judge_bp.login'))
    
    # 1. Get Judge Info
    judge_domain = session.get('judge_domain', 'General')
    
    # 2. Get Teams (Filter by Domain if needed, or show all)
    # Ideally, judges only see teams in their domain.
    teams_ref = db.collection('teams').stream()
    all_teams = []
    
    for t in teams_ref:
        team = t.to_dict()
        team_email = t.id
        
        # Check if already graded by THIS judge
        score_doc = db.collection('scores').document(f"{team_email}_{session['judge_user']}").get()
        team['my_score'] = score_doc.to_dict().get('total', 'Not Graded') if score_doc.exists else None
        team['id'] = team_email # Store email as ID for linking
        
        all_teams.append(team)

    return render_template('judge.html', mode='dashboard', teams=all_teams, judge_name=session['judge_name'])

# --- SUBMIT SCORE ---
@judge_bp.route('/judge/score', methods=['POST'])
def submit_score():
    if 'judge_user' not in session: return redirect(url_for('judge_bp.login'))
    
    try:
        team_email = request.form.get('team_email')
        
        # Scoring Criteria (Max 10 each)
        c1 = int(request.form.get('innovation', 0))
        c2 = int(request.form.get('tech_stack', 0))
        c3 = int(request.form.get('presentation', 0))
        c4 = int(request.form.get('feasibility', 0))
        c5 = int(request.form.get('ui_ux', 0))
        
        total = c1 + c2 + c3 + c4 + c5 # Max 50
        
        score_data = {
            "judge": session['judge_user'],
            "team_email": team_email,
            "breakdown": {
                "innovation": c1,
                "tech_stack": c2,
                "presentation": c3,
                "feasibility": c4,
                "ui_ux": c5
            },
            "total": total
        }
        
        # Save unique score per judge/team combination
        # Format: teamEmail_judgeEmail
        db.collection('scores').document(f"{team_email}_{session['judge_user']}").set(score_data)
        
        # Update Global Team Score (Average or Sum)
        # For simplicity, let's just save the score record.
        # Admin can calculate winners later.
        
        flash(f"Score Submitted! Total: {total}/50", "success")
        
    except Exception as e:
        print(e)
        flash("Error submitting score.", "error")
        
    return redirect(url_for('judge_bp.dashboard'))

# --- LOGOUT ---
@judge_bp.route('/judge/logout')
def logout():
    session.pop('judge_user', None)
    return redirect(url_for('judge_bp.login'))