from flask import flash, jsonify, redirect, render_template, request, session, url_for
from users.enroll.user_db import UserOperation
from extensions import user_login_required
import logging
from users import users_bp

user_op = UserOperation()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

@users_bp.route('/dashboard/<course_code>/<unique_code>')
@user_login_required
def course_dashboard(course_code, unique_code):
    email = session.get('user_email')
    username = session.get('user_username')
    
    if not all([email, username]):
        flash("You must be logged in to access the dashboard.", "dashboard_warning")
        logger.warning("Unauthorized access to course dashboard: user not logged in.")
        return redirect(url_for('users.user_login'))

    stored_code = user_op.get_user_unique_code(email, course_code)
    if stored_code != unique_code:
        flash("Access Denied! Invalid or unauthorized access.", "dashboard_warning")
        logger.warning(f"Access denied for user {email} to course {course_code} due to invalid unique code.")
        return redirect(url_for('users.course_view'))

    course_details = user_op.get_course_details(course_code)
    course_name = course_details['name'] if course_details else course_code
    
    logger.info(f"User {email} accessing dashboard for course {course_code}.")

    available_practice_sections = user_op.get_practice_sections_for_code(course_code)

    question_sections = {}
    if 'Topic-wise' in available_practice_sections:
        question_sections['Topic-wise'] = url_for('users.browse_by_topic', unique_code=unique_code, paper_code=course_code)
    if 'Subject-wise' in available_practice_sections:
        question_sections['Subject-wise'] = url_for('users.browse_by_subject', unique_code=unique_code, paper_code=course_code)
    if 'Year-wise' in available_practice_sections:
        question_sections['Year-wise'] = url_for('users.browse_by_year', unique_code=unique_code, paper_code=course_code)

    courses = user_op.get_free_courses_by_code(course_code)
    sections = user_op.get_sections_by_code(course_code)

    return render_template(
        "users/dashboard/materials.html",
        email=email,
        username=username,
        course_code=course_code.upper(),
        course_name=course_name,
        unique_code=unique_code,
        question_sections=question_sections,
        courses=courses,
        sections=sections
    )
