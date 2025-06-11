import pyotp
import time
from flask import session
import re
from flask_mail import Message

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

def generate_otp():
    otp_secret = pyotp.random_base32()
    otp_value = pyotp.TOTP(otp_secret, interval=OTP_VALIDITY_PERIOD).now()
    session['otp'] = {'value': otp_value, 'expiry': time.time() + OTP_VALIDITY_PERIOD}
    session['otp_secret'] = otp_secret
    return otp_value

def validate_otp(user_otp):
    otp_data = session.get('otp')
    if not otp_data or time.time() > otp_data['expiry']:
        return False, "OTP expired or invalid."
    return user_otp == otp_data['value'], "Invalid OTP."

def clear_signup_session():
    for key in ['signup_data', 'otp_data', 'otp', 'otp_secret', 'otp_last_sent', 'otp_attempts']:
        session.pop(key, None)

def send_signup_email_otp(username, email, otp_value, mail):
    msg = Message(
        subject='Signup OTP Verification',
        sender='your-email@example.com',  
        recipients=[email]
    )

    msg.html = f"""
    <html>
      <head>
        <style>
          body {{
            background: #f4f4f4;
            font-family: Arial, sans-serif;
            padding: 0;
            margin: 0;
          }}
          .email-box {{
            background: #ffffff;
            max-width: 500px;
            margin: 40px auto;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
          }}
          h2 {{
            color: #333333;
            margin-bottom: 20px;
          }}
          .otp {{
            font-size: 36px;
            font-weight: bold;
            background: #e6f0ff;
            color: #1a73e8;
            padding: 15px 25px;
            display: inline-block;
            border-radius: 6px;
            margin: 20px 0;
            letter-spacing: 4px;
          }}
          p {{
            font-size: 15px;
            color: #666666;
            line-height: 1.6;
          }}
          .footer {{
            margin-top: 30px;
            font-size: 13px;
            color: #aaaaaa;
            border-top: 1px solid #eeeeee;
            padding-top: 20px;
          }}
          .brand {{
            color: #1a73e8;
            font-weight: bold;
          }}
        </style>
      </head>
      <body>
        <div class="email-box">
          <h2>Verify Your Email</h2>
          <p>Hello <strong>{username}</strong>,</p>
          <p>Thank you for signing up at <span class="brand">Shyam Practice Paper</span>.<br>
          Use the OTP below to complete your signup:</p>
          <div class="otp">{otp_value}</div>
          <p>This OTP is valid for <strong>5 minutes</strong>.</p>
          <div class="footer">
            <p>If you did not request this, please ignore this email.</p>
            <p>&copy; 2025 <span class="brand">Shyam Practice Paper</span>. All rights reserved.</p>
          </div>
        </div>
      </body>
    </html>
    """
    
    mail.send(msg)

def send_signup_success_email(username, email, mail):
    msg = Message(
        subject='Welcome to Shyam Practice Paper!',
        sender='your-email@example.com',  # replace with your actual sender
        recipients=[email]
    )

    msg.html = f"""
    <html>
      <head>
        <style>
          body {{
            background-color: #f8f8f8;
            font-family: Arial, sans-serif;
            padding: 0;
            margin: 0;
          }}
          .container {{
            max-width: 500px;
            margin: 30px auto;
            padding: 20px;
            background: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
          }}
          h2 {{
            color: #008080;
            margin-bottom: 20px;
          }}
          p {{
            font-size: 16px;
            color: #333333;
            line-height: 1.6;
          }}
          .username {{
            color: #008080;
            font-weight: bold;
          }}
          .footer {{
            margin-top: 30px;
            font-size: 13px;
            color: #999999;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <h2>Signup Successful!</h2>
          <p>Hi <span class="username">{username}</span>,</p>
          <p>Welcome to <strong>Shyam Practice Paper</strong>.<br>
          Your account has been created successfully.</p>
          <p>You're now ready to explore our platform and start practicing!</p>
          <div class="footer">
            <p>&copy; 2025 Shyam Practice Paper. All rights reserved.</p>
          </div>
        </div>
      </body>
    </html>
    """

    mail.send(msg)
