import pyotp
import time
from flask import session, current_app as app
from flask_mail import Message
import re
import bcrypt

OTP_VALIDITY_PERIOD = 300

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_password_secure(password):
    return (
        len(password) >= 8 and
        any(c.isupper() for c in password) and
        any(c.isdigit() for c in password) and
        any(c in "!@#$%^&*()-_=+[{]}\|;:'\",<.>/?`~" for c in password)
    )
def clear_signup_session():
    """Clear temporary signup data and OTP-related session keys."""
    keys_to_clear = ['signup_data', 'otp', 'otp_secret', 'otp_last_sent', 'otp_verified', 'signup_step']
    for key in keys_to_clear:
        session.pop(key, None)

def generate_otp():
    otp_secret = pyotp.random_base32()
    otp_value = pyotp.TOTP(otp_secret, interval=OTP_VALIDITY_PERIOD).now()
    session['otp'] = {'value': otp_value, 'expiry': time.time() + OTP_VALIDITY_PERIOD}
    session['otp_secret'] = otp_secret
    return otp_value

def validate_otp(user_otp):
    otp_data = session.get('otp')
    if not otp_data or time.time() > otp_data['expiry']:
        clear_signup_session()
        return False, "OTP expired or invalid. Please start over."
    return (user_otp == otp_data['value']), "Invalid OTP."


def send_signup_email_otp(username, email, otp_value, mail):
    msg = Message('Signup OTP Verification',
                  sender='your-email@example.com',
                  recipients=[email])

    msg.html = f"""
    <html>
      <head>
        <style>
          body {{
            font-family: 'Helvetica', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f7f7f7;
          }}
          .email-container {{
            max-width: 600px;
            margin: 30px auto;
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            border: 1px solid #ddd;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
          }}
          .header {{
            text-align: center;
            font-size: 28px;
            color: #333333;
            font-weight: bold;
            margin-bottom: 20px;
          }}
          .otp-box {{
            text-align: center;
            background-color: #f1f8ff;
            border: 2px solid #4e79c6;
            color: #4e79c6;
            font-size: 40px;
            font-weight: bold;
            padding: 20px;
            margin: 20px auto;
            width: 220px;
            border-radius: 8px;
          }}
          .content {{
            font-size: 16px;
            color: #666666;
            line-height: 1.6;
            text-align: center;
          }}
          .footer {{
            font-size: 14px;
            color: #999999;
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
          }}
          .company-name {{
            font-weight: bold;
            color: #4e79c6;
          }}
        </style>
      </head>
      <body>
        <div class="email-container">
          <div class="header">OTP Verification</div>
          <p class="content">Hi <strong>{username}</strong>,</p>
          <p class="content">Thank you for signing up with Shyam Practice Paper. Please use the OTP below to complete your registration process.</p>
          <div class="otp-box">{otp_value}</div>
          <p class="content">This OTP will expire in <strong>5 minutes</strong>. Please make sure to use it within this time frame.</p>
          <div class="footer">
            <p class="content">If you didn't request this, please ignore this email.</p>
            <p class="company-name">Shyam Practice Paper</p>
            <p>&copy; 2025 All Rights Reserved</p>
          </div>
        </div>
      </body>
    </html>
    """
    mail.send(msg)
