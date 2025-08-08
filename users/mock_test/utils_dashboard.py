from functools import wraps
from flask import session, redirect, url_for, flash, request
import logging
import time
from users.mock_test.handler_db.user_db import UserOperation

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

user_op = UserOperation()

def get_user_session():
    user_email = session.get('user_email')
    user_username = session.get('user_username')

    if not user_email or not user_username:
        logger.warning(f"USER_SESSION: Missing user_email/user_username. Email: {user_email}, Username: {user_username}, IP: {request.remote_addr}")
        flash("Session expired or invalid. Please log in again.", "warning")
        return redirect(url_for('users.user_login'))

    logger.info(f"USER_SESSION: Session valid. Email: {user_email}, Username: {user_username}")
    return user_email, user_username

def redirect_if_test_not_found(test, endpoint, **kwargs):
    if not test:
        logger.warning(f"TEST_ACCESS: Test not found with provided details.")
        flash('Test details not found.', 'danger')
        return redirect(url_for(endpoint, **kwargs))
    logger.info(f"TEST_ACCESS: Test found.")
    return None

def format_section_count(sections):
    num_sections = len(sections)
    section_text = f"{num_sections} section{'s' if num_sections > 1 else ''}"
    logger.debug(f"SECTION_COUNT: Formatted section count: {section_text}")
    return section_text
