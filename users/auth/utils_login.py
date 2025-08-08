import logging
import time
import bcrypt
from flask import session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_LOGIN_ATTEMPT_LIMIT = 5
ADMIN_LOCKOUT_TIME = 300

USER_LOGIN_ATTEMPT_LIMIT = 5
USER_LOCKOUT_TIME = 300

def is_admin_locked_out():
    attempts = session.get('admin_login_attempts', 0)
    last_time = session.get('admin_last_attempt_time', 0)
    if attempts >= ADMIN_LOGIN_ATTEMPT_LIMIT and (time.time() - last_time) < ADMIN_LOCKOUT_TIME:
        return True
    return False

def increment_admin_login_attempts():
    session['admin_login_attempts'] = session.get('admin_login_attempts', 0) + 1
    session['admin_last_attempt_time'] = time.time()

def reset_admin_login_attempts():
    session.pop('admin_login_attempts', None)
    session.pop('admin_last_attempt_time', None)

def is_user_locked_out():
    attempts = session.get('user_login_attempts', 0)
    last_time = session.get('user_last_attempt_time', 0)
    if attempts >= USER_LOGIN_ATTEMPT_LIMIT and (time.time() - last_time) < USER_LOCKOUT_TIME:
        return True
    return False

def increment_user_login_attempts():
    session['user_login_attempts'] = session.get('user_login_attempts', 0) + 1
    session['user_last_attempt_time'] = time.time()

def reset_user_login_attempts():
    session.pop('user_login_attempts', None)
    session.pop('user_last_attempt_time', None)

def reset_admin_session():
    for key in ['admin_username', 'admin_email', 'admin_role', 'admin_login_step', 'admin_email_pending', 'admin_login_attempts', 'admin_last_attempt_time']:
        session.pop(key, None)

def verify_password(input_password, hashed_password):
    try:
        return bcrypt.checkpw(input_password.encode(), hashed_password.encode())
    except Exception:
        return False

def hash_password(password):
    try:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    except Exception:
        return None
