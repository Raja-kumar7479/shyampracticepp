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

def _process_tests_for_new_badge(tests):
    processed_tests = []
    three_days_ago = datetime.datetime.now() - datetime.timedelta(days=3)
    for test in tests:
        last_update_time = test.get('updated_at')
        if last_update_time:
            test['is_newly_added'] = last_update_time > three_days_ago
        else:
            test['is_newly_added'] = False
        processed_tests.append(test)
    return processed_tests

def _prepare_test_data(all_tests_basic_info, email, section_id):
    pending_tests = []
    completed_tests_details = []
    course_name = ''
    stream = ''

    completed_tests_from_db = user_op.get_completed_tests_for_user(email, section_id)
    completed_test_keys = {test['test_key'] for test in completed_tests_from_db}

    completed_tests_map = {test['test_key']: test for test in completed_tests_from_db}

    if all_tests_basic_info:
        course_name = all_tests_basic_info[0].get('course_name', '')
        stream = all_tests_basic_info[0].get('stream', '')

        for test_basic in all_tests_basic_info:
            test_key = test_basic.get('test_key')
            
            if test_key in completed_test_keys:
                completed_test_entry = completed_tests_map.get(test_key)
                if completed_test_entry:
                    completed_tests_details.append(completed_test_entry)
            else:
                pending_tests.append(test_basic)
    
    display_tests = _process_tests_for_new_badge(pending_tests)
    
    return {
        'display_tests': display_tests,
        'completed_tests_details': completed_tests_details,
        'course_name': course_name,
        'stream': stream
    }

def prepare_mock_test_data_free(course_code, email, section_id):
    all_tests_basic_info = content_op.get_mock_tests_free(section_id, course_code, email)
    return _prepare_test_data(all_tests_basic_info, email, section_id)

def prepare_mock_test_data_paid(course_code, email, section_id):
    all_tests_basic_info = content_op.get_mock_tests_paid(section_id, course_code, email)
    return _prepare_test_data(all_tests_basic_info, email, section_id)

