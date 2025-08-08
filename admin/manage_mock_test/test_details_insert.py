import csv
from io import StringIO
import logging
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, request, jsonify, session
from admin.manage_mock_test.test_details_db import UserOperation
from extensions import admin_login_required
from admin import admin_bp
import mysql.connector

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='app.log')

user_op = UserOperation()
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _convert_negative_marks(negative_marks_str):
    if not negative_marks_str: return 0.0
    try:
        if isinstance(negative_marks_str, (int, float)): return float(negative_marks_str)
        negative_marks_str = str(negative_marks_str).strip()
        if '/' in negative_marks_str:
            num, den = map(float, negative_marks_str.split('/'))
            if den == 0: raise ValueError("Denominator cannot be zero.")
            return num / den
        return float(negative_marks_str)
    except (ValueError, TypeError):
        raise ValueError(f'Invalid format for Negative Marks: "{negative_marks_str}". Use a number or a fraction like "1/4".')

@admin_bp.route('/api/upload-quill-image', methods=['POST'])
@admin_login_required
def upload_quill_image():
    if 'image' not in request.files:
        return jsonify({'message': 'No image file found in the request.'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'message': 'No selected file.'}), 400
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            url_path = os.path.join('uploads', 'images', unique_filename).replace('\\', '/')
            return jsonify({'url': f'/static/{url_path}'})
        except Exception as e:
            logger.error(f"Error saving uploaded image: {e}")
            return jsonify({'message': f'An error occurred while saving the image: {str(e)}'}), 500
    else:
        return jsonify({'message': 'Invalid file type. Allowed types are png, jpg, jpeg, gif.'}), 400

@admin_bp.route('/manage-tests', methods=['GET'])
@admin_login_required
def manage_tests():
    admin_email = session.get('admin_email', 'UnknownAdmin')
    logger.info(f"[{admin_email}] Accessed /manage-tests")
    return render_template('admin/manage_mock_test/test_details_insert.html')

@admin_bp.route('/api/content-for-tests', methods=['GET'])
@admin_login_required
def get_content_for_tests_api():
    admin_email = session.get('admin_email', 'UnknownAdmin')
    try:
        logger.info(f"[{admin_email}] Requested test content")
        content = user_op.get_content_for_tests()
        return jsonify(content)
    except Exception as e:
        logger.exception(f"[{admin_email}] Error in get_content_for_tests_api")
        return jsonify({'message': 'An error occurred: ' + str(e)}), 500

@admin_bp.route('/api/test-descriptions/<test_id>', methods=['GET'])
@admin_login_required
def get_test_descriptions_api(test_id):
    admin_email = session.get('admin_email', 'UnknownAdmin')
    try:
        logger.info(f"[{admin_email}] Fetching test descriptions for test_id={test_id}")
        descriptions = user_op.get_test_descriptions_by_test_id(test_id)
        return jsonify(descriptions)
    except Exception as e:
        logger.exception(f"[{admin_email}] Failed fetching test descriptions for test_id={test_id}")
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/api/test-descriptions/add', methods=['POST'])
@admin_login_required
def add_test_description_api():
    admin_email = session.get('admin_email', 'UnknownAdmin')
    data = request.get_json()
    required = ['test_id', 'test_key', 'subject_title', 'total_questions', 'total_marks', 'total_duration_minutes']
    if not all(data.get(field) for field in required):
        logger.warning(f"[{admin_email}] Missing fields in test description add: {data}")
        return jsonify({'message': 'Missing required fields.'}), 400
    try:
        user_op.insert_test_description(data)
        logger.info(f"[{admin_email}] Test description added: {data}")
        return jsonify({'message': 'Test Description added successfully!'}), 201
    except Exception as e:
        logger.exception(f"[{admin_email}] Failed to add test description")
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/api/test-descriptions/update/<int:id>', methods=['PUT'])
@admin_login_required
def update_test_description_api(id):
    admin_email = session.get('admin_email', 'UnknownAdmin')
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided.'}), 400
    try:
        for field, value in data.items():
            user_op.update_test_description_field(id, field, value)
        logger.info(f"[{admin_email}] Updated test description ID {id}: {data}")
        return jsonify({'message': 'Test Description updated successfully!'})
    except Exception as e:
        logger.exception(f"[{admin_email}] Error updating test description ID {id}")
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/api/test-descriptions/delete/<int:id>', methods=['DELETE'])
@admin_login_required
def delete_test_description_api(id):
    admin_email = session.get('admin_email', 'UnknownAdmin')
    try:
        user_op.delete_test_description(id)
        logger.info(f"[{admin_email}] Deleted test description ID {id}")
        return jsonify({'message': 'Test Description and all its questions deleted successfully!'})
    except Exception as e:
        logger.exception(f"[{admin_email}] Error deleting test description ID {id}")
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/api/questions/<int:description_id>', methods=['GET'])
@admin_login_required
def get_questions_api(description_id):
    admin_email = session.get('admin_email', 'UnknownAdmin')
    try:
        section_id = request.args.get('section_id')
        if not section_id:
            return jsonify({'message': 'Section ID is required'}), 400
        desc = user_op.get_test_description_by_id(description_id)
        if not desc:
            return jsonify({'message': 'Test Description not found'}), 404
        questions = user_op.get_questions_for_description_section(description_id, section_id)
        current_count = user_op.get_question_count_for_description(description_id)
        max_allowed = desc.get('total_questions', 0)
        logger.info(f"[{admin_email}] Retrieved questions for description_id={description_id}, section_id={section_id}")
        return jsonify({
            'questions': questions,
            'current_count': current_count,
            'max_allowed': max_allowed
        })
    except Exception as e:
        logger.exception(f"[{admin_email}] Failed to fetch questions for description_id={description_id}")
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/api/test-questions/add', methods=['POST'])
@admin_login_required
def add_test_question_api():
    admin_email = session.get('admin_email', 'UnknownAdmin')
    data = request.get_json()
    required = ['test_id', 'test_key', 'test_description_id', 'section_id', 'section_name',
                'question_type', 'question_text', 'correct_option', 'correct_marks']
    if not all(data.get(field) is not None for field in required):
        logger.warning(f"[{admin_email}] Missing required fields in test question add.")
        return jsonify({'message': 'Missing required fields.'}), 400
    try:
        data['negative_marks'] = _convert_negative_marks(data.get('negative_marks'))
        data['correct_marks'] = float(data['correct_marks'])
        last_q_num = user_op.get_max_question_number_in_section(data['test_description_id'], data['section_id'])
        data['question_number'] = last_q_num + 1
        user_op.insert_test_question(data)
        logger.info(f"[{admin_email}] Added new test question: {data}")
        return jsonify({'message': 'Question added successfully!'}), 201
    except ValueError as e:
        logger.warning(f"[{admin_email}] Invalid negative marks: {e}")
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        logger.exception(f"[{admin_email}] Failed to add test question")
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/api/test-questions/update/<int:id>', methods=['PUT'])
@admin_login_required
def update_test_question_api(id):
    admin_email = session.get('admin_email', 'UnknownAdmin')
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided.'}), 400
    try:
        if 'negative_marks' in data:
            data['negative_marks'] = _convert_negative_marks(data['negative_marks'])
        for field, value in data.items():
            user_op.update_test_question_field(id, field, value)
        logger.info(f"[{admin_email}] Updated test question ID {id}: {data}")
        return jsonify({'message': 'Question updated successfully!'})
    except ValueError as e:
        logger.warning(f"[{admin_email}] Validation error: {e}")
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        logger.exception(f"[{admin_email}] Failed to update test question ID {id}")
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/api/test-questions/delete/<int:id>', methods=['DELETE'])
@admin_login_required
def delete_test_question_api(id):
    admin_email = session.get('admin_email', 'UnknownAdmin')
    try:
        user_op.delete_test_question(id)
        logger.info(f"[{admin_email}] Deleted test question ID {id}")
        return jsonify({'message': 'Question deleted successfully!'})
    except Exception as e:
        logger.exception(f"[{admin_email}] Failed to delete test question ID {id}")
        return jsonify({'message': str(e)}), 500

