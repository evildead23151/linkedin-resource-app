import os
import smtplib
import re # NEW: Import the regular expression module
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from wtforms.validators import ValidationError # NEW: For custom validation

# App Initialization
load_dotenv()
app = Flask(__name__)
CORS(app)

# Database Configuration
database_url = os.getenv('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("postgres://", "postgresql://", 1)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

# --- NEW: Robust LinkedIn Activity ID Extractor ---
def extract_linkedin_activity_id(url_string):
    """
    Extracts the unique activity ID from various LinkedIn URL formats.
    """
    if not isinstance(url_string, str):
        return None
    
    # Pattern 1: Matches feed/update/urn:li:activity:12345
    match = re.search(r'urn:li:activity:(\d+)', url_string)
    if match:
        return match.group(1)
        
    # Pattern 2: Matches posts/...-activity-12345
    match = re.search(r'activity-(\d+)', url_string)
    if match:
        return match.group(1)
        
    return None # Return None if no ID is found

# --- UPDATED: Database Models to use activity_id ---
class PostResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # NEW: Store the unique activity ID
    activity_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    # We'll still store the original URL for reference, but it's not used for lookups
    post_url = db.Column(db.String(500), nullable=False)
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

# Secure Admin Views
class AuthView(ModelView):
    def is_accessible(self):
        auth = request.authorization
        return (auth and auth.username == os.getenv('ADMIN_USER') and auth.password == os.getenv('ADMIN_PASS'))
    def inaccessible_callback(self, name, **kwargs):
        return Response('Authentication Required', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

# --- UPDATED: PostResourceView to extract and save the activity_id ---
class PostResourceView(AuthView):
    column_list = ('resource_name', 'post_url', 'activity_id') # Show the activity_id in the list
    form_columns = ('resource_name', 'post_url', 'resource_link') # Only ask for these in the form
    
    def on_model_change(self, form, model, is_created):
        # When a post is created or updated, extract the ID from the URL
        if model.post_url:
            activity_id = extract_linkedin_activity_id(model.post_url)
            if not activity_id:
                # If no ID can be found, prevent saving and show an error
                raise ValidationError('Could not extract a valid Activity ID from the provided LinkedIn URL. Please use the full post URL.')
            model.activity_id = activity_id
        super().on_model_change(form, model, is_created)

class SubmissionView(AuthView):
    can_create = False
    can_edit = False

class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        auth = request.authorization
        return (auth and auth.username == os.getenv('ADMIN_USER') and auth.password == os.getenv('ADMIN_PASS'))
    def inaccessible_callback(self, name, **kwargs):
        return Response('Authentication Required', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

# Admin Panel Setup
admin = Admin(app, name='Resource Admin', template_mode='bootstrap3', index_view=SecureAdminIndexView())
admin.add_view(PostResourceView(PostResource, db.session, name='Manage Posts'))
admin.add_view(SubmissionView(Submission, db.session, name='View Submissions'))

# --- UPDATED: Main API Route to use activity_id for lookups ---
@app.route('/api/request-resource', methods=['POST'])
def request_resource():
    data = request.get_json()
    
    # Extract the activity ID from the user's submitted URL
    linkedin_post_url_from_user = data.get('linkedin_post_url')
    extracted_id = extract_linkedin_activity_id(linkedin_post_url_from_user) if linkedin_post_url_from_user else None

    if not extracted_id:
        return jsonify({"status": "error", "message": "Invalid LinkedIn post URL provided."}), 400

    # Query the database using the extracted ID
    resource = PostResource.query.filter_by(activity_id=extracted_id).first()

    if not resource:
        return jsonify({"status": "error", "message": "Sorry, this LinkedIn post is not associated with a resource."}), 404

    # The rest of the logic remains the same...
    new_submission = Submission(
        name=data.get('name'), email=data.get('email'), position=data.get('position'), 
        company_college=data.get('company_college'), requested_resource_name=resource.resource_name
    )
    db.session.add(new_submission)
    db.session.commit()
    try:
        sender_email = os.getenv('EMAIL_ADDRESS')
        sender_password = os.getenv('EMAIL_PASSWORD')
        msg = MIMEMultipart()
        msg['From'] = f"Gitesh Malik <{sender_email}>"; msg['To'] = data.get('email')
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

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
