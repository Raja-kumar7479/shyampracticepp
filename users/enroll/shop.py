
from flask import flash, jsonify, redirect, render_template, request, session, url_for
import mysql
from config import Config
from users.enroll.user_db import UserOperation

from users import users_bp
user_op =UserOperation()


@users_bp.route('/course_shop/<course_code>/<unique_code>')
def course_shop(course_code, unique_code):
    if 'email' not in session:
        return redirect(url_for('users.user_login'))

    email = session['email']
    stored_code = user_op.get_user_unique_code(email, course_code)

    if stored_code != unique_code:
        flash("Access Denied! Invalid or unauthorized access.", "dashboard_alerts")
        return redirect(url_for('users.course_view'))

    courses = user_op.get_courses_by_code(course_code)
    enrolled_courses = user_op.get_enrolled_courses(email)

    purchase_status_map = {}
    purchase_code_map = {}

    for course in courses:
        check = user_op.is_course_purchased_securely(
            email,
            course_code,
            course['title'],
            course['subtitle']
        )
        key = f"{course['title']}|{course['subtitle']}"
        purchase_status_map[key] = check is not None
        purchase_code_map[key] = check['purchase_code'] if check else None

    return render_template(
        'users/dashboard/shop.html',
        courses=courses,
        email=email,
        
        enrolled_courses=enrolled_courses,
        purchase_status_map=purchase_status_map,
        purchase_code_map=purchase_code_map,
        course_code=course_code.upper(),
        unique_code=unique_code
    )
