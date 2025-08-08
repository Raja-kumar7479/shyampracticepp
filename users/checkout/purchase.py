import logging
from venv import logger
from flask import flash, jsonify,redirect, render_template, request, session, url_for
from users.checkout.user_db import UserOperation
from users.checkout.user_db import UserOperation
from users.checkout.utils_receipt import generate_download_token
from extensions import user_login_required
from users import users_bp
from flask_mail import Mail
from collections import defaultdict

mail = Mail()
user_op = UserOperation()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@users_bp.route('/purchase/<course_code>/<unique_code>', methods=['GET'])
@user_login_required
def purchase_dashboard(course_code, unique_code):
    user_username = session.get('user_username')
    user_email = session.get('user_email')
    
    if not all([user_username, user_email]):
        flash("Please login to access purchases.", "login_warning")
        logger.warning("Unauthorized access to purchase dashboard - user not logged in.")
        return redirect(url_for('users.user_login'))

    purchases = user_op.get_all_purchases(user_email)
    if not purchases:
        flash("No purchases found.", "cart_info")
        logger.info(f"No purchases found for user {user_email}.")
        return redirect(url_for('users.course_shop', course_code=course_code, unique_code=unique_code))

    for purchase in purchases:
        purchase['download_link'] = url_for(
            'users.download_receipt',
            payment_id=purchase['payment_id'],
            token=generate_download_token(purchase['payment_id'])
        )

    grouped_purchases = defaultdict(list)
    for p in purchases:
        grouped_purchases[p['section']].append(p)
    
    initials = "".join([name[0] for name in user_username.split()]).upper()
    logger.info(f"Displaying purchase dashboard for user {user_email}.")

    return render_template(
        'users/purchase/purchase.html',
        grouped_purchases=grouped_purchases,
        course_code=course_code,
        unique_code=unique_code,
        username=user_username,
        initials=initials
    )
