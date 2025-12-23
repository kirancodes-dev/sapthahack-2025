import os
import secrets
from datetime import timedelta
from flask import Flask, render_template

# Windows Network Fix
os.environ["GRPC_DNS_RESOLVER"] = "native"
os.environ["GRPC_POLL_STRATEGY"] = "poll"

from firebase_config import db
from admin_routes import admin_bp
from student_routes import student_bp
from judge_routes import judge_bp

app = Flask(__name__, 
            template_folder='sapthagiri_app/templates', 
            static_folder='sapthagiri_app/static')

app.secret_key = secrets.token_hex(32)
app.permanent_session_lifetime = timedelta(days=30)

# --- 📁 FIX: PROPER UPLOAD CONFIGURATION ---
# This line prevents the 'KeyError' seen in your image
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'sapthagiri_app/static/uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Email Settings
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sapthhack@gmail.com'
app.config['MAIL_PASSWORD'] = 'bbcw iimk ghvu pvof'

app.register_blueprint(admin_bp)
app.register_blueprint(student_bp)
app.register_blueprint(judge_bp)

@app.route('/')
def home(): return render_template('home.html', show_portal=False)

@app.route('/portal-select')
def portal_select(): return render_template('home.html', show_portal=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)