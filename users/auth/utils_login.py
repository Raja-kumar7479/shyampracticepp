from flask import session
import time
from users.auth.user_db import UserOperation


user_op = UserOperation()
RATE_LIMIT_MAX_ATTEMPTS = 100
RATE_LIMIT_RESET_TIME = 30  

def is_locked_out():
    attempts = session.get('login_attempts', 0)
    last_time = session.get('last_attempt_time', 0)

    if attempts >= RATE_LIMIT_MAX_ATTEMPTS and (time.time() - last_time < RATE_LIMIT_RESET_TIME):
        return True
    elif time.time() - last_time >= RATE_LIMIT_RESET_TIME:
        # Reset tracking after timeout
        session.pop('login_attempts', None)
        session.pop('last_attempt_time', None)
    return False

