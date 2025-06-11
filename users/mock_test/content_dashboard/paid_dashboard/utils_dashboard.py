import datetime
from users.mock_test.content_dashboard.content_db import ContentOperation
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.handler_db.result_handler_db import ResultHandler

import logging

user_op = UserOperation()
content_op = ContentOperation()

result_handler = ResultHandler()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def prepare_mock_test_data_paid(course_code, email):
    all_tests_basic_info = content_op.get_mock_tests_paid(course_code, email)
    display_tests = []
    completed_tests_details = []
    course_name = ''
    stream = ''

    if all_tests_basic_info:
        course_name = all_tests_basic_info[0].get('course_name', '')
        stream = all_tests_basic_info[0].get('stream', '')

        for test_basic in all_tests_basic_info:
            test_status = test_basic.get('user_test_status')

            if test_status == 'completed':
                test_id = test_basic.get('test_id')
                if test_id:
                    summary_data = result_handler.get_test_summary_details(test_id, email)
                    if summary_data and summary_data.get('overall'):
                        overall = summary_data['overall']
                        submission_timestamp = overall.get('submission_timestamp')
                        if isinstance(submission_timestamp, str):
                            try:
                                submission_timestamp = datetime.datetime.strptime(submission_timestamp, '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                logger.error(f"Failed to parse submission_timestamp: {submission_timestamp}")
                                submission_timestamp = None
                        
                        completed_test_entry = {
                            'test_id': test_id,
                            'test_number': test_basic.get('test_number'),
                            'subject_title': test_basic.get('subject_title'),
                            'subject_subtitle': test_basic.get('subject_subtitle'),
                            'submission_timestamp': submission_timestamp,
                            'net_score': overall.get('net_score', 0.0),
                            'percentage': overall.get('percentage', 0.0),
                            'label': test_basic.get('label')  # <-- Added this line
                        }
                        completed_tests_details.append(completed_test_entry)
                    else:
                        logger.warning(f"No detailed summary data for completed test_id: {test_id} for user: {email}")
                else:
                    logger.warning(f"Completed test found without test_id: {test_basic}")
            else:
                # Add the test to display if it's not completed
                display_tests.append(test_basic)

    return {
        'display_tests': display_tests,
        'completed_tests_details': completed_tests_details,
        'course_name': course_name,
        'stream': stream
    }