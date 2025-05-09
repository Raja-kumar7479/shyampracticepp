import hashlib
import hmac
import random, string
from datetime import datetime
from users.purchase.payment import RAZORPAY_KEY_ID,RAZORPAY_SECRET
from flask import session, flash, redirect, url_for


def get_session_user():
    username = session.get('username')
    email = session.get('email')
    phone = session.get('validated_phone')
    if not all([username, email, phone]):
        return None, None, None
    return username, email, phone

def calculate_final_price(cart_courses, discount=0):
    total = sum(c['price'] for c in cart_courses)
    discount_amount = round(total * discount / 100, 2)
    final_amount = round(total - discount_amount, 2)
    return total, discount_amount, final_amount


def verify_hmac_signature(order_id, payment_id, signature, secret):
    generated_signature = hmac.new(
        secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(generated_signature, signature)

def is_payment_info_valid(email, username, payment_id):
    if not all([email, username, payment_id]):
        return False
    return True

def validate_unique_code(user_op, email, course_code, unique_code):
    stored_code = user_op.get_user_unique_code(email, course_code)
    return stored_code == unique_code

def process_cart_purchases(user_op, cart_courses, email, username, phone, payment_id,
                           amount_paid, discount_percent, original_price, course_code):

    for course in cart_courses:
        price = course['price']
        course_discount_amt = round(price * discount_percent / 100, 2)
        final_price = round(price - course_discount_amt, 2)
        
        purchase_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        user_op.add_purchase(
            email=email,
            username=username,
            phone=phone,
            title=course['title'],
            subtitle=course['subtitle'],
            price=price,
            original_price=price,  # corrected
            discount_percent=discount_percent,
            final_price=final_price,
            payment_date=datetime.now(),
            payment_id=payment_id,
            status='Paid',
            purchase_code=purchase_code,
            course_code=course_code
        )

def clear_payment_session(user_cart_key):
    keys_to_clear = [
        user_cart_key, 'razorpay_order_id', 'current_course_payment',
        'discount', 'coupon_applied', 'coupon_expiry'
    ]
    for key in keys_to_clear:
        session.pop(key, None)
