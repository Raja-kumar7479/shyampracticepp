from flask import render_template, request, session, redirect, url_for, jsonify, flash
from users.practice.user_db import UserOperation
from users.practice.utils_question import secure_access_required
from extensions import login_required
from users import users_bp

user_op = UserOperation()

@users_bp.route('/questions/topic/<paper_code>')
@login_required
def browse_by_topic(paper_code):
    email = session['email']
    unique_code = user_op.get_unique_code(email, paper_code)
    if not unique_code:
        return redirect(url_for('users.user_login'))
    return redirect(url_for('users.browse_by_topic_with_code', unique_code=unique_code, paper_code=paper_code))

@users_bp.route('/questions/topic/<unique_code>/<paper_code>')
@secure_access_required(('unique_code', 'paper_code'))
def browse_by_topic_with_code(unique_code, paper_code):
    email = session['email']
    subjects = user_op.fetch_all("SELECT DISTINCT subject FROM questions WHERE paper_code = %s", (paper_code,))
    return render_template('users/question/topic_select.html', subjects=subjects, paper_code=paper_code, username=session['username'], email=email, unique_code=unique_code)

@users_bp.route('/questions/topic/<unique_code>/<paper_code>/<subject>')
@secure_access_required(('unique_code', 'paper_code'))
def browse_topic_subject(unique_code, paper_code, subject):
    email = session['email']
    topics = user_op.fetch_all("SELECT DISTINCT topic FROM questions WHERE subject = %s AND paper_code = %s", (subject, paper_code))
    return render_template('users/question/topic_list.html', topics=topics, subject=subject, paper_code=paper_code, username=session['username'], email=email, unique_code=unique_code)

@users_bp.route('/questions/topic/<unique_code>/<paper_code>/<subject>/<topic>')
@secure_access_required(('unique_code', 'paper_code'))
def show_topic_questions(unique_code, paper_code, subject, topic):
    email = session['email']
    page = request.args.get('page', 1, type=int)
    per_page = 8
    total = user_op.fetch_one("SELECT COUNT(*) as total FROM questions WHERE subject = %s AND topic = %s AND paper_code = %s", (subject, topic, paper_code))['total']
    offset = (page - 1) * per_page
    questions = user_op.fetch_all("SELECT * FROM questions WHERE subject = %s AND topic = %s AND paper_code = %s LIMIT %s OFFSET %s", (subject, topic, paper_code, per_page, offset))
    total_pages = (total + per_page - 1) // per_page
    return render_template('users/question/display_questions.html', questions=questions, section='topic', subject=subject, topic=topic, paper_code=paper_code, page=page, total_pages=total_pages, username=session['username'], email=email, unique_code=unique_code)

@users_bp.route('/questions/subject/<unique_code>/<paper_code>')
@secure_access_required(('unique_code', 'paper_code'))
def browse_by_subject(unique_code, paper_code):
    email = session['email']
    subjects = user_op.fetch_all("SELECT DISTINCT subject FROM questions WHERE paper_code = %s", (paper_code,))
    return render_template('users/question/subject_select.html', subjects=subjects, paper_code=paper_code, username=session['username'], email=email, unique_code=unique_code)

@users_bp.route('/questions/subject/<unique_code>/<paper_code>/<subject>')
@secure_access_required(('unique_code', 'paper_code'))
def show_subject_questions(unique_code, paper_code, subject):
    email = session['email']
    page = request.args.get('page', 1, type=int)
    per_page = 8
    total = user_op.fetch_one("SELECT COUNT(*) as total FROM questions WHERE subject = %s AND paper_code = %s", (subject, paper_code))['total']
    offset = (page - 1) * per_page
    questions = user_op.fetch_all("SELECT * FROM questions WHERE subject = %s AND paper_code = %s LIMIT %s OFFSET %s", (subject, paper_code, per_page, offset))
    total_pages = (total + per_page - 1) // per_page
    return render_template('users/question/display_questions.html', questions=questions, section='subject', subject=subject, paper_code=paper_code, page=page, total_pages=total_pages, username=session['username'], email=email, unique_code=unique_code)

@users_bp.route('/questions/year/<unique_code>/<paper_code>')
@secure_access_required(('unique_code', 'paper_code'))
def browse_by_year(unique_code, paper_code):
    email = session['email']
    years = user_op.fetch_all("SELECT DISTINCT year FROM questions WHERE paper_code = %s ORDER BY year DESC", (paper_code,))
    return render_template('users/question/year_select.html', years=years, paper_code=paper_code, username=session['username'], email=email, unique_code=unique_code)

@users_bp.route('/questions/year/<unique_code>/<paper_code>/<int:year>')
@secure_access_required(('unique_code', 'paper_code'))
def show_year_questions(unique_code, paper_code, year):
    email = session['email']
    page = request.args.get('page', 1, type=int)
    per_page = 8
    total = user_op.fetch_one("SELECT COUNT(*) as total FROM questions WHERE year = %s AND paper_code = %s", (year, paper_code))['total']
    offset = (page - 1) * per_page
    questions = user_op.fetch_all("SELECT * FROM questions WHERE year = %s AND paper_code = %s LIMIT %s OFFSET %s", (year, paper_code, per_page, offset))
    total_pages = (total + per_page - 1) // per_page
    return render_template('users/question/display_questions.html', questions=questions, section='year', year=year, paper_code=paper_code, page=page, total_pages=total_pages, username=session['username'], email=email, unique_code=unique_code)

@users_bp.route('/check_answer/<int:question_id>', methods=['POST'])
@login_required
def check_answer_form(question_id):
    data = request.get_json()
    selected_option = data.get('selected_option')

    question = user_op.get_question_by_id(question_id)
    if not question:
        return jsonify({'error': 'Question not found.'}), 404

    correct_option = question['correct_option']
    question_type = question['question_type']
    answer_text = question.get('answer_text', '')
    explanation_link = question.get('explanation_link', '')

    is_correct = False

    if question_type == 'MCQ':
        is_correct = selected_option == correct_option

    elif question_type == 'MSQ':
        if isinstance(selected_option, list):
            selected_set = set(opt.upper().strip() for opt in selected_option)
            correct_set = set(opt.strip().upper() for opt in correct_option.split(','))
            is_correct = selected_set == correct_set

    elif question_type == 'NAT':
        try:
            selected_str = str(selected_option).strip().lower()
            correct_str = correct_option.strip().lower()
            is_correct = selected_str == correct_str
        except Exception:
            return jsonify({
                'error': 'Invalid input.',
                'correct_option': correct_option,
                'answer_text': answer_text,
                'explanation_link': explanation_link,
                'is_correct': False
            })

    return jsonify({
        'is_correct': is_correct,
        'correct_option': correct_option,
        'answer_text': answer_text,
        'explanation_link': explanation_link
    })
