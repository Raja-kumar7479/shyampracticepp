from flask import jsonify, render_template, request, session
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.utils_dashboard import get_user_session
from users.mock_test.decorator import secure_access_required                        
from extensions import login_required
from users import users_bp
from extensions import login_required

user_op = UserOperation() 
import logging


user_op = UserOperation()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

@users_bp.route('/api/record-violation/<test_id>/<course_code>/<unique_code>', methods=['POST'])
@login_required
@secure_access_required(('unique_code', 'course_code'))
def record_violation(test_id, course_code, unique_code):
    from datetime import datetime
    email, username = get_user_session()
    if not email or not username:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401

    data = request.get_json()
    try:
        violation_type = data.get('violationType')
        details = data.get('details')

        session_key = f"violations:{email}:{test_id}"
        violations = session.get(session_key, [])
        violations.append({
            'type': violation_type,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        })
        session[session_key] = violations
        session.modified = True

        if len(violations) >= 5 or violation_type == 'devtools_open':
            user_op.terminate_user_test_log(email, test_id)
            session.pop(session_key, None)
            session[f"terminated:{email}:{test_id}"] = True
            return jsonify({'status': 'terminated'}), 403

        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.exception("Violation recording failed")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@users_bp.route('/test-terminated/<test_id>/<course_code>/<unique_code>/<violation_type>')
@login_required
@secure_access_required(('unique_code', 'course_code'))
def test_terminated(test_id, course_code, unique_code, violation_type):
    return render_template("users/course_materials/mock_test/instruction_handler/termination.html",
                           test_id=test_id,
                           course_code=course_code,
                           unique_code=unique_code,
                           violation_type=violation_type)
