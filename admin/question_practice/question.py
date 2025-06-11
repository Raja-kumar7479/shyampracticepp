from flask import render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from extensions import admin_login_required
from admin.question_practice.question_db import UserOperation
from admin import admin_bp
from admin.question_practice.utils_question import validate_question_form
import re 

user_op = UserOperation()

@admin_bp.route('/admin/insert', methods=['GET'])
@admin_login_required
def insert_question():
    next_id = user_op.get_next_question_id()
    return render_template('admin/question_practice/insert_question.html', next_question_id=next_id, now=datetime.utcnow())

@admin_bp.route('/admin/insert_question_ajax', methods=['POST'])
@admin_login_required
def insert_question_ajax():
    form_data = request.get_json()

    next_id = user_op.get_next_question_id()

    data, error = validate_question_form(form_data, next_id)

    if error:
        flash(f'Error: {error}', 'danger')
        return jsonify({'success': False, 'error': error}), 400

    success, db_error = user_op.insert_question(data)
    if success:
        flash(f"Question inserted successfully with ID {data['question_id']}!", 'success')
        return jsonify({'success': True, 'message': f"Question inserted successfully with ID {data['question_id']}!"}), 200
    else:
        flash(f"Failed to insert question: {db_error}", 'danger')
        return jsonify({'success': False, 'error': f"Failed to insert question: {db_error}"}), 500

@admin_bp.route('/admin/get_next_question_id', methods=['GET'])
@admin_login_required
def get_next_question_id_api():
    next_id = user_op.get_next_question_id()
    return jsonify({'next_id': next_id})

@admin_bp.route('/admin/show_questions', methods=['GET', 'POST'])
@admin_login_required
def show_questions():
    if request.method == 'POST':
        session['paper_code'] = request.form.get('paper_code', '').strip()
        session['subject'] = request.form.get('subject', '').strip()
        session['topic'] = request.form.get('topic', '').strip()
        
        return redirect(url_for('admin.show_questions', 
                                 paper_code=session['paper_code'],
                                 subject=session['subject'],
                                 topic=session['topic']))

    paper_code = request.args.get('paper_code', '').strip() or session.get('paper_code', '')
    subject = request.args.get('subject', '').strip() or session.get('subject', '')
    topic = request.args.get('topic', '').strip() or session.get('topic', '')

    questions = []
    if paper_code:
        questions = user_op.fetch_questions(paper_code, subject, topic)
    
    for q in questions:
        question_text_with_placeholder = q.get('question_text') or ''
        image_url = q.get('image_path')
        
        if image_url and '[IMAGE_PLACEHOLDER]' in question_text_with_placeholder:
            q['display_question_text'] = question_text_with_placeholder.replace(
                '[IMAGE_PLACEHOLDER]', 
                f'<img src="{image_url}">'
            )
        else:
            q['display_question_text'] = question_text_with_placeholder 

        if isinstance(q.get('last_updated'), str):
            try:
                q['last_updated'] = datetime.strptime(q['last_updated'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                q['last_updated'] = None

    return render_template('admin/question_practice/show_questions.html',
                           questions=questions,
                           now=datetime.utcnow(),
                           paper_code=paper_code,
                           subject=subject,
                           topic=topic)

@admin_bp.route('/admin/delete_question/<question_id>', methods=['POST'])
@admin_login_required
def delete_question(question_id):
    success, error = user_op.delete_question_by_id(question_id)
    if success:
        flash(f'Question ID {question_id} deleted successfully.', 'success')
        return jsonify({'success': True})
    else:
        flash(f'Error deleting question ID {question_id}: {error}', 'danger')
        return jsonify({'success': False, 'error': error})

@admin_bp.route('/admin/update_single_question', methods=['POST'])
@admin_login_required
def update_single_question():
    data = request.get_json()
    original_id = data.get('original_id')
    new_id_from_frontend = data.get('new_id')
    updates = data.get('updates', {})

    if not original_id or not updates:
        flash('Invalid data sent for update.', 'danger')
        return jsonify({'success': False, 'error': 'Invalid data sent.'})

    id_changed = False
    if new_id_from_frontend and new_id_from_frontend != original_id:
        id_changed = True
        potential_new_id = new_id_from_frontend
        
        success, error = user_op.update_question_id(original_id, potential_new_id)
        if not success:
            flash(f"Failed to update Question ID from '{original_id}' to '{potential_new_id}': {error}", 'danger')
            return jsonify({'success': False, 'error': error})
        
        original_id = potential_new_id

    success, error = user_op.update_question_by_id(original_id, updates)
    if success:
        flash(f'Question ID {original_id} updated successfully.', 'success')
        return jsonify({'success': True, 'new_question_id': original_id if id_changed else None})
    else:
        flash(f'Error updating question ID {original_id}: {error}', 'danger')
        return jsonify({'success': False, 'error': error})