import logging
from flask import  session, url_for, redirect, render_template, current_app
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.handler_db.result_handler_db import ResultHandler
from extensions import login_required
from users.mock_test.decorator import secure_access_required
from users.mock_test.utils_dashboard import get_user_session

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

from users import users_bp
user_op = UserOperation()

result_handler = ResultHandler()

@users_bp.route('/test_overview/<test_id>/<course_code>/<unique_code>')
@login_required
@secure_access_required(('unique_code', 'course_code'))
def test_overview(test_id, course_code, unique_code):
    user_session = get_user_session()

    user_email, username = user_session

    overview_data = result_handler.get_test_summary_details(test_id, user_email)
    if not overview_data:
        current_app.logger.error(f"Could not retrieve overview data for test_id: {test_id}, email: {user_email}")
        return render_template('error.html', message="Test overview data not found."), 404

    overall = overview_data['overall']
    counts = overview_data['counts']

    test_basic_details = user_op.get_test_basic_details(test_id)
    total_duration_minutes = test_basic_details.get('total_duration_minutes', 'N/A')

    overview_table_data_for_template = {
        'subject_title': overall.get('subject_title', 'N/A'), 
        'subject_subtitle': overall.get('subject_subtitle', 'N/A'),
        'net_score': overall.get('net_score', 0.0),
        'total_marks': overall.get('total_marks', 0.0),
        'percentage': overall.get('percentage', 0.0),
        'total_time_taken_seconds': overall.get('total_time_taken_seconds', 0),
        'ranker': overall.get('ranker', 'N/A'),
        'total_participants': overall.get('total_participants', 'N/A'),

        'total_questions': counts.get('all', 0),
        'correct_questions_count': counts.get('correct', 0),
        'incorrect_questions_count': counts.get('incorrect', 0),
        'skipped_questions_count': counts.get('skipped', 0),
        'total_duration_minutes': total_duration_minutes,
    }

    return render_template(
        'users/course_materials/mock_test/result_handler/test_overview.html',
        overview_table_data=overview_table_data_for_template,
        test_id=test_id,
        course_code=course_code,
        unique_code=unique_code,
        username=username  
    )

@users_bp.route('/test_summary/<test_id>/<course_code>/<unique_code>')
@login_required
@secure_access_required(('unique_code', 'course_code'))
def test_summary(test_id, course_code, unique_code):
    user_session = get_user_session()
    
    user_email, username = user_session

    test_summary_data = result_handler.get_test_summary_details(test_id, user_email)
    if not test_summary_data:
        logger.error(f"No test summary found for test_id: {test_id}, email: {user_email}")

    return render_template(
        'users/course_materials/mock_test/result_handler/test_result.html',
        summary=test_summary_data,
        course_code=course_code,
        unique_code=unique_code,
        username=username  
    )
