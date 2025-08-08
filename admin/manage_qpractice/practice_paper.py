import csv
from io import StringIO
import logging
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import render_template, request, jsonify, flash, redirect, url_for
from .practice_paper_db import PaperOperation
from extensions import admin_login_required
from admin import admin_bp

paper_op = PaperOperation()
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'images', 'practice_paper')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/manage-practice-papers')
@admin_login_required
def manage_practice_papers():
    try:
        return render_template('admin/manage_qpractice/practice_paper.html')
    except Exception as e:
        logging.error(f"Error rendering manage_practice_papers template: {e}", exc_info=True)
        flash("An internal server error occurred while loading the page.", "admin_error")
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/api/papers/codes', methods=['GET'])
@admin_login_required
def get_paper_codes():
    try:
        codes = paper_op.get_all_paper_codes()
        return jsonify([code['code'] for code in codes])
    except Exception as e:
        logging.error(f"Error fetching paper codes: {e}", exc_info=True)
        return jsonify({'message': f'Could not fetch paper codes: {e}'}), 500

@admin_bp.route('/api/papers/subjects', methods=['GET'])
@admin_login_required
def get_subjects_for_paper():
    paper_code = request.args.get('paper_code')
    if not paper_code:
        return jsonify({'message': 'Paper Code is required.'}), 400
    try:
        subjects = paper_op.get_distinct_values('subject', paper_code)
        return jsonify([s['subject'] for s in subjects])
    except Exception as e:
        logging.error(f"Error fetching subjects for {paper_code}: {e}", exc_info=True)
        return jsonify({'message': f'Could not fetch subjects: {e}'}), 500

@admin_bp.route('/api/papers/topics', methods=['GET'])
@admin_login_required
def get_topics_for_subject():
    paper_code = request.args.get('paper_code')
    subject = request.args.get('subject')
    if not paper_code or not subject:
        return jsonify({'message': 'Paper Code and Subject are required.'}), 400
    try:
        topics = paper_op.get_distinct_values('topic', paper_code, subject)
        return jsonify([t['topic'] for t in topics])
    except Exception as e:
        logging.error(f"Error fetching topics for {paper_code}/{subject}: {e}", exc_info=True)
        return jsonify({'message': f'Could not fetch topics: {e}'}), 500

@admin_bp.route('/api/upload-quill-image', methods=['POST'])
@admin_login_required
def practice_upload_quill_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file found.'}), 400
    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type.'}), 400
    try:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        url_path = os.path.join('uploads', 'images', 'practice_paper', unique_filename).replace('\\', '/')
        return jsonify({'url': f'/static/{url_path}'})
    except Exception as e:
        logging.error(f"Error in practice_upload_quill_image: {e}", exc_info=True)
        return jsonify({'error': f'An error occurred during file upload: {e}'}), 500

@admin_bp.route('/api/questions/upload-csv', methods=['POST'])
@admin_login_required
def practice_upload_questions_csv():
    if 'csv_file' not in request.files:
        return jsonify({"message": "No CSV file provided."}), 400
    paper_code = request.form.get('paper_code')
    if not paper_code:
        return jsonify({"message": "Paper Code is required."}), 400
    csv_file = request.files['csv_file']
    if not csv_file or not csv_file.filename.lower().endswith('.csv'):
        return jsonify({"message": "Invalid file type. Please upload a .csv file."}), 400
    try:
        stream = StringIO(csv_file.stream.read().decode("UTF-8"))
        reader = csv.reader(stream)
        header_row = next(reader, None)
        inserted, failed, errors = 0, 0, []
        expected_header = ['question_id', 'question_type', 'year', 'paper_set', 'subject', 'topic',
                           'question_text', 'option_a', 'option_b', 'option_c', 'option_d',
                           'correct_option', 'answer_text', 'explanation_link']
        for i, row in enumerate(reader, 2):
            if not any(row):
                continue
            try:
                question_data = dict(zip(expected_header, row))
                question_data['paper_code'] = paper_code.strip()
                if not all(k in question_data and question_data[k] for k in ['question_id', 'question_type', 'subject', 'correct_option']):
                    raise ValueError("CSV row is missing required data: question_id, question_type, subject, or correct_option must not be empty.")
                paper_op.insert_question(question_data)
                inserted += 1
            except Exception as e:
                failed += 1
                errors.append({"row": i, "error": str(e)})
        return jsonify({"message": "CSV processing complete.", "inserted": inserted, "failed": failed, "errors": errors}), 200
    except Exception as e:
        logging.error(f"Error processing CSV: {e}", exc_info=True)
        return jsonify({'message': f'Failed to process CSV file: {e}'}), 500

@admin_bp.route('/api/questions/add-manual', methods=['POST'])
@admin_login_required
def practice_add_manual_question():
    data = request.get_json()
    if not data or not all(data.get(k) for k in ['paper_code', 'subject', 'question_id', 'question_type', 'correct_option']):
        return jsonify({'message': 'Paper Code, Subject, Question ID, Question Type, and Correct Option are required.'}), 400
    try:
        question_db_id = paper_op.insert_question(data)
        return jsonify({'message': 'Question added successfully!', 'id': question_db_id}), 201
    except Exception as e:
        logging.error(f"Error adding manual question: {e}", exc_info=True)
        return jsonify({'message': f'Database error: {e}'}), 500

@admin_bp.route('/api/questions/search', methods=['GET'])
@admin_login_required
def practice_search_questions_api():
    paper_code = request.args.get('paper_code')
    subject = request.args.get('subject')
    topic = request.args.get('topic')
    if not paper_code or not subject:
        return jsonify({'message': 'Paper Code and Subject are required for search.'}), 400
    try:
        questions = paper_op.search_questions(paper_code, subject, topic)
        return jsonify({'questions': questions, 'count': len(questions)})
    except Exception as e:
        logging.error(f"Error searching questions: {e}", exc_info=True)
        return jsonify({'message': f'Database error during search: {e}'}), 500

@admin_bp.route('/api/questions/update/<int:id>', methods=['PUT'])
@admin_login_required
def practice_update_question_api(id):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided for update.'}), 400
    try:
        paper_op.update_question(id, data)
        return jsonify({'message': 'Question updated successfully!'})
    except Exception as e:
        logging.error(f"Error updating question {id}: {e}", exc_info=True)
        return jsonify({'message': f'Database error during update: {e}'}), 500

@admin_bp.route('/api/questions/delete/<int:id>', methods=['DELETE'])
@admin_login_required
def practice_delete_question_api(id):
    try:
        paper_op.delete_question(id)
        return jsonify({'message': 'Question deleted successfully!'})
    except Exception as e:
        logging.error(f"Error deleting question {id}: {e}", exc_info=True)
        return jsonify({'message': f'Database error during deletion: {e}'}), 500
