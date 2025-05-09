from flask_mail import Mail, Message
import time
from flask import session
import pyotp

mail = Mail()


def send_otp_email(email, mail):
    if 'otp_secret' not in session:
        session['otp_secret'] = pyotp.random_base32()

    totp = pyotp.TOTP(session['otp_secret'], interval=300)
    otp = totp.now()
    otp_expiry = time.time() + 300
    session['otp'] = {'value': otp, 'expiry': otp_expiry}
    session['otp_last_sent'] = time.time()

    msg = Message('Reset Password OTP',
                  sender='your_email@gmail.com',
                  recipients=[email])
    
    msg.html = f"""
    <html>
      <head>
        <style>
          body {{
            font-family: 'Helvetica', Arial, sans-serif;
            background-color: #f7f7f7;
            margin: 0; padding: 0;
          }}
          .email-container {{
            max-width: 600px;
            margin: 30px auto;
            background-color: #fff;
            padding: 30px;
            border-radius: 10px;
            border: 1px solid #ddd;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
          }}
          .header {{
            font-size: 26px;
            color: #4e79c6;
            text-align: center;
            margin-bottom: 20px;
          }}
          .otp-box {{
            text-align: center;
            background-color: #f1f8ff;
            border: 2px solid #4e79c6;
            color: #4e79c6;
            font-size: 36px;
            font-weight: bold;
            padding: 20px;
            margin: 20px auto;
            width: 220px;
            border-radius: 8px;
          }}
          .content {{
            text-align: center;
            font-size: 16px;
            color: #555;
            line-height: 1.6;
          }}
          .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 14px;
            color: #999;
          }}
          .company-name {{
            color: #4e79c6;
            font-weight: bold;
          }}
        </style>
      </head>
      <body>
        <div class="email-container">
          <div class="header">Reset Password OTP</div>
          <p class="content">Use the OTP below to reset your password:</p>
          <div class="otp-box">{otp}</div>
          <p class="content">This OTP is valid for <strong>5 minutes</strong>.</p>
          <div class="footer">
            <p class="company-name">Shyam Practice Paper</p>
            <p>&copy; 2025 All Rights Reserved</p>
          </div>
        </div>
      </body>
    </html>
    """

    mail.send(msg)
