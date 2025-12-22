from flask import Flask, render_template, request, redirect, url_for, flash, session
# --- 1. IMPORT DB FROM CONFIG ---
from firebase_config import db 

# --- 2. IMPORT BLUEPRINTS ---
from admin_routes import admin_bp
from student_routes import student_bp
from chatbot_routes import chat_bp
from judge_routes import judge_bp   # <--- Judge Logic

# --- 3. IMPORT UTILITIES ---
from utils import get_all_teams, get_all_scores, get_all_submissions, get_all_events

app = Flask(__name__, template_folder='sapthagiri_app/templates', static_folder='sapthagiri_app/static')
app.secret_key = 'super_secret_key_for_session'

# --- 4. REGISTER BLUEPRINTS ---
app.register_blueprint(admin_bp)
app.register_blueprint(student_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(judge_bp)

# --- HOME ROUTES ---
@app.route('/')
def home():
    return render_template('home.html', show_portal=False)

@app.route('/portal-select')
def portal_select():
    return render_template('home.html', show_portal=True)

# --- PUBLIC DISPLAY ROUTES (Big Screen) ---

# 1. LIVE LEADERBOARD
@app.route('/leaderboard')
def leaderboard():
    try:
        teams = get_all_teams() or {}   
        scores = get_all_scores() or {} 
        
        ranked_teams = []
        for email, score in scores.items():
            # Match score ID to team email
            # Note: Score ID might be "teamEmail_judgeEmail" or just "teamEmail" depending on logic.
            # Assuming score logic aggregates totals into a simple dict {team_email: total_score}
            # If scores key is "team_email", we match directly:
            if email in teams:
                t = teams[email]
                ranked_teams.append({
                    "name": t.get('team_name', 'Unknown'),
                    "score": int(score),
                    "ps": t.get('problem_statement', 'N/A'),
                    "lead": t.get('lead_name', '')
                })
        
        # Sort Highest Score First
        ranked_teams.sort(key=lambda x: x['score'], reverse=True)
        return render_template('leaderboard.html', teams=ranked_teams)

    except Exception as e:
        print(f"Leaderboard Error: {e}")
        return "Leaderboard loading..."

# 2. ANALYTICS DASHBOARD
@app.route('/analytics')
def analytics():
    teams = get_all_teams() or {}
    submissions = get_all_submissions() or {}
    scores = get_all_scores() or {}
    
    # Basic Stats
    total_teams = len(teams)
    total_subs = len(submissions)
    avg_score = round(sum(scores.values()) / len(scores), 1) if scores else 0
    
    # Graphs: Problem Statements
    ps_counts = {}
    for t in teams.values():
        ps = t.get('problem_statement', 'Unknown')
        ps_counts[ps] = ps_counts.get(ps, 0) + 1
        
    # Graphs: Top 5
    ranked_list = []
    for email, score in scores.items():
        if email in teams:
            ranked_list.append({'name': teams[email]['team_name'], 'score': score})
    
    ranked_list.sort(key=lambda x: x['score'], reverse=True)
    top_5 = ranked_list[:5]
    
    return render_template('analytics.html', 
                           total_teams=total_teams, 
                           total_subs=total_subs, 
                           avg_score=avg_score,
                           ps_labels=list(ps_counts.keys()),
                           ps_values=list(ps_counts.values()),
                           top_names=[x['name'] for x in top_5],
                           top_scores=[x['score'] for x in top_5])

# 3. WINNERS REVEAL
@app.route('/winners')
def winners():
    teams = get_all_teams() or {}
    scores = get_all_scores() or {}
    
    ranked = []
    for email, score in scores.items():
        if email in teams:
            ranked.append({
                "name": teams[email]['team_name'],
                "score": score,
                "lead": teams[email]['lead_name']
            })
    
    ranked.sort(key=lambda x: x['score'], reverse=True)
    return render_template('winners.html', winners=ranked[:3])

# --- ERROR HANDLER ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)