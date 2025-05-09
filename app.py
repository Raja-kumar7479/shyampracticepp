from flask import Flask, make_response, render_template, jsonify
from flask_mail import Mail
from extensions import init_limiter
from dotenv import load_dotenv
import logging
from config import Config

from admin import admin_bp
from users import users_bp

app = Flask(__name__)
app.config.from_object(Config)
load_dotenv()

init_limiter(app)

mail = Mail(app)
   
app.register_blueprint(admin_bp)
app.register_blueprint(users_bp)

app.config.update({
    'SESSION_TYPE': 'filesystem',
    'PERMANENT_SESSION_LIFETIME': 1800,
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax'
})

@app.after_request
def add_security_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

from flask import session

@app.context_processor
def inject_user():
    try:
        username = str(session.get('username', ''))
        email = str(session.get('email', ''))
        return dict(username=username, email=email)
    except Exception:
        return dict(username='', email='')

@app.route('/')
def index():
    username = session.get('username')
    email = session.get('email')

    response = make_response(render_template(
        'users/index/index.html',
        username=username,
        email=email
    ))

    # Prevent caching (for security after logout)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "404 Not Found", "message": "The requested URL was not found on the server."}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "500 Internal Server Error", "message": "An internal error occurred. Please try again later."}), 500

@app.errorhandler(403)
def forbidden_error(error):
    return jsonify({"error": "403 Forbidden", "message": "You do not have permission to access this resource."}), 403

@app.errorhandler(401)
def unauthorized_error(error):
    return jsonify({"error": "401 Unauthorized", "message": "You must be logged in to access this page."}), 401

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )
    try:
        app.run(debug=False, port=5002)
    except Exception as e:
        logging.exception("Failed to start the app: %s", e)
