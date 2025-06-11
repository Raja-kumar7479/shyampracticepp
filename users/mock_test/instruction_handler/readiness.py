from flask import flash,  redirect,  request, session, url_for
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.utils_dashboard import (get_user_session,
                                             )
from users.mock_test.decorator import secure_access_required
from extensions import login_required
from users import users_bp
from extensions import login_required

user_op = UserOperation() 
import logging


user_op = UserOperation()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


@users_bp.route('/process-readiness/<test_id>/<course_code>/<unique_code>', methods=['POST'])
@login_required
@secure_access_required(('unique_code', 'course_code'))
def process_readiness(test_id, course_code, unique_code):
    email, username = get_user_session()
  
    is_checkbox_checked = request.form.get('readiness_checkbox') == 'on'
    if not is_checkbox_checked:
        flash('You must acknowledge the instructions before proceeding.', 'danger')
        return redirect(url_for('users.paper_instruction',
                                test_id=test_id, course_code=course_code,
                                unique_code=unique_code))

    user_op.store_user_test_start(email, test_id, username,
                                  is_checkbox_checked=True, ready_to_begin=True)

    flash('You are now ready to begin the test.', 'success')
  
    return redirect(url_for('users.start_test', test_id=test_id,
                            course_code=course_code, unique_code=unique_code))
