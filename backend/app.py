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
from urllib.parse import urlparse, urlunparse, parse_qs # NEW: Import URL parsing tools

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

# --- NEW: URL Normalization Function ---
def normalize_linkedin_url(url_string):
    """
    Normalizes a LinkedIn URL by standardizing scheme, domain, path,
    and removing common tracking parameters.
    """
    if not isinstance(url_string, str):
        return None

    # Step 1: Basic cleanup and lowercase
    url_string = url_string.strip().lower()

    # Step 2: Parse the URL
    parsed_url = urlparse(url_string)

    # Step 3: Standardize scheme and netloc (domain) to 'https' and 'www.linkedin.com'
    scheme = 'https'
    netloc = 'www.linkedin.com' # Force www.linkedin.com for consistency

    # Step 4: Clean the path: remove trailing slash unless it's just '/'
    path = parsed_url.path
    if path.endswith('/') and len(path) > 1: # Only remove if path is not just '/'
        path = path[:-1]

    # Step 5: Clean query parameters: remove common LinkedIn tracking parameters
    query_params = parse_qs(parsed_url.query)
    # Common tracking parameters to remove
    tracking_params_to_remove = ['trk', 'utm_source', 'utm_medium', 'utm_campaign', 'd_id', 'client_context', 'originalsubdomain']
    
    cleaned_query_list = []
    for key, values in query_params.items():
        if key not in tracking_params_to_remove:
            for value in values: # Assuming single value per key for simplicity
                cleaned_query_list.append(f"{key}={value}")
    cleaned_query = '&'.join(cleaned_query_list)

    # Step 6: Reconstruct the normalized URL
    normalized_url_parts = (
        scheme,
        netloc,
        path,
        parsed_url.params, # Keep parameters (e.g., ;jsessionid) if they exist in path
        cleaned_query,
        '' # Always remove fragment
    )
    return urlunparse(normalized_url_parts)


# Database Models
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

# Secure Admin Views with Basic Auth
class AuthView(ModelView):
    def is_accessible(self):
        auth = request.authorization
        return (auth and
                auth.username == os.getenv('ADMIN_USER') and
                auth.password == os.getenv('ADMIN_PASS'))

    def inaccessible_callback(self, name, **kwargs):
        return Response('Authentication Required', 401, {
            'WWW-Authenticate': 'Basic realm="Login Required"'
        })

# --- NEW: PostResourceView with URL Normalization ---
class PostResourceView(AuthView): # Inherit from AuthView for security
    column_list = ('resource_name', 'post_url', 'resource_link')
    
    # Override on_model_change to normalize URL before saving or updating
    def on_model_change(self, form, model, is_created):
        if model.post_url:
            model.post_url = normalize_linkedin_url(model.post_url)
        super(PostResourceView, self).on_model_change(form, model, is_created) # Call parent method

class SubmissionView(AuthView): # Inherit from AuthView for security
    column_list = ('timestamp', 'name', 'email', 'position', 'company_college', 'requested_resource_name')
    can_create = False
    can_edit = False
    can_delete = True

class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        auth = request.authorization
        return (auth and
                auth.username == os.getenv('ADMIN_USER') and
                auth.password == os.getenv('ADMIN_PASS'))

    def inaccessible_callback(self, name, **kwargs):
        return Response('Authentication Required', 401, {
            'WWW-Authenticate': 'Basic realm="Login Required"'
        })

# Admin Panel Setup
admin = Admin(app, name='Resource Admin', template_mode='bootstrap3', index_view=SecureAdminIndexView())
# Use our custom PostResourceView for normalization
admin.add_view(PostResourceView(PostResource, db.session, name='Manage Posts'))
admin.add_view(SubmissionView(Submission, db.session, name='View Submissions'))

# Main API Route
@app.route('/api/request-resource', methods=['POST'])
def request_resource():
    data = request.get_json()
    
    # --- NEW: Normalize the incoming URL from the user ---
    linkedin_post_url_from_user = data.get('linkedin_post_url')
    if linkedin_post_url_from_user:
        # Normalize the user's input URL before querying the database
        normalized_linkedin_post_url = normalize_linkedin_url(linkedin_post_url_from_user)
    else:
        # Handle case where URL is missing from input
        normalized_linkedin_post_url = None

    # Query the database using the normalized URL
    resource = PostResource.query.filter_by(post_url=normalized_linkedin_post_url).first()

    if not resource:
        return jsonify({"status": "error", "message": "Sorry, this LinkedIn post is not associated with a resource."}), 404

    new_submission = Submission(
        name=data.get('name'),
        email=data.get('email'),
        position=data.get('position'),
        company_college=data.get('company_college'),
        requested_resource_name=resource.resource_name
    )
    db.session.add(new_submission)
    db.session.commit()

    try:
        sender_email = os.getenv('EMAIL_ADDRESS')
        sender_password = os.getenv('EMAIL_PASSWORD')
        msg = MIMEMultipart()
        msg['From'] = f"Gitesh Malik <{sender_email}>"
        msg['To'] = data.get('email')
        msg['Subject'] = f"Here is your requested resource: {resource.resource_name}"
        body = f"""Hi {data.get('name')},

Here is the resource you requested:
Resource: {resource.resource_name}
Download Link: {resource.resource_link}

Best,
Gitesh Malik"""
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return jsonify({"status": "success", "message": "Success! The resource has been sent."}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": "An error occurred while sending the email."}), 500

# Automatic Database Initialization on startup
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