@admin_bp.route('/api/test-questions/upload-csv', methods=['POST'])
@admin_login_required
def upload_questions_csv():
    if 'csv_file' not in request.files: return jsonify({"message": "No CSV file provided"}), 400
    csv_file = request.files['csv_file']
    if not csv_file or not csv_file.filename.lower().endswith('.csv'):
        return jsonify({"message": "Invalid file. Please upload a CSV."}), 400
    test_id = request.form.get('test_id')
    test_key = request.form.get('test_key')
    description_id = request.form.get('test_description_id')
    section_id = request.form.get('section_id')
    section_name = request.form.get('section_name')
    if not all([test_id, test_key, description_id, section_id, section_name]):
        return jsonify({"message": "Missing test/section identifiers."}), 400
    try:
        stream = StringIO(csv_file.stream.read().decode("UTF-8"))
        reader = csv.DictReader(stream)
        inserted, failed, errors = 0, 0, []
        last_q_num = user_op.get_max_question_number_in_section(description_id, section_id)
        for i, row in enumerate(reader, 2):
            if not any(row.values()): continue
            try:
                question_data = {
                    'test_id': test_id,
                    'test_key': test_key,
                    'test_description_id': description_id,
                    'section_id': section_id,
                    'section_name': section_name,
                    'question_number': last_q_num + 1,
                    'question_type': row.get('question_type', '').strip(),
                    'question_text': row.get('question_text', '').strip(),
                    'option_a': row.get('option_a', '').strip() or None,
                    'option_b': row.get('option_b', '').strip() or None,
                    'option_c': row.get('option_c', '').strip() or None,
                    'option_d': row.get('option_d', '').strip() or None,
                    'correct_option': row.get('correct_option', '').strip(),
                    'correct_marks': float(row.get('correct_marks', '0').strip()),
                    'negative_marks': _convert_negative_marks(row.get('negative_marks', '0').strip()),
                    'question_level': row.get('question_level', 'Medium').strip(),
                    'answer_text': row.get('answer_text', '').strip() or None,
                    'answer_link': row.get('answer_link', '').strip() or None,
                }
                if not all(question_data.get(k) for k in ['question_type', 'question_text', 'correct_option']):
                    raise ValueError("Missing required data in CSV row.")
                user_op.insert_test_question(question_data)
                last_q_num += 1
                inserted += 1
            except Exception as e:
                failed += 1
                errors.append({"row_number": i, "message": str(e)})
        return jsonify({
            "message": "CSV processing complete.", "inserted_count": inserted,
            "failed_count": failed, "errors": errors
        }), 200
    except Exception as e:
        logger.error(f"Error in upload_questions_csv: {e}")
        return jsonify({'message': f'Failed to process CSV file: {str(e)}'}), 500