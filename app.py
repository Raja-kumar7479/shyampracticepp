from flask import Flask, make_response, render_template, jsonify, session
from flask_mail import Mail
from flask_session import Session
from extensions import init_limiter
from redis import Redis
from dotenv import load_dotenv
import logging
from config import Config
from datetime import timedelta

from admin import admin_bp
from users import users_bp


load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)


Session(app)

app.config.update({
    'SESSION_TYPE': 'redis',
    'SESSION_REDIS': Redis(host='localhost', port=6379, decode_responses=True),
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'SESSION_PERMANENT': True,
    'PERMANENT_SESSION_LIFETIME': timedelta(minutes=30)
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


init_limiter(app)


mail = Mail(app)

app.register_blueprint(admin_bp)
app.register_blueprint(users_bp)


@app.before_request
def make_session_permanent():
    session.permanent = True


@app.context_processor
def inject_user():
    try:
        return dict(
            username=str(session.get('username', '')),
            email=str(session.get('email', ''))
        )
    except Exception:
        return dict(username='', email='')

@app.route('/')
def index():
    username = session.get('username') or session.get('username')
    email = session.get('email')
    logged_in = bool(username and email)
    return render_template(
        'users/index/index.html',
        username=username,
        email=email,
        logged_in=logged_in
    )

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

@app.errorhandler(400)
def handle_400(error):
    return jsonify({
        "error": "Bad Request",
        "message": error.description or "The server could not understand the request."
    }), 400

@app.errorhandler(403)
def handle_403(error):
    return jsonify({
        "error": "Forbidden",
        "message": error.description or "You don't have permission to access this resource."
    }), 403

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
