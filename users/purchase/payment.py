from flask import flash, jsonify, redirect, render_template, request, session, url_for
from users.purchase.user_db import UserOperation
from users.purchase.utils_payment import (get_session_user,is_valid_session,calculate_final_price,
generate_purchase_code,clear_payment_session_keys)
from datetime import datetime, timedelta
from users import users_bp
import razorpay
import string
import random
import os
import re

user_op = UserOperation()


RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_SECRET = os.environ.get("RAZORPAY_SECRET")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))

@users_bp.route('/payment/<course_code>/<unique_code>', methods=['GET'])
def payment(course_code, unique_code):
    username, email, phone = get_session_user()

    if not is_valid_session(username, email, phone):
        flash("Session expired. Please login again.", "login")
        return redirect(url_for('users.user_login'))

    user_cart_key = f'{email}_{course_code}_cart'
    cart_courses = session.get(user_cart_key)

    if not cart_courses:
        flash("No items in your cart.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    discount = session.get('discount', 0)
    _, _, final_amount = calculate_final_price(cart_courses, discount)
    amount_in_paise = int(final_amount * 100)

    try:
        razorpay_order = razorpay_client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': 1
        })
    except Exception as e:
        flash("Payment gateway error. Try again.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    session['razorpay_order_id'] = razorpay_order['id']
    session['current_course_payment'] = course_code

    return render_template('users/purchase/payment.html',
        razorpay_order_id=razorpay_order['id'],
        razorpay_key_id=RAZORPAY_KEY_ID,
        amount=amount_in_paise,
        username=username,
        email=email,
        phone=phone,
        course_code=course_code,
        unique_code=unique_code
    )
