from io import BytesIO
from mailbox import Message
from flask import  flash, redirect,request, send_file, session, url_for
from users.purchase.user_db import UserOperation
from users.purchase.utils_success import (get_session_user,is_payment_info_valid,
 validate_unique_code,process_cart_purchases,clear_payment_session,verify_hmac_signature)
from users.purchase.user_db import UserOperation
from users.purchase.payment import RAZORPAY_SECRET
from users.purchase.utils_receipt import generate_pdf_receipt,verify_download_token
from users import users_bp
from flask_mail import Message
from flask_mail import Mail


mail = Mail()
user_op = UserOperation()

@users_bp.route('/payment_success/<course_code>/<unique_code>', methods=['POST'])
def payment_success(course_code, unique_code):
    username, email, phone = get_session_user()
    if not all([username, email, phone]):
        flash("Session expired. Please login again.", "login")
        return redirect(url_for('users.user_login'))

    payment_id = request.form.get('razorpay_payment_id')
    order_id = request.form.get('razorpay_order_id')
    signature = request.form.get('razorpay_signature')

    # 1. Check payment validity
    if not all([payment_id, order_id, signature]):
        flash("Missing payment information.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    if not verify_hmac_signature(order_id, payment_id, signature, RAZORPAY_SECRET):
        flash("Payment verification failed.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    if not is_payment_info_valid(email, username, payment_id):
        flash("Invalid payment attempt.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    if not validate_unique_code(user_op, email, course_code, unique_code):
        flash("Unauthorized access detected!", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    # 2. Check cart
    user_cart_key = f'{email}_{course_code}_cart'
    cart_courses = session.get(user_cart_key)
    if not cart_courses:
        flash("Cart is empty or expired after payment.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    # 3. Calculate discount from session
    total_price = sum(c['price'] for c in cart_courses)
    discount = session.get('discount', 0)
    discount_amount = round(total_price * discount / 100, 2)
    final_amount = round(total_price - discount_amount, 2)

    # 4. Store final amount in database with purchase
    process_cart_purchases(
        user_op=user_op,
        cart_courses= cart_courses,
        email=email,
        username=username,
        phone=phone,
        payment_id=payment_id,
        course_code=course_code,
        amount_paid=final_amount,
        discount_percent=discount,
        original_price=total_price
    )

    # 5. Clear session
    clear_payment_session(user_cart_key)
    for key in ['discount', 'coupon_applied', 'coupon_expiry']:
        session.pop(key, None)

    # 6. Generate and email receipt
    purchases = user_op.get_purchase_by_payment_id(email, payment_id)
    if purchases:
        purchaser = purchases[0]
        pdf = generate_pdf_receipt(
           username=purchaser['username'],
           email=purchaser['email'],
           phone=purchaser['phone'],
           payment_id=payment_id,
           purchases=purchases,
           discount=discount,
           original_price=total_price,
           final_amount=final_amount
        )

        msg = Message(subject="Your Payment Receipt",
                      sender="your-email@example.com",
                      recipients=[purchaser['email']])
        msg.body = f"Hello {purchaser['username']},\n\nPlease find attached your receipt.\n\nThank you!"
        msg.attach("receipt.pdf", "application/pdf", pdf.getvalue())
        mail.send(msg)

    flash("Payment successful! Receipt sent to your email.", "purchase_notification")
    return redirect(url_for('users.purchase_dashboard', course_code=course_code, unique_code=unique_code))

@users_bp.route('/download_receipt/<payment_id>', methods=['GET'])
def download_receipt(payment_id):
    token = request.args.get("token")
    if not token or not verify_download_token(payment_id, token):
        flash("Invalid or expired download link.", "cart_warning")
        return redirect(url_for('users.purchase_dashboard', course_code="none", unique_code="none"))

    email = session.get('email')
    if not email:
        flash("Login required.", "login")
        return redirect(url_for('users.user_login'))

    purchases = user_op.get_purchase_by_payment_id(email, payment_id)
    if not purchases or purchases[0]['email'] != email:
        flash("Access denied.", "cart_warning")
        return redirect(url_for('users.user_login'))

    total_price = sum(float(p['original_price']) for p in purchases)
    discount = float(purchases[0].get('discount_percent', 0))
    discount_amount = round(total_price * discount / 100, 2)
    final_amount = round(total_price - discount_amount, 2)

    pdf = generate_pdf_receipt(
        username=purchases[0]['username'],
        email=email,
        phone=purchases[0]['phone'],
        payment_id=payment_id,
        purchases=purchases,
        discount=discount,
        original_price=total_price,
        final_amount=final_amount
    )
    
    return send_file(BytesIO(pdf.getvalue()), mimetype='application/pdf', as_attachment=True, download_name='receipt.pdf')
