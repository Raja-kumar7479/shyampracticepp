from flask import flash, jsonify,redirect, render_template, request, session, url_for
from users.checkout.user_db import UserOperation
from users.checkout.user_db import UserOperation
from users.checkout.utils_receipt import generate_download_token
from users import users_bp
from flask_mail import Mail
from collections import defaultdict

mail = Mail()
user_op = UserOperation()

@users_bp.route('/purchase/<course_code>/<unique_code>', methods=['GET'])
def purchase_dashboard(course_code, unique_code):
    username = session.get('username')
    email = session.get('email')

    if not all([username, email]):
        flash("Please login to access purchases.", "login")
        return redirect(url_for('users.user_login'))

    purchases = user_op.get_all_purchases(email)
    if not purchases:
        flash("No purchases found.", "cart_warning")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    # Generate download links
    for purchase in purchases:
        purchase['download_link'] = url_for(
            'users.download_receipt',
            payment_id=purchase['payment_id'],
            token=generate_download_token(purchase['payment_id'])
        )

    grouped_purchases = defaultdict(list)
    for p in purchases:
        grouped_purchases[p['section']].append(p)

    phone = purchases[0]['phone'] if 'phone' in purchases[0] else None

    return render_template(
        'users/purchase/purchase.html',
        grouped_purchases=grouped_purchases,
        course_code=course_code,
        unique_code=unique_code,
        phone=phone
    )

@users_bp.route('/open/notes_1', methods=['GET', 'POST'])
def open_notes_1():
    if request.method == 'POST':
        data = request.get_json()
        return jsonify({"message": "POST received for NOTES_1", "data": data})
    else:
        return jsonify({"message": "Welcome to NOTES_1 section via GET"})
