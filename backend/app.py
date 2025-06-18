import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView

# App Initialization
load_dotenv()
app = Flask(__name__)
CORS(app)

# Database Configuration
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Use the production database URL from Neon
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("postgres://", "postgresql://", 1)
else:
    # Use a local SQLite database for development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

# Database Models (No changes here)
class PostResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_url = db.Column(db.String(500), unique=True, nullable=False)
    resource_name = db.Column(db.String(200), nullable=False)
    resource_link = db.Column(db.String(500), nullable=False)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(100))
    company_college = db.Column(db.String(100))
    requested_resource_name = db.Column(db.String(200))

# Secure Admin Views with Basic Auth (No changes here)
class AuthView(ModelView):
    def is_accessible(self):
        auth = request.authorization
        return (auth and auth.username == os.getenv('ADMIN_USER') and auth.password == os.getenv('ADMIN_PASS'))
    def inaccessible_callback(self, name, **kwargs):
        return Response('Authentication Required', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        auth = request.authorization
        return (auth and auth.username == os.getenv('ADMIN_USER') and auth.password == os.getenv('ADMIN_PASS'))
    def inaccessible_callback(self, name, **kwargs):
        return Response('Authentication Required', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

# Admin Panel Setup (No changes here)
admin = Admin(app, name='Resource Admin', template_mode='bootstrap3', index_view=SecureAdminIndexView())
admin.add_view(AuthView(PostResource, db.session, name='Manage Posts'))
admin.add_view(AuthView(Submission, db.session, name='View Submissions'))

# Main API Route (No changes here)
@app.route('/api/request-resource', methods=['POST'])
def request_resource():
    # ... (rest of the function is the same)
    data = request.get_json()
    linkedin_post_url = data.get('linkedin_post_url')
    resource = PostResource.query.filter_by(post_url=linkedin_post_url).first()
    if not resource: return jsonify({"status": "error", "message": "Sorry, this LinkedIn post is not associated with a resource."}), 404
    new_submission = Submission(name=data.get('name'), email=data.get('email'), position=data.get('position'), company_college=data.get('company_college'), requested_resource_name=resource.resource_name)
    db.session.add(new_submission)
    db.session.commit()
    try:
        sender_email = os.getenv('EMAIL_ADDRESS')
        sender_password = os.getenv('EMAIL_PASSWORD')
        msg = MIMEMultipart()
        msg['From'] = f"Gitesh Malik <{sender_email}>"
        msg['To'] = data.get('email')
        msg['Subject'] = f"Here is your requested resource: {resource.resource_name}"
        body = f"Hi {data.get('name')},\n\nHere is the resource you requested:\nResource: {resource.resource_name}\nDownload Link: {resource.resource_link}\n\nBest,\nGitesh Malik"
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return jsonify({"status": "success", "message": "Success! The resource has been sent."}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": "An error occurred while sending the email."}), 500

# ===================================================================
# == NEW: Automatic Database Initialization                        ==
# ===================================================================
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
