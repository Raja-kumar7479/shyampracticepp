import logging
from flask import render_template, request, session, redirect, url_for, jsonify, Blueprint
from users.question_practice.user_db import UserOperation
from users.question_practice.utils_question import secure_access_required
from extensions import user_login_required
from users import users_bp

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

user_op = UserOperation()

@users_bp.route('/questions/topic/<paper_code>')
@user_login_required
def browse_by_topic(paper_code):
    try:
        user_email = session['user_email']
        logger.info(f"User '{user_email}' starting topic-wise browse for paper: {paper_code}")
        unique_code = user_op.get_unique_code(user_email, paper_code)
        if not unique_code:
            logger.warning(f"No unique_code for user '{user_email}' and paper '{paper_code}'.")
            return redirect(url_for('users.user_login'))
        return redirect(url_for('users.browse_by_topic_with_code', unique_code=unique_code, paper_code=paper_code))
    except Exception:
        logger.exception(f"Error in browse_by_topic for paper_code: {paper_code}")
        return "An internal server error occurred.", 500

@users_bp.route('/questions/topic/<unique_code>/<paper_code>')
@secure_access_required(('unique_code', 'paper_code'))
def browse_by_topic_with_code(unique_code, paper_code):
    try:
        user_email = session['user_email']
        logger.info(f"User '{user_email}' fetching subjects for paper: {paper_code}")
        subjects = user_op.fetch_all("SELECT DISTINCT subject FROM questions WHERE paper_code = %s", (paper_code,))
        return render_template('users/question_practice/topic_select.html', subjects=subjects, paper_code=paper_code, username=session['user_username'], email=user_email, unique_code=unique_code)
    except Exception:
        logger.exception(f"Error fetching subjects for paper: {paper_code}")
        return "An internal server error occurred.", 500

@users_bp.route('/questions/topic/<unique_code>/<paper_code>/<subject>')
@secure_access_required(('unique_code', 'paper_code'))
def browse_topic_subject(unique_code, paper_code, subject):
    try:
        user_email = session['user_email']
        logger.info(f"User '{user_email}' fetching topics for subject: {subject}, paper: {paper_code}")
        topics = user_op.fetch_all("SELECT DISTINCT topic FROM questions WHERE subject = %s AND paper_code = %s", (subject, paper_code))
        return render_template('users/question_practice/topic_list.html', topics=topics, subject=subject, paper_code=paper_code, username=session['user_username'], email=user_email, unique_code=unique_code)
    except Exception:
        logger.exception(f"Error fetching topics for subject: {subject}, paper: {paper_code}")
        return "An internal server error occurred.", 500

@users_bp.route('/questions/topic/<unique_code>/<paper_code>/<subject>/<topic>')
@secure_access_required(('unique_code', 'paper_code'))
def show_topic_questions(unique_code, paper_code, subject, topic):
    try:
        user_email = session['user_email']
        page = request.args.get('page', 1, type=int)
        logger.info(f"User '{user_email}' viewing questions for topic: {topic}, page: {page}")
        per_page = 8
        total_result = user_op.fetch_one("SELECT COUNT(*) as total FROM questions WHERE subject = %s AND topic = %s AND paper_code = %s", (subject, topic, paper_code))
        if total_result is None:
            logger.error(f"Failed to fetch question count for topic: {topic}")
            return "Could not retrieve question count.", 500
        total = total_result['total']
        offset = (page - 1) * per_page
        questions = user_op.fetch_all("SELECT * FROM questions WHERE subject = %s AND topic = %s AND paper_code = %s LIMIT %s OFFSET %s", (subject, topic, paper_code, per_page, offset))
        total_pages = (total + per_page - 1) // per_page
        return render_template('users/question_practice/display_questions.html', questions=questions, section='topic', subject=subject, topic=topic, paper_code=paper_code, page=page, total_pages=total_pages, username=session['user_username'], email=user_email, unique_code=unique_code)
    except Exception:
        logger.exception(f"Error showing topic questions for topic: {topic}")
        return "An internal server error occurred.", 500

@users_bp.route('/questions/subject/<unique_code>/<paper_code>')
@secure_access_required(('unique_code', 'paper_code'))
def browse_by_subject(unique_code, paper_code):
    try:
        user_email = session['user_email']
        logger.info(f"User '{user_email}' starting subject-wise browse for paper: {paper_code}")
        subjects = user_op.fetch_all("SELECT DISTINCT subject FROM questions WHERE paper_code = %s", (paper_code,))
        return render_template('users/question_practice/subject_select.html', subjects=subjects, paper_code=paper_code, username=session['user_username'], email=user_email, unique_code=unique_code)
    except Exception:
        logger.exception(f"Error in browse_by_subject for paper: {paper_code}")
        return "An internal server error occurred.", 500

@users_bp.route('/questions/subject/<unique_code>/<paper_code>/<subject>')
@secure_access_required(('unique_code', 'paper_code'))
def show_subject_questions(unique_code, paper_code, subject):
    try:
        user_email = session['user_email']
        page = request.args.get('page', 1, type=int)
        logger.info(f"User '{user_email}' viewing questions for subject: {subject}, page: {page}")
        per_page = 8
        total_result = user_op.fetch_one("SELECT COUNT(*) as total FROM questions WHERE subject = %s AND paper_code = %s", (subject, paper_code))
        if total_result is None:
            logger.error(f"Failed to fetch question count for subject: {subject}")
            return "Could not retrieve question count.", 500
        total = total_result['total']
        offset = (page - 1) * per_page
        questions = user_op.fetch_all("SELECT * FROM questions WHERE subject = %s AND paper_code = %s LIMIT %s OFFSET %s", (subject, paper_code, per_page, offset))
        total_pages = (total + per_page - 1) // per_page
        return render_template('users/question_practice/display_questions.html', questions=questions, section='subject', subject=subject, paper_code=paper_code, page=page, total_pages=total_pages, username=session['user_username'], email=user_email, unique_code=unique_code)
    except Exception:
        logger.exception(f"Error showing subject questions for subject: {subject}")
        return "An internal server error occurred.", 500

