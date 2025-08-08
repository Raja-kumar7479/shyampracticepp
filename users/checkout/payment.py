from flask import (
    jsonify,
    request,
    session,
    flash,redirect, render_template,url_for
)
from users import users_bp
from users.checkout.user_db import UserOperation
from extensions import user_login_required
import logging
import razorpay
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

user_op = UserOperation()

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_SECRET = os.environ.get("RAZORPAY_SECRET")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))

def get_session_user():
    username = session.get('user_username')
    email = session.get('user_email')
    phone = session.get('user_phone')
    return username, email, phone

def is_valid_session(username, email, phone):
    return username and email and phone

def calculate_final_price(cart_courses, discount):
    total_price = sum(c.get('price', 0) for c in cart_courses)
    discount_amount = round(total_price * discount / 100, 2)
    final_amount = round(total_price - discount_amount, 2)
    return total_price, discount_amount, final_amount


@users_bp.route('/payment/<course_code>/<unique_code>', methods=['GET'])
@user_login_required
def payment(course_code, unique_code):
    username, email, phone = get_session_user()

    if not is_valid_session(username, email, phone):
        flash("Session expired. Please login again.", "login_warning")
        return redirect(url_for('users.user_login'))

    user_cart_key = f'user_{email}_cart'
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
        flash("Payment gateway error. Try again.", "cart_error")
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
