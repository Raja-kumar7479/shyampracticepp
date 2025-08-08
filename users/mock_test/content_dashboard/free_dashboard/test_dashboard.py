from flask import abort, redirect, render_template, request, url_for
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.content_dashboard.content_db import ContentOperation
from users.mock_test.utils_dashboard import get_user_session
from users.mock_test.content_dashboard.free_dashboard.utils_dashboard import prepare_mock_test_data_free, prepare_mock_test_data_paid
from users.mock_test.decorator import secure_access_required
from extensions import user_login_required
from users import users_bp
import logging

user_op = UserOperation()
content_op = ContentOperation()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

@users_bp.route('/open/mock_test/<section_id>/<course_code>/<unique_code>')
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def open_mock_test_section(section_id, course_code, unique_code):
    email, username = get_user_session()

    section_label = content_op.get_section_label(section_id)

    if not section_label:
        abort(404)

    data = {}
    dashboard_type = ''

    if section_label == 'Free':
        data = prepare_mock_test_data_free(course_code, email, section_id)
        dashboard_type = 'free'
    elif section_label == 'Paid':
        
        data = prepare_mock_test_data_paid(course_code, email, section_id)
        dashboard_type = 'paid'
    else:
        abort(400)

    return render_template(
        'users/mock_test/content_dashboard/test_dashboard/test_dashboard.html',
        tests=data.get('display_tests', []),
        completed_tests=data.get('completed_tests_details', []),
        email=email,
        username=username,
        course_code=course_code,
        course_name=data.get('course_name', ''),
        stream=data.get('stream', ''),
        unique_code=unique_code,
        dashboard_type=dashboard_type
    )
