from flask import flash,redirect, render_template, session, url_for
from users.purchase.user_db import UserOperation
from users.purchase.user_db import UserOperation
from users.purchase.utils_receipt import generate_download_token
from users import users_bp
from flask_mail import Mail

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

    # Generate download links and extract phone number
    for purchase in purchases:
        purchase['download_link'] = url_for(
            'users.download_receipt',
            payment_id=purchase['payment_id'],
            token=generate_download_token(purchase['payment_id'])
        )

    # Get phone from the first purchase (assuming same phone used for all)
    phone = purchases[0]['phone'] if 'phone' in purchases[0] else None

    return render_template(
        'users/purchase/purchase.html',
        purchases=purchases,
        course_code=course_code,
        unique_code=unique_code,
        phone=phone
    )
