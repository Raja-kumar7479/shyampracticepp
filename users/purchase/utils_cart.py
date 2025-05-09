from flask import flash, jsonify, redirect, render_template, request, session, url_for
from users.purchase.user_db import UserOperation
from datetime import datetime, timedelta
import re

user_op = UserOperation()

def is_user_logged_in():
    username = session.get('username')
    email = session.get('email')
    if not username or not email:
        flash("Session expired. Please login again.", "login")
        return False, username, email
    return True, username, email

def add_to_cart(user_cart_key, form):
    cart_courses = session.get(user_cart_key, [])
    new_course = {
        'title': form.get('title'),
        'subtitle': form.get('subtitle'),
        'price': float(form.get('price'))
    }
    if not any(c['title'] == new_course['title'] and c['subtitle'] == new_course['subtitle'] for c in cart_courses):
        cart_courses.append(new_course)
        session[user_cart_key] = cart_courses
        for key in ['show_billing', 'discount', 'coupon_applied', 'coupon_expiry']:
            session.pop(key, None)
        flash(f"{new_course['title']} added to cart.", "cart_notification")
    else:
        flash("Course already added.", "cart_warning")

def remove_from_cart(user_cart_key, title, email):
    cart_courses = [c for c in session.get(user_cart_key, []) if c['title'] != title]
    session[user_cart_key] = cart_courses
    flash(f"{title} removed from cart.", "cart_notification")

    total = sum(c['price'] for c in cart_courses)
    if 'coupon_applied' in session:
        coupon = user_op.get_coupon_by_code(session['coupon_applied'], email)
        if coupon and total < coupon[0]['min_purchase']:
            for key in ['discount', 'coupon_applied', 'coupon_expiry']:
                session.pop(key, None)
            flash("Coupon removed due to insufficient purchase total.", "cart_warning")
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
        else:
            flash(f"Minimum ₹{coupon['min_purchase']} required for this coupon.", "cart_warning")
    else:
        flash("Invalid or expired coupon.", "cart_warning")

def clear_cart(user_cart_key):
    session[user_cart_key] = []
    for key in ['discount', 'coupon_applied', 'coupon_expiry']:
        session.pop(key, None)
    flash("Cart cleared.", "cart_notification")
