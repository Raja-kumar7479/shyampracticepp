from flask import session, redirect, url_for, flash
import logging
from users.mock_test.handler_db.user_db import UserOperation

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

user_op = UserOperation()

def get_user_session():
    email = session.get('email')
    username = session.get('username')

    if not email or not username:
        logger.warning(f"USER_SESSION: Missing email/username. Email: {email}, Username: {username}, IP: {session.get('remote_addr')}")
        flash("Session expired or invalid. Please log in again.", "warning")
        return redirect(url_for('users.user_login'))

    logger.info(f"USER_SESSION: Session valid. Email: {email}, Username: {username}")
    return email, username

def redirect_if_test_not_found(test, route_name, test_id, course_code, unique_code):
    if not test:
        logger.warning(f"TEST_ACCESS: Test not found. Test ID: {test_id}, Course: {course_code}, Code: {unique_code}")
        flash('Test details not found.', 'danger')
        return redirect(url_for(f'users.{route_name}',
                                test_id=test_id,
                                course_code=course_code,
                                unique_code=unique_code))
    logger.info(f"TEST_ACCESS: Test found. Test ID: {test_id}")
    return None

def format_section_count(sections):
    num_sections = len(sections)
    section_text = f"{num_sections} section{'s' if num_sections > 1 else ''}"
    logger.debug(f"SECTION_COUNT: Formatted section count: {section_text}")
    return section_text