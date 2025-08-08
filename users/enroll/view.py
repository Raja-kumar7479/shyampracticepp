from flask import flash, jsonify, redirect, render_template, request, session, url_for
from users.enroll.user_db import UserOperation
from extensions import user_login_required
import logging
from users import users_bp

user_op = UserOperation()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

@users_bp.route('/my_courses', methods=['GET'])
@user_login_required
def my_courses():
    if 'user_email' not in session:
        flash('Please log in first!', 'course_warning')
        logger.warning('Unauthorized access attempt to my_courses page.')
        return redirect(url_for('users.user_login'))

    email = session['user_email']
    username = session.get('user_username')

    if not username:
        user_data = user_op.get_user_by_email(email)
        if user_data:
            user_username = user_data['user_username']
            session['user_username'] = user_username
            logger.info(f"Username retrieved from DB for user {email}")
        else:
            flash('User data not found. Please log in again.', 'course_error')
            logger.error(f"User data not found for email: {email}")
            return redirect(url_for('users.user_login'))

    enrolled_courses_data = user_op.get_enrolled_courses(email)
    logger.info(f"User {email} is viewing their enrolled courses.")

    enrolled_courses = []
    for item in enrolled_courses_data:
        course_code = item['code']
        unique_code = item['unique_code']
        course_details = user_op.get_course_details(course_code)
        if course_details:
            course_details['unique_code'] = unique_code
            enrolled_courses.append(course_details)

    return render_template('users/enroll/enrolled_courses.html',
                           enrolled_courses=enrolled_courses,
                           email=email,
                           username=username)

@users_bp.route('/course', methods=['GET'])
def course_view():
    if 'user_email' not in session:
        flash('Please log in first!', 'course_warning')
        logger.warning('Unauthorized access attempt to course_view page.')
        return redirect(url_for('users.user_login'))

    email = session['user_email']
    username = session.get('user_username')

    if not username:
        user_data = user_op.get_user_by_email(email)
        if user_data:
            username = user_data['user_username']
            session['user_username'] = username
            logger.info(f"Username retrieved from DB for user {email} on course view.")
        else:
            flash('User data not found. Please log in again.', 'course_error')
            logger.error(f"User data not found for email: {email}")
            return redirect(url_for('users.user_login'))

    courses = user_op.get_all_courses()
    logger.info(f"User {email} is viewing all available courses.")

    enrollments = {
        course['code']: user_op.check_enrollment(email, course['code'])
        for course in courses
    }

    return render_template(
        'users/enroll/available_courses.html',
        courses=courses,
        enrollments=enrollments,
        user_email=email,
        username=username
    )
