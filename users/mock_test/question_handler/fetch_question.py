import json
import traceback
from flask import flash, jsonify, redirect, render_template, request, session, url_for
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



@users_bp.route('/fetch-questions/<test_id>/<course_code>/<unique_code>', methods=['GET'])
@login_required
@secure_access_required(('unique_code', 'course_code'))
def fetch_questions(test_id, course_code, unique_code):
    email, username = get_user_session()
    logger.info(f"Fetching questions for user {email}, test {test_id}")

    all_questions = user_op.get_all_test_questions(test_id)
    if not all_questions:
        return jsonify({"error": "No questions available for this test."}), 404

    processed_questions = []
    for q_idx, q in enumerate(all_questions):
        processed_questions.append({
            "id": q.get('id'),
            "test_id": q.get('test_id'),
            "section_id": q.get('section_id'),
            "section_name": q.get('section_name'),
            "question_number_in_section": q.get('question_number'),
            "overall_question_index": q_idx,
            "question_type": q.get('question_type'),
            "question_text": q.get('question_text'),
            "question_image": q.get('question_image'),
            "options": {
                "a": q.get('option_a'),
                "b": q.get('option_b'),
                "c": q.get('option_c'),
                "d": q.get('option_d'),
            },
            "correct_marks": q.get('correct_marks'),
            "negative_marks": q.get('negative_marks'),
        })

    return jsonify(processed_questions)

