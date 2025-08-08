import logging
from flask import flash, session
from users.checkout.user_db import UserOperation

user_op = UserOperation()
logger = logging.getLogger(__name__)

def is_user_logged_in():
    user_username = session.get('user_username')
    user_email = session.get('user_email')
    if not user_username or not user_email:
        logger.warning("Session expired: user is not logged in.")
        flash("Session expired. Please login again.", "login")
        return False, user_username, user_email
    logger.info(f"User {user_email} is logged in.")
    return True, user_username, user_email

def add_to_cart(user_cart_key, form):
    cart_courses = session.get(user_cart_key, [])
    new_course = {
        'title': form.get('title'),
        'subtitle': form.get('subtitle'),
        'price': float(form.get('price')),
        'section': form.get('section'),
        'section_id': form.get('section_id')
    }
    if not any(c['title'] == new_course['title'] and c['subtitle'] == new_course['subtitle'] for c in cart_courses):
        cart_courses.append(new_course)
        session[user_cart_key] = cart_courses
        for key in ['show_billing', 'discount', 'coupon_applied', 'coupon_expiry']:
            session.pop(key, None)
        flash(f"{new_course['title']} added to cart.", "cart_notification")
        logger.info(f"Course '{new_course['title']}' added to cart for session {user_cart_key}.")
    else:
        flash("Course already added.", "cart_warning")
        logger.warning(f"Attempt to add duplicate course '{new_course['title']}' to cart for session {user_cart_key}.")

def remove_from_cart(user_cart_key, title, email):
    cart_courses = [c for c in session.get(user_cart_key, []) if c['title'] != title]
    session[user_cart_key] = cart_courses
    flash(f"{title} removed from cart.", "cart_notification")
    logger.info(f"Course '{title}' removed from cart for session {user_cart_key}.")

    total = sum(c['price'] for c in cart_courses)
    if 'coupon_applied' in session:
        coupon = user_op.get_coupon_by_code(session['coupon_applied'], email)
        if coupon and total < coupon[0]['min_purchase']:
            for key in ['discount', 'coupon_applied', 'coupon_expiry']:
                session.pop(key, None)
            flash("Coupon removed due to insufficient purchase total.", "cart_warning")
            logger.warning(f"Coupon '{session.get('coupon_applied')}' removed due to insufficient purchase total for session {user_cart_key}.")
    return cart_courses

def apply_coupon(user_cart_key, coupon_code, email):
    cart_courses = session.get(user_cart_key, [])
    total = sum(c['price'] for c in cart_courses)
    coupons = user_op.get_coupon_by_code(coupon_code, email)
    if coupons:
        coupon = coupons[0]
        if total >= coupon['min_purchase']:
            session['discount'] = coupon['discount']
            session['coupon_applied'] = coupon['coupon_code']
            session['coupon_expiry'] = coupon['expiry_date'].strftime('%Y-%m-%d')
            flash("Coupon applied successfully!", "cart_notification")
            logger.info(f"Coupon '{coupon_code}' applied successfully to cart for session {user_cart_key}.")
        else:
            flash(f"Minimum ₹{coupon['min_purchase']} required for this coupon.", "cart_warning")
            logger.warning(f"Coupon '{coupon_code}' not applied: minimum purchase not met for session {user_cart_key}.")
    else:
        flash("Invalid or expired coupon.", "cart_warning")
        logger.warning(f"Failed to apply coupon '{coupon_code}': invalid or expired.")

def clear_cart(user_cart_key):
    session[user_cart_key] = []
    for key in ['discount', 'coupon_applied', 'coupon_expiry']:
        session.pop(key, None)
    flash("Cart cleared.", "cart_notification")
    logger.info(f"Cart cleared for session {user_cart_key}.")
