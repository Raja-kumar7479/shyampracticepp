from datetime import timedelta, datetime
import re
from flask import flash, jsonify, redirect, render_template, request, session, url_for
from users.purchase.user_db import UserOperation
from users import users_bp


def validate_phone_number(phone_number):
    phone_number = phone_number.strip()
    if not phone_number.isdigit() or len(phone_number) != 10 or phone_number[0] == '0':
        return False, "Invalid phone number. Please enter a valid 10-digit number starting from 1-9."
    return True, None

@users_bp.route('/validate_phone/<course_code>/<unique_code>', methods=['POST'])
def validate_phone(course_code, unique_code):
    username = session.get('username')
    email = session.get('email')
    if not username or not email:
        flash("Login first.", "login")
        return redirect(url_for('users.user_login'))

    phone = request.form.get('phone_number', '').strip()
    valid, error = validate_phone_number(phone)
    if not valid:
        flash(error, "cart_warning")
        return redirect(url_for('users.add_cart', course_code=course_code, unique_code=unique_code))

    session['validated_phone'] = phone
    flash("Phone number validated. Fill billing details.", "cart_notification")
    # 🛠 Redirect with query param show_billing=true
    return redirect(url_for('users.add_cart', course_code=course_code, unique_code=unique_code, show_billing='true'))