@users_bp.route('/questions/year/<unique_code>/<paper_code>')
@secure_access_required(('unique_code', 'paper_code'))
def browse_by_year(unique_code, paper_code):
    try:
        user_email = session['user_email']
        logger.info(f"User '{user_email}' starting year-wise browse for paper: {paper_code}")
        years = user_op.fetch_all("SELECT DISTINCT year FROM questions WHERE paper_code = %s ORDER BY year DESC", (paper_code,))
        return render_template('users/question_practice/year_select.html', years=years, paper_code=paper_code, username=session['user_username'], email=user_email, unique_code=unique_code)
    except Exception:
        logger.exception(f"Error in browse_by_year for paper: {paper_code}")
        return "An internal server error occurred.", 500

@users_bp.route('/questions/year/<unique_code>/<paper_code>/<int:year>')
@secure_access_required(('unique_code', 'paper_code'))
def show_year_questions(unique_code, paper_code, year):
    try:
        user_email = session['user_email']
        page = request.args.get('page', 1, type=int)
        logger.info(f"User '{user_email}' viewing questions for year: {year}, page: {page}")
        per_page = 8
        total_result = user_op.fetch_one("SELECT COUNT(*) as total FROM questions WHERE year = %s AND paper_code = %s", (year, paper_code))
        if total_result is None:
            logger.error(f"Failed to fetch question count for year: {year}")
            return "Could not retrieve question count.", 500
        total = total_result['total']
        offset = (page - 1) * per_page
        questions = user_op.fetch_all("SELECT * FROM questions WHERE year = %s AND paper_code = %s LIMIT %s OFFSET %s", (year, paper_code, per_page, offset))
        total_pages = (total + per_page - 1) // per_page
        return render_template('users/question_practice/display_questions.html', questions=questions, section='year', year=year, paper_code=paper_code, page=page, total_pages=total_pages, username=session['user_username'], email=user_email, unique_code=unique_code)
    except Exception:
        logger.exception(f"Error showing year questions for year: {year}")
        return "An internal server error occurred.", 500

@users_bp.route('/check_answer/<int:question_id>', methods=['POST'])
@user_login_required
def check_answer_form(question_id):
    user_email = session.get('user_email', 'unknown')
    try:
        data = request.get_json()
        if not data:
            logger.warning(f"User '{user_email}' sent empty payload for question_id: {question_id}")
            return jsonify({'error': 'Bad request. No data received.'}), 400
        
        selected_option = data.get('selected_option')
        logger.info(f"User '{user_email}' checking answer for question_id: {question_id} with option: {selected_option}")
        
        question = user_op.get_question_by_id(question_id)
        if not question:
            logger.warning(f"Question not found for id: {question_id} attempt by user: '{user_email}'")
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
                logger.warning(f"Invalid NAT input for question_id: {question_id} from user: '{user_email}'", exc_info=True)
                return jsonify({
                    'error': 'Invalid input for NAT question.',
                    'correct_option': correct_option,
                    'answer_text': answer_text,
                    'explanation_link': explanation_link,
                    'is_correct': False
                })

        logger.info(f"Answer for QID:{question_id} by user '{user_email}' was {'correct' if is_correct else 'incorrect'}.")
        return jsonify({
            'is_correct': is_correct,
            'correct_option': correct_option,
            'answer_text': answer_text,
            'explanation_link': explanation_link
        })
    except Exception:
        logger.exception(f"Fatal error in check_answer_form for QID: {question_id}, user: '{user_email}'")
        return jsonify({'error': 'An internal server error occurred.'}), 500

@users_bp.route('/report_issue/<int:question_id>', methods=['POST'])
@user_login_required
def report_issue(question_id):
    user_email = session.get('user_email', 'unknown')
    try:
        data = request.get_json()
        problem_description = data.get('problem')
        
        if not problem_description or not isinstance(problem_description, str) or len(problem_description.strip()) < 10:
            logger.warning(f"Insufficient problem description from user '{user_email}' for QID: {question_id}.")
            return jsonify({'error': 'Please provide a detailed description of the issue (minimum 10 characters).'}), 400

        logger.info(f"User '{user_email}' is reporting an issue for question ID: {question_id}.")
        
        success = user_op.report_question_issue(question_id, problem_description.strip(), user_email)
        
        if success:
            logger.info(f"Successfully recorded issue for QID: {question_id} from user '{user_email}'.")
            return jsonify({'message': 'Your report has been submitted successfully. Thank you for your feedback!'})
        else:
            logger.error(f"Failed to record issue for QID: {question_id} from user '{user_email}'.")
            return jsonify({'error': 'We could not process your report at this time. Please try again later.'}), 500
            
    except Exception:
        logger.exception(f"Fatal error in report_issue for QID: {question_id}, user: '{user_email}'")
        return jsonify({'error': 'An internal server error occurred.'}), 500
