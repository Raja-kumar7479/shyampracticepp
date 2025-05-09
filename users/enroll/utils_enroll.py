import os
import hmac
import base64
import uuid
import hashlib

def generate_secure_code(email, course_name):
    secret_key = os.environ.get("ENROLL_SECRET_KEY")
    if not secret_key:
        raise ValueError("ENROLL_SECRET_KEY must be set in environment variables.")

    raw_data = f"{email}:{course_name}:{uuid.uuid4()}".encode()

    hmac_digest = hmac.new(secret_key.encode(), raw_data, hashlib.sha512).digest()

    secure_code = base64.urlsafe_b64encode(hmac_digest).decode().rstrip('=')

    return secure_code[:40]
