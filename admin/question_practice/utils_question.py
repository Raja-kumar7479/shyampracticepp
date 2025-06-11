from admin.question_practice.question_db import UserOperation

user_op = UserOperation()

from datetime import datetime

def validate_question_form(form_data, next_id):
    question_id = form_data.get('question_id', '').strip()
    paper_code = form_data.get('paper_code', '').strip()
    subject = form_data.get('subject', '').strip()
    topic = form_data.get('topic', '').strip()
    question_type = form_data.get('question_type', '').strip()
    year = form_data.get('year', '').strip()
    question_text = form_data.get('question_text', '').strip()
    image_path = form_data.get('image_path', '').strip()

    option_a = form_data.get('option_a', '').strip()
    option_b = form_data.get('option_b', '').strip()
    option_c = form_data.get('option_c', '').strip()
    option_d = form_data.get('option_d', '').strip()

    correct_option = form_data.get('correct_option', '').strip()

    answer_text = form_data.get('answer_text', '').strip()
    explanation_link = form_data.get('explanation_link', '').strip()
    paper_set = form_data.get('paper_set', '').strip()

    if not paper_code:
        return None, "Paper Code is required."
    if not subject:
        return None, "Subject is required."
    if not topic:
        return None, "Topic is required."
    if not question_text or question_text == '<p><br></p>':
        return None, "Question Text cannot be empty."
    if not question_type:
        return None, "Question Type is required."
    if not year:
        return None, "Year is required."
    try:
        year_int = int(year)
        if not (2000 <= year_int <= 2030): 
            return None, "Year must be between 2000 and 2030."
    except ValueError:
        return None, "Year must be a valid number."

    if not question_id:
        question_id = str(next_id)
    
    if not correct_option:
        return None, "Correct Option/Value is required."

    if question_type == 'MCQ':
        if len(correct_option) != 1 or correct_option not in "ABCD":
            return None, "For MCQ, Correct Option must be a single letter (A, B, C, or D)."
    elif question_type == 'MSQ':
        selected_options = [opt.strip().upper() for opt in correct_option.replace(' ', ',').split(',') if opt.strip()]
        if not selected_options:
            return None, "For MSQ, Correct Option cannot be empty."
        valid_options = "ABCD"
        for opt in selected_options:
            if len(opt) != 1 or opt not in valid_options:
                return None, f"For MSQ, '{opt}' is an invalid option. Use A, B, C, or D."
        if len(set(selected_options)) != len(selected_options):
            return None, "For MSQ, Correct Option letters must be unique (e.g., A,B,C not A,A,B)."
        correct_option = ','.join(sorted(selected_options))
    elif question_type == 'NAT':
        try:
            float(correct_option)
        except ValueError:
            return None, "For NAT, Correct Value must be a valid number (integer or float)."
    else:
        return None, "Invalid Question Type."

    data = {
        'question_id': question_id,
        'paper_code': paper_code,
        'subject': subject,
        'topic': topic,
        'year': int(year),
        'question_type': question_type,
        'question_text': question_text,
        'image_path': image_path if image_path else None, 
        'option_a': option_a if option_a else None,
        'option_b': option_b if option_b else None,
        'option_c': option_c if option_c else None,
        'option_d': option_d if option_d else None,
        'correct_option': correct_option,
        'answer_text': answer_text if answer_text else None,
        'explanation_link': explanation_link if explanation_link else None,
        'paper_set': paper_set if paper_set else None,
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return data, None
