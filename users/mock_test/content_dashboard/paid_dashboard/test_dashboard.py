from flask import abort, redirect, render_template, request, url_for
import datetime
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.content_dashboard.content_db import ContentOperation
from users.mock_test.utils_dashboard import get_user_session
from users.mock_test.handler_db.result_handler_db import ResultHandler
from users.mock_test.content_dashboard.paid_dashboard.utils_dashboard import prepare_mock_test_data_paid
from users.mock_test.decorator import secure_access_required
from extensions import login_required
from users import users_bp
import logging

user_op = UserOperation()
content_op = ContentOperation()

result_handler = ResultHandler()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

@users_bp.route('/open/mock-test-14/<course_code>/<unique_code>')
@login_required
@secure_access_required(('unique_code', 'course_code'))
def open_mock_test_14(course_code, unique_code):
    email, username = get_user_session()
    data = prepare_mock_test_data_paid(course_code, email)

    return render_template(
        'users/course_materials/mock_test/content_dashboard/test_dashboard/test_dashboard.html',
        tests=data['display_tests'],
        completed_tests=data['completed_tests_details'],
        email=email,
        username=username,
        course_code=course_code,
        course_name=data['course_name'],
        stream=data['stream'],
        unique_code=unique_code,
        dashboard_type='paid'  
    )