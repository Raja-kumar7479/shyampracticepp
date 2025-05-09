from flask import render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from extensions import admin_login_required
from admin.question.admin_db import UserOperation
from admin import admin_bp
from admin.question.utils_question import validate_question_form

user_op = UserOperation()


@admin_bp.route('/admin/insert', methods=['GET', 'POST'])
@admin_login_required
def insert_question():
    next_id = user_op.get_next_question_id()

    if request.method == 'POST':
        form_data = request.form.to_dict()
        data, error = validate_question_form(form_data, next_id)

        if error:
            flash(error, 'danger')
            return redirect(url_for('admin.insert_question'))

        user_op.insert_question(data)
        flash(f"Question inserted successfully with ID {data['question_id']}!", 'success')
        return redirect(url_for('admin.insert_question'))

    return render_template('admin/question/insert_question.html', next_question_id=next_id)

@admin_bp.route('/admin/show_questions', methods=['GET', 'POST'])
@admin_login_required
def show_questions():
    if request.method == 'POST':
        session['paper_code'] = request.form.get('paper_code', '').strip()
        session['subject'] = request.form.get('subject', '').strip()
        session['topic'] = request.form.get('topic', '').strip()
        return redirect(url_for('admin.show_questions'))

    paper_code = request.args.get('paper_code', '').strip() or session.get('paper_code', '')
    subject = request.args.get('subject', '').strip() or session.get('subject', '')
    topic = request.args.get('topic', '').strip() or session.get('topic', '')

    questions = user_op.fetch_questions(paper_code, subject, topic) if paper_code else []

    return render_template('admin/question/show_questions.html',
                           questions=questions,
                           now=datetime.utcnow(),
                           paper_code=paper_code,
                           subject=subject,
                           topic=topic)

@admin_bp.route('/admin/delete_question/<int:question_id>', methods=['POST'])
@admin_login_required
def delete_question(question_id):
    success, error = user_op.delete_question_by_id(question_id)
    return jsonify({'success': success, 'error': error} if not success else {'success': True})

@admin_bp.route('/admin/update_single_question', methods=['POST'])
@admin_login_required
def update_single_question():
    data = request.get_json()
    original_id = data.get('original_id')
    new_id = data.get('new_id')
    updates = data.get('updates', {})

    if not original_id or not updates:
        return jsonify({'success': False, 'error': 'Invalid data sent.'})

    success, error = user_op.update_question_by_id(original_id, updates)
    return jsonify({'success': success, 'new_id': new_id} if success else {'success': False, 'error': error})
