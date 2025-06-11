from flask import flash,redirect, render_template, request, session, url_for
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.utils_dashboard import (
                                             get_user_session,
                                             redirect_if_test_not_found)
from users.mock_test.decorator import secure_access_required
from users.mock_test.utils_token import generate_test_token
from extensions import login_required
from users import users_bp
from extensions import login_required

user_op = UserOperation() 

import logging


user_op = UserOperation()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


@users_bp.route('/test-login/<test_id>/<course_code>/<unique_code>', methods=['GET', 'POST'])
@login_required
@secure_access_required(('unique_code', 'course_code'))
def test_login(test_id, course_code, unique_code):
    email, username = get_user_session()
    terminated = request.args.get('terminated')

    if terminated:
        flash('Test terminated due to multiple violations.', 'danger')

    test_details = user_op.get_test_details(test_id)
    if not test_details:
        flash('Test not found.', 'danger')
        return redirect(url_for('users.open_mock_test', course_code=course_code, unique_code=unique_code))

    test_key_from_db = test_details.get('test_key')
    test_code_from_db = test_details.get('test_code')

    if request.method == 'POST':
        test_key_submitted = request.form.get('test_key')
        test_code_submitted = request.form.get('test_code')

        if test_key_submitted != test_key_from_db or test_code_submitted != test_code_from_db:
             flash('Invalid Test Key or Test Code!', 'danger')
             return redirect(url_for('users.test_login', test_id=test_id, course_code=course_code, unique_code=unique_code))


        if user_op.check_test_already_taken(email, test_id):
            flash('You have already completed this test.', 'warning')
            return redirect(url_for('users.open_mock_test', course_code=course_code, unique_code=unique_code))

        user_op.store_user_test_start(email, test_id, username)

        session['proceed_test'] = True
        session['test_popup_initiated'] = True
        return redirect(url_for('users.test_login', test_id=test_id, course_code=course_code, unique_code=unique_code))

    test = user_op.get_test_details(test_id)
    redir = redirect_if_test_not_found(test, 'open_mock_test', test_id, course_code, unique_code)
    if redir:
        return redir

    proceed = session.pop('proceed_test', False)

    user_test_status = user_op.get_test_status_for_user(email, test_id)

    return render_template('users/course_materials/mock_test/test_handler/test_login.html',
                            test=test, test_id=test_id, course_code=course_code,
                            unique_code=unique_code, username=username, proceed=proceed,
                            user_test_status=user_test_status,
                            test_key_prefilled=test_key_from_db,  
                            test_code_prefilled=test_code_from_db)