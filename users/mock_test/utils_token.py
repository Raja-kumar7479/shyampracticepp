import time
import hmac
import hashlib
import secrets
from flask import current_app
import logging

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_BUFFER_SECONDS = 30  

def generate_test_token(email, test_id, duration_seconds):
    """
    Generates a secure HMAC token for a test session.
    """
    secret_key = current_app.config['TEST_TOKEN_SECRET']
    timestamp = int(time.time())
    nonce = secrets.token_hex(16)
    data = f"{email}:{test_id}:{timestamp}:{nonce}:{duration_seconds}"
    signature = hmac.new(secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()
    return f"{data}:{signature}"


def validate_test_token(token, email, test_id):
    """
    Validates the HMAC token and checks for expiry.
    """
    if not token:
        return False

    try:
        parts = token.split(':')
        if len(parts) != 6:
            return False

        email_from_token, test_id_from_token, timestamp_str, nonce, duration_str, received_signature = parts
        timestamp = int(timestamp_str)
        duration = int(duration_str)

        # Check for email/test ID match
        if email != email_from_token or test_id != test_id_from_token:
            return False

        # Recreate signature
        data = f"{email}:{test_id}:{timestamp}:{nonce}:{duration}"
        secret_key = current_app.config['TEST_TOKEN_SECRET']
        expected_signature = hmac.new(secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_signature, received_signature):
            return False

        # Check expiry
        current_time = int(time.time())
        expiry_time = timestamp + duration + TOKEN_EXPIRY_BUFFER_SECONDS
        if current_time > expiry_time:
            return False

        return True
    except Exception as e:
        logger.exception(f"[TOKEN VALIDATION ERROR] {e}")
        return False
