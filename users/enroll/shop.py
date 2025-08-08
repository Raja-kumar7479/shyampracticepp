import logging
from flask import flash, jsonify, redirect, render_template, request, session, url_for
from users.enroll.user_db import UserOperation
from users import users_bp

user_op = UserOperation()
logger = logging.getLogger(__name__)

@users_bp.route('/course_shop/<course_code>/<unique_code>')
def course_shop(course_code, unique_code):
    email = session.get('user_email')
    username = session.get('user_username')

    if not email:
        logger.warning("Unauthorized access attempt to course shop.")
        return redirect(url_for('users.user_login'))

    stored_code = user_op.get_user_unique_code(email, course_code)

    if stored_code != unique_code:
        flash("Access Denied! Invalid or unauthorized access.", "dashboard_warning")
        logger.warning(f"Access denied for user {email} to course {course_code} due to invalid unique code.")
        return redirect(url_for('users.course_view'))

    all_paid_courses = user_op.get_paid_courses_by_code(course_code)
    
    purchased_courses = []
    available_courses = []

    for course in all_paid_courses:
        is_purchased = user_op.is_course_purchased_securely(
            email,
            course_code,
            course['title'],
            course['subtitle']
        )
        if is_purchased:
            purchased_courses.append(course)
        else:
            available_courses.append(course)
    
    logger.info(f"User {email} accessed course shop for {course_code}.")

    return render_template(
        'users/dashboard/shopping.html',
        purchased_courses=purchased_courses,
        available_courses=available_courses,
        email=email,
        username=username,
        course_code=course_code.upper(),
        unique_code=unique_code
    )
