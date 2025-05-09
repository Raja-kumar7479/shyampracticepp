import time
import bcrypt
from flask import session

RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_RESET_TIME = 300

def is_rate_limited():
    attempts = session.get('login_attempts', 0)
    last_time = session.get('last_attempt_time', 0)
    if attempts >= RATE_LIMIT_MAX_ATTEMPTS and (time.time() - last_time) < RATE_LIMIT_RESET_TIME:
        return True
    elif attempts >= RATE_LIMIT_MAX_ATTEMPTS:
        session.pop('login_attempts', None)
        session.pop('last_attempt_time', None)
    return False

def increment_login_attempts():
    session['login_attempts'] = session.get('login_attempts', 0) + 1
    session['last_attempt_time'] = time.time()

def reset_login_attempts():
    session.pop('login_attempts', None)
    session.pop('last_attempt_time', None)

def verify_password(input_password, hashed_password):
    return bcrypt.checkpw(input_password.encode(), hashed_password.encode())

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def reset_admin_session():
    keys = [
        'admin_username', 'admin_email', 'admin_role',
        'admin_login_step', 'admin_email_pending',
        'admin_login_attempts', 'admin_last_attempt_time'
    ]
    for k in keys:
        session.pop(k, None)