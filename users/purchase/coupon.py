import re
from datetime import datetime, timedelta

from flask import (
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from users import users_bp
from users.purchase.user_db import UserOperation

user_op = UserOperation()

@users_bp.route('/get_coupons')
def get_coupons():
    coupons = user_op.get_all_active_coupons()
    formatted_coupons = []
    for coupon in coupons:
        coupon_dict = coupon.copy()
        if 'expiry_date' in coupon and coupon['expiry_date']:
            if hasattr(coupon['expiry_date'], 'strftime'):
                coupon_dict['expiry_date'] = coupon['expiry_date'].strftime('%Y-%m-%d')
        formatted_coupons.append(coupon_dict)
    return jsonify({"coupons": formatted_coupons})



@users_bp.route('/apply_coupon/<course_code>/<unique_code>', methods=['POST'])
def apply_coupon(course_code, unique_code):
    email = session.get('email')
    coupon_code = request.form.get('coupon_code')

    if not coupon_code:
        return jsonify({"status": "fail", "message": "No coupon provided"}), 400

    coupons = user_op.get_coupon_by_code(coupon_code, email)
    if not coupons:
        return jsonify({"status": "fail", "message": "Invalid or expired coupon"}), 404

    user_key = f'{email}_{course_code}_added_courses'
    cart_courses = session.get(user_key, [])
    total_price = sum(c.get('price', 0) for c in cart_courses)

    valid_coupon = next((c for c in coupons if total_price >= c.get('min_purchase', 0)), None)
    if not valid_coupon:
        min_purchase = coupons[0]['min_purchase']
        return jsonify({
            "status": "fail",
            "message": f"Minimum purchase ₹{min_purchase:.2f} required to apply this coupon."
        }), 400

    session['discount'] = valid_coupon['discount']
    session['coupon_applied'] = valid_coupon['coupon_code']
    session['coupon_expiry'] = (
        valid_coupon['expiry_date'].strftime('%Y-%m-%d') if hasattr(valid_coupon['expiry_date'], 'strftime') else valid_coupon['expiry_date']
    )

    return jsonify({
        "status": "success",
        "discount": valid_coupon['discount'],
        "coupon": valid_coupon['coupon_code'],
        "expiry_date": session['coupon_expiry']
    })
