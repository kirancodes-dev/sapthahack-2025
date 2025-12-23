from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from firebase_config import db

judge_bp = Blueprint('judge_bp', __name__)

@judge_bp.route('/judge', methods=['GET', 'POST'])
def login():
    if 'judge_user' in session:
        return redirect(url_for('judge_bp.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            doc = db.collection('judges').document(email).get()
            if doc.exists:
                data = doc.to_dict()
                if data.get('password') == password:
                    session['judge_user'] = email
                    session['judge_name'] = data.get('name')
                    return redirect(url_for('judge_bp.dashboard'))
            
            flash("Invalid Credentials. Please check the email sent by Admin.", "error")
        except Exception as e:
            flash(f"System Error: {e}", "error")
            
    return render_template('judge.html', mode='login')

@judge_bp.route('/judge/dashboard')
def dashboard():
    if 'judge_user' not in session: return redirect(url_for('judge_bp.login'))
    
    try:
        # Fetch all teams
        teams_ref = db.collection('teams').stream()
        teams = []
        for t in teams_ref:
            team = t.to_dict()
            team['id'] = t.id
            
            # Check if THIS judge has already scored this team
            score_id = f"{t.id}_{session['judge_user']}"
            score_doc = db.collection('scores').document(score_id).get()
            
            if score_doc.exists:
                team['my_score'] = score_doc.to_dict().get('total')
                team['status'] = 'Graded'
            else:
                team['my_score'] = 0
                team['status'] = 'Pending'
                
            teams.append(team)

        return render_template('judge.html', mode='dashboard', teams=teams, judge_name=session.get('judge_name'))
    except Exception as e:
        return f"Error loading dashboard: {e}"

@judge_bp.route('/judge/evaluate', methods=['POST'])
def evaluate():
    if 'judge_user' not in session: return redirect(url_for('judge_bp.login'))
    
    try:
        team_email = request.form.get('team_email')
        c1 = int(request.form.get('c1', 0))
        c2 = int(request.form.get('c2', 0))
        c3 = int(request.form.get('c3', 0))
        total = c1 + c2 + c3
        
        # Save Score
        score_id = f"{team_email}_{session['judge_user']}"
        db.collection('scores').document(score_id).set({
            "team_email": team_email,
            "judge": session['judge_user'],
            "c1": c1, "c2": c2, "c3": c3,
            "total": total
        })
        
        # Also update global score (Simplified: Last judge overwrites total for live monitor)
        # In a real app, you would average them.
        db.collection('scores').document(f"{team_email}_score").set({
            "total": total,
            "team_email": team_email
        })

        flash("Score Submitted Successfully!", "success")
    except Exception as e:
        flash(f"Error submitting score: {e}", "error")
        
    return redirect(url_for('judge_bp.dashboard'))

@judge_bp.route('/judge/logout')
def logout():
    session.pop('judge_user', None)
    return redirect(url_for('judge_bp.login'))