from admin.question.admin_db import UserOperation

user_op = UserOperation()

def validate_question_form(form_data, next_id):
    data = {}
    q_id = form_data.get('question_id', '').strip()
    q_text = form_data.get('question_text', '').strip()

    if q_id:
        if user_op.check_question_exists_by_id(q_id):
            return None, f"Question ID {q_id} already exists!"
        data['question_id'] = q_id
    else:
        data['question_id'] = str(next_id)

    if user_op.check_question_exists_by_text(q_text):
        return None, "This question already exists!"
    data['question_text'] = q_text

    q_type = form_data.get('question_type', '').strip()
    data['question_type'] = q_type

    allowed_fields = [
        'paper_code', 'subject', 'topic', 'answer_text',
        'paper_set', 'explanation_link', 'year', 'image_path'
    ]
    if q_type != 'NAT':
        allowed_fields += ['option_a', 'option_b', 'option_c', 'option_d']

    for field in allowed_fields:
        data[field] = form_data.get(field, '').strip()

    # Ensure image path is valid (only accept HTTP links)
    img_path = data.get('image_path', '')
    data['image_path'] = img_path if img_path.startswith('http') else ''

    # Correct Option
    if q_type == 'MCQ':
        opt = form_data.get('correct_option_mcq', '').strip().upper()
        if len(opt) != 1 or opt not in 'ABCD':
            return None, "MCQ must have one correct option (A, B, C, or D)."
        data['correct_option'] = opt
    elif q_type == 'MSQ':
        raw = form_data.get('correct_option_mcq', '')
        options = [o.strip().upper() for o in raw.split(',') if o.strip()]
        if not options or not all(opt in 'ABCD' for opt in options):
            return None, "MSQ options must be A, B, C, or D (comma-separated)."
        data['correct_option'] = ','.join(sorted(set(options)))
    elif q_type == 'NAT':
        nat_val = form_data.get('correct_option_nat', '').strip()
        try:
            float(nat_val)
            data['correct_option'] = nat_val
        except ValueError:
            return None, "NAT must be a valid numeric value."
    else:
        return None, "Invalid question type."

    return data, None
