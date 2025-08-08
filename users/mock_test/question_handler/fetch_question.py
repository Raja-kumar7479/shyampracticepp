from flask import jsonify
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.utils_dashboard import get_user_session
from users.mock_test.decorator import secure_access_required
from extensions import user_login_required
from users import users_bp

user_op = UserOperation()

def clean_html(html_content):
    if not html_content:
        return html_content
    html_content = html_content.strip()
    if html_content.startswith('<p>') and html_content.endswith('</p>'):
        inner_content = html_content[3:-4].strip()
        if '<p>' not in inner_content:
            return inner_content
    return html_content

@users_bp.route('/fetch-questions/<test_key>/<course_code>/<unique_code>', methods=['GET'])
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def fetch_questions(test_key, course_code, unique_code):
    all_questions = user_op.get_all_test_questions(test_key)
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
            "options": {
                "a": clean_html(q.get('option_a')),
                "b": clean_html(q.get('option_b')),
                "c": clean_html(q.get('option_c')),
                "d": clean_html(q.get('option_d')),
            },
            "correct_marks": q.get('correct_marks'),
            "negative_marks": q.get('negative_marks'),
        })
    return jsonify(processed_questions)
