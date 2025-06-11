import time
import bcrypt
from flask import session

USER_RATE_LIMIT_MAX_ATTEMPTS = 5
USER_RATE_LIMIT_RESET_TIME = 300

def is_rate_limited():
    attempts = session.get('user_login_attempts', 0)
    last_time = session.get('user_last_attempt_time', 0)
    if attempts >= USER_RATE_LIMIT_MAX_ATTEMPTS and (time.time() - last_time) < USER_RATE_LIMIT_RESET_TIME:
        return True
    elif attempts >= USER_RATE_LIMIT_MAX_ATTEMPTS:
        session.pop('user_login_attempts', None)
        session.pop('user_last_attempt_time', None)
    return False

def increment_login_attempts():
    session['user_login_attempts'] = session.get('user_login_attempts', 0) + 1
    session['user_last_attempt_time'] = time.time()

def reset_login_attempts():
    session.pop('user_login_attempts', None)
    session.pop('user_last_attempt_time', None)

def reset_admin_session():
    keys = ['username', 'email', 'user_login_step', 'user_login_attempts', 'user_last_attempt_time']
    for k in keys:
        session.pop(k, None)

def verify_password(input_password, hashed_password):
    return bcrypt.checkpw(input_password.encode(), hashed_password.encode())

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
