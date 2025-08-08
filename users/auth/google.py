import os
import pathlib
import requests
from flask import flash, render_template, session, abort, redirect, request, url_for
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import logging

from config import Config
from users.auth.user_db import UserOperation
from users import users_bp

user_op = UserOperation()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

client_secrets_file = os.path.join(
    pathlib.Path(__file__).parent, "client_secret.json"
)

def create_flow():
    return Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email"
        ],
        redirect_uri=Config.REDIRECT_URI
    )

@users_bp.route('/google_login')
def google_login():
    flow = create_flow()
    authorization_url, state = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        include_granted_scopes='true'
    )
    session["user_google_state"] = state
    logger.info("Google login initiated")
    return redirect(authorization_url)

@users_bp.route("/callback")
def callback():
    if session.get("user_google_id"):
        return redirect(url_for('users.login_success'))

    if session.get("user_google_state") != request.args.get("state"):
        abort(403, description="Invalid state parameter")

    flow = create_flow()
    try:
        flow.fetch_token(authorization_response=request.url)
    except Exception:
        abort(400, description="Failed to fetch token from Google")
    
    logger.info("Google token fetched successfully")

    credentials = flow.credentials
    request_session = requests.session()
    token_request = google.auth.transport.requests.Request(session=cachecontrol.CacheControl(request_session))

    try:
        id_info = id_token.verify_oauth2_token(
            credentials._id_token,
            token_request,
            Config.GOOGLE_CLIENT_ID
        )
    except ValueError:
        abort(400, description="Invalid ID token")
    
    logger.info("Google ID token verified")

    if not id_info.get("email_verified"):
        abort(403, description="Email not verified")

    user_email = id_info.get("email")
    user_name = id_info.get("name")
    user_oauth_id = id_info.get("sub")

    existing_user = user_op.get_user_by_email(user_email)

    if existing_user:
        auth_type = existing_user.get("auth_type", "manual").lower()
        if auth_type == "manual":
            user_op.update_auth_type_to_both(user_email, user_oauth_id)
            logger.info(f"Updated auth_type to 'both' for user {user_email}")
    else:
        user_op.insert_user_google(user_name, user_email, user_oauth_id)
        logger.info(f"New Google user created: {user_email}")

    user_session_keys = ['user_username', 'user_email', 'user_google_id', 'user_google_state', 'user_login_step', 'user_email_pending']
    for key in user_session_keys:
        session.pop(key, None)

    session["user_google_id"] = user_oauth_id
    session["user_username"] = user_name
    session["user_email"] = user_email
    session.permanent = True

    flash("Login successful via Google!", "login_success")
    logger.info(f"User login successful via Google for {user_email}")
    return redirect(url_for('users.login_success'))

@users_bp.route('/login_success')
def login_success():
    return render_template('users/auth/spineer.html')
