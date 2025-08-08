import hashlib
import hmac
import logging
import random, string
from datetime import datetime

from flask import session



def get_session_user():
    return session.get('user_username'), session.get('user_email'), session.get('validated_phone')

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

def process_cart_purchases(cart_courses, email, username, phone, payment_id,
                           amount_paid, discount_percent, original_price, course_code, payment_mode, status):
    purchases_data = []
    for course in cart_courses:
        price = course['price']
        course_discount_amt = round(price * discount_percent / 100, 2)
        final_price = round(price - course_discount_amt, 2)
        purchase_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        section = course.get('section')
        section_id = course.get('section_id')
        
        purchase_entry = {
            'email': email,
            'username': username,
            'phone': phone,
            'title': course['title'],
            'subtitle': course.get('subtitle', ''),
            'price': price,
            'original_price': price,
            'discount_percent': discount_percent,
            'final_price': final_price,
            'payment_date': datetime.now(),
            'payment_id': payment_id,
            'status': status,
            'purchase_code': purchase_code,
            'course_code': course_code,
            'section': section,
            'section_id': section_id,
            'payment_mode': payment_mode
        }
        purchases_data.append(purchase_entry)
    return purchases_data

def clear_payment_session(user_cart_key):
    keys_to_clear = [
        user_cart_key,
        'razorpay_order_id',
        'current_course_payment',
        'discount',
        'coupon_applied',
        'coupon_expiry'
    ]

    for key in keys_to_clear:
        session.pop(key, None)
    logging.info(f"Cleared payment session keys including cart: {user_cart_key}")
