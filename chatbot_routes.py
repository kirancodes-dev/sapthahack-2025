from flask import Blueprint, request, jsonify
from firebase_config import db

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/bot/chat', methods=['POST'])
def chat_response():
    user_msg = request.json.get('message', '').lower().strip()
    
    # 1. Fetch Basic Stats for Context
    try:
        teams_count = len(list(db.collection('teams').stream()))
        event_doc = db.collection('settings').document('current_event').get()
        event = event_doc.to_dict() if event_doc.exists else {}
        event_name = event.get('event_name', 'SapthaHack')
    except:
        teams_count = 0
        event_name = "SapthaHack"

    # 2. Logic
    if "hello" in user_msg or "hi" in user_msg:
        reply = f"Hello! Welcome to {event_name}. How can I help you today?"
    elif "register" in user_msg:
        reply = "To register, click on the 'Participant' portal button on the home page."
    elif "team" in user_msg or "count" in user_msg:
        reply = f"Currently, there are {teams_count} teams registered for the event."
    elif "judge" in user_msg:
        reply = "Judges need credentials sent by the Admin to log in."
    elif "date" in user_msg or "when" in user_msg:
        reply = f"The event is scheduled for {event.get('date', 'TBD')}."
    elif "contact" in user_msg:
        reply = "You can contact support at admissions@snpsu.edu.in"
    else:
        reply = "I am an AI Assistant. Please ask about Registration, Teams, or Event Dates."

    return jsonify({"reply": reply})