from flask import Blueprint, request, jsonify
from firebase_config import db
# Import ALL data helpers to make the bot "aware" of the whole system
from utils import get_all_events, get_all_teams, get_all_judges, get_all_scores

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/bot/chat', methods=['POST'])
def chat_response():
    user_msg = request.json.get('message', '').lower().strip()
    
    # --- 1. FETCH LIVE SYSTEM DATA ---
    # We fetch fresh data every time so the bot is always up-to-date
    teams = get_all_teams()
    judges = get_all_judges()
    scores = get_all_scores()
    
    # Get Event Settings (Rules, Dates, Links)
    event_doc = db.collection('settings').document('current_event').get()
    event_data = event_doc.to_dict() if event_doc.exists else {}
    
    event_name = event_data.get('event_name', 'SapthaHack')
    wa_link = event_data.get('whatsapp_link', '#')
    team_config = event_data.get('team_config', {'max_students': 4})

    # --- 2. INTELLIGENT RESPONSE LOGIC ---
    
    # GREETING
    if any(x in user_msg for x in ["hello", "hi", "hey"]):
        reply = f"Hello! I am the <b>{event_name}</b> AI. I can check stats, rules, and status for you!"

    # DYNAMIC STATS (Real Database Counts)
    elif "how many team" in user_msg or "total team" in user_msg:
        count = len(teams)
        reply = f"Currently, there are <b>{count} teams</b> registered for {event_name}."

    elif "how many judge" in user_msg or "jury" in user_msg:
        count = len(judges)
        reply = f"We have <b>{count} expert judges</b> evaluating the projects."

    # RULES (From Admin Settings)
    elif "team size" in user_msg or "how many member" in user_msg:
        max_s = team_config.get('max_students', 4)
        reply = f"According to the rules, a team can have up to <b>{max_s} students</b>."

    elif "whatsapp" in user_msg or "group" in user_msg:
        if wa_link and wa_link != '#':
            reply = f"Join our official group here: <a href='{wa_link}' target='_blank' style='color:#003366; font-weight:bold;'>Click to Join</a>"
        else:
            reply = "The WhatsApp link hasn't been released by the Admin yet."

    # STATUS CHECKER (Powerful Feature!)
    # Usage: "status for myemail@gmail.com"
    elif "status for" in user_msg:
        # Extract email from message
        words = user_msg.split()
        email_query = words[-1] # simplistic extraction (assumes email is last word)
        
        if "@" in email_query:
            # Check DB
            found_team = teams.get(email_query)
            if found_team:
                status = found_team.get('payment_status', 'Pending')
                reply = f"Team <b>{found_team.get('team_name')}</b> found!<br>Current Status: <b>{status}</b>"
            else:
                reply = "❌ No team found with that Lead Email. Please register first."
        else:
            reply = "Please type 'status for <b>your_email@gmail.com</b>' to check."

    # LEADERBOARD / WINNERS
    elif "winning" in user_msg or "highest score" in user_msg or "leader" in user_msg:
        if not scores:
            reply = "No evaluations have been submitted yet."
        else:
            # Sort scores to find top
            top_email = max(scores, key=scores.get)
            top_score = scores[top_email]
            top_team_name = teams.get(top_email, {}).get('team_name', 'Unknown')
            reply = f"🏆 Current Leader: <b>{top_team_name}</b> with {top_score} points!"

    # NAVIGATION HELP
    elif "register" in user_msg:
        reply = "Click the <b>'Participant'</b> button on the home page to register your team."
    elif "login" in user_msg:
        reply = "Go to the <b>'Participant'</b> portal to login with your registered email."

    # DEFAULT FALLBACK
    else:
        reply = "I didn't quite catch that. You can ask me about:<br>• Total Teams<br>• Team Size Rules<br>• Who is winning?<br>• Status for [your_email]"

    return jsonify({"reply": reply})