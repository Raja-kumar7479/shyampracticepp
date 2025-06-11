from io import BytesIO
import logging
from mailbox import Message
from flask import  flash, redirect,request, send_file, session, url_for
from users.checkout.user_db import UserOperation
from users.checkout.utils_success import (get_session_user,is_payment_info_valid,
 validate_unique_code,process_cart_purchases,clear_payment_session,verify_hmac_signature)
from users.checkout.user_db import UserOperation
from users.checkout.payment import RAZORPAY_SECRET,razorpay_client

from users.checkout.utils_receipt import generate_pdf_receipt,verify_download_token
from users import users_bp
from flask_mail import Message
from flask_mail import Mail


mail = Mail()
user_op = UserOperation()


@users_bp.route('/payment_success/<course_code>/<unique_code>', methods=['POST'])
def payment_success(course_code, unique_code):
    username, email, phone = get_session_user()
    if not all([username, email, phone]):
        flash("Your session has expired. Please log in and try again.", "login")
        return redirect(url_for('users.user_login'))

    payment_id = request.form.get('razorpay_payment_id')
    order_id = request.form.get('razorpay_order_id')
    signature = request.form.get('razorpay_signature')

    if not all([payment_id, order_id, signature]):
        flash("Payment information is missing. Please do not refresh the page after payment.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    if not verify_hmac_signature(order_id, payment_id, signature, RAZORPAY_SECRET):
        flash("Payment verification failed. Your payment was not successful. Please contact support if money was deducted.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    try:
        payment_details = razorpay_client.payment.fetch(payment_id)
        payment_method = payment_details.get('method', 'N/A')
        payment_status = payment_details.get('status', 'captured')
    except Exception as e:
        logging.error(f"Could not fetch payment details from Razorpay for {payment_id}: {e}")
        flash("Could not confirm payment details. Please contact support.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    if payment_status != 'captured':
        flash(f"Payment status is '{payment_status}'. Only successful payments are processed. Please contact support.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    if not is_payment_info_valid(email, username, payment_id):
        flash("Invalid payment attempt detected.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    if not validate_unique_code(user_op, email, course_code, unique_code):
        flash("Unauthorized access detected! Mismatch in security codes.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    user_cart_key = f'{email}_{course_code}_cart'
    cart_courses = session.get(user_cart_key)
    if not cart_courses:
        flash("Your cart is empty or your session expired after payment. Please check your purchase history or contact support.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    total_price = sum(c['price'] for c in cart_courses)
    discount = session.get('discount', 0)
    discount_amount = round(total_price * discount / 100, 2)
    final_amount = round(total_price - discount_amount, 2)

    purchases_to_add = process_cart_purchases(
        cart_courses=cart_courses,
        email=email,
        username=username,
        phone=phone,
        payment_id=payment_id,
        course_code=course_code,
        amount_paid=final_amount,
        discount_percent=discount,
        payment_mode=payment_method,
        status='Paid',
        original_price=total_price
    )

    if not user_op.add_purchase_transactional(purchases_to_add):
        flash("A critical error occurred while saving your purchase. Please contact support immediately with your payment ID.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    clear_payment_session(user_cart_key)
    for key in ['discount', 'coupon_applied', 'coupon_expiry']:
        session.pop(key, None)

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
            final_amount=final_amount,
            payment_mode=payment_method,
            status='Paid'
        )

        msg = Message(
            subject="Your Payment Receipt from Shyam Practice Paper",
            sender="your-email@example.com",
            recipients=[purchaser['email']]
        )
        msg.body = f"Hello {purchaser['username']},\n\nThank you for your purchase! Your payment was successful.\nPlease find your receipt attached.\n\nThank you for choosing us!"
        msg.attach("receipt.pdf", "application/pdf", pdf.getvalue())

        try:
            mail.send(msg)
            flash("Payment successful! A receipt has been sent to your email.", "purchase_notification")
        except Exception as e:
            logging.error(f"Failed to send receipt email for payment {payment_id}: {e}")
            flash("Payment successful, but we couldn't send the receipt email. You can download it from your dashboard.", "purchase_notification")

   
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

    payment_mode = purchases[0].get('payment_mode', 'N/A')
    status = purchases[0].get('status', 'Pending')
    
    pdf = generate_pdf_receipt(
        username=purchases[0]['username'],
        email=email,
        phone=purchases[0]['phone'],
        payment_id=payment_id,
        purchases=purchases,
        discount=discount,
        original_price=total_price,
        final_amount=final_amount,
        payment_mode=payment_mode,
        status=status
    )

    return send_file(BytesIO(pdf.getvalue()), mimetype='application/pdf', as_attachment=True, download_name='receipt.pdf')
