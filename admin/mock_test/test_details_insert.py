from flask import Flask, render_template, request, jsonify
from admin.mock_test.test_details_db import UserOperation
from extensions import admin_login_required
from admin import admin_bp
import mysql.connector 

user_op = UserOperation()

def _convert_negative_marks(negative_marks_str):
    if not negative_marks_str:
        return 0.0
    try:
        if isinstance(negative_marks_str, (int, float)):
            return float(negative_marks_str)
        if '/' in negative_marks_str:
            parts = negative_marks_str.split('/')
            if len(parts) == 2:
                return float(parts[0]) / float(parts[1])
            else:
                raise ValueError("Invalid fraction format.")
        else:
            return float(negative_marks_str)
    except ValueError:
        raise ValueError('Invalid format for Negative Marks. Please use a number or a simple fraction like "1/2".')


@admin_bp.route('/manage-study-materials', methods=['GET'])
@admin_login_required
def manage_study_materials():
    return render_template('admin/mock_test/test_details_insert.html')

@admin_bp.route('/api/study-materials', methods=['GET'])
@admin_login_required
def get_study_materials_api():
    try:
        materials = user_op.get_all_study_materials()
        return jsonify(materials)
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error fetching study materials: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/study-materials/add', methods=['POST'])
@admin_login_required
def add_study_material_api():
    data = request.get_json()
    required_fields = ['name', 'code', 'status', 'label', 'stream', 'test_id', 'test_key', 'test_code']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({'message': f'Error: Missing or empty required field: {field}'}), 400

    try:
        if user_op.is_test_id_or_key_or_code_duplicate(data['test_id'], data['test_key'], data['test_code']):
            return jsonify({'message': 'Error: Duplicate Test ID, Test Key, or Test Code. Please use unique values.'}), 400
        user_op.insert_study_material(data)
        return jsonify({'message': 'Study Material added successfully!'}), 201
    except mysql.connector.IntegrityError as e:
        
        return jsonify({'message': f'Database integrity error: {str(e)}'}), 400
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error adding study material: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/study-materials/update/<int:id>', methods=['PUT'])
@admin_login_required
def update_study_material_api(id):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided for update.'}), 400
    try:
        for field, value in data.items():

            if field in ['test_id', 'test_key', 'test_code']:

                if user_op.is_test_id_or_key_or_code_duplicate(data.get('test_id', ''), data.get('test_key', ''), data.get('test_code', ''), material_id=id):
                     return jsonify({'message': 'Error: Update would result in duplicate Test ID, Test Key, or Test Code with another material.'}), 400

            user_op.update_study_material_field(id, field, value)
        return jsonify({'message': 'Study Material updated successfully!'})
    except ValueError as e: 
        return jsonify({'message': f'Invalid update request: {str(e)}'}), 400
    except mysql.connector.IntegrityError as e:
        return jsonify({'message': f'Database integrity error during update: {str(e)}'}), 400
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error updating study material: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/study-materials/delete/<int:id>', methods=['DELETE'])
@admin_login_required
def delete_study_material_api(id):
    try:
        user_op.delete_study_material(id)
        return jsonify({'message': 'Study Material deleted successfully!'})
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error deleting study material: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/test-descriptions', methods=['GET'])
@admin_login_required
def get_all_test_descriptions_api():
    try:
        descriptions = user_op.get_all_test_descriptions()
        return jsonify(descriptions)
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error fetching test descriptions: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/test-descriptions/<test_id>', methods=['GET'])
@admin_login_required
def get_test_descriptions_by_id_api(test_id):
    try:
        descriptions = user_op.get_test_descriptions_by_test_id(test_id)
        return jsonify(descriptions)
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error fetching test descriptions by ID: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/test-descriptions/add', methods=['POST'])
@admin_login_required
def add_test_description_api():
    data = request.get_json()
    required_fields = ['test_id', 'test_number', 'subject_title', 'total_questions', 'total_marks', 'total_duration_minutes']
    for field in required_fields:
        if field not in data or not data[field] :
            return jsonify({'message': f'Error: Missing or empty required field: {field}'}), 400

    for num_field in ['test_number', 'total_questions', 'total_marks', 'total_duration_minutes']:
        try:
            data[num_field] = int(data[num_field])
        except (ValueError, TypeError):
            return jsonify({'message': f'Error: {num_field} must be a valid number.'}), 400
    if 'year' in data and data['year']: # Year is optional
        try:
            data['year'] = int(data['year'])
        except (ValueError, TypeError):
            return jsonify({'message': 'Error: Year must be a valid number.'}), 400
    else:
        data['year'] = None 

    try:
        user_op.insert_test_description(data)
        return jsonify({'message': 'Test Description added successfully!'}), 201
    except mysql.connector.IntegrityError as e:
        return jsonify({'message': f'Database integrity error: {str(e)}. Test Number might be duplicate for this Test ID.'}), 400
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error adding test description: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/test-descriptions/update/<int:id>', methods=['PUT'])
@admin_login_required
def update_test_description_api(id):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided for update.'}), 400

    for field, value in data.items():
        if field in ['test_number', 'total_questions', 'total_marks', 'total_duration_minutes', 'year']:
            if value is not None and value != '': # Allow year to be empty
                try:
                    data[field] = int(value) if field != 'year' else (int(value) if value else None)
                except (ValueError, TypeError):
                    return jsonify({'message': f'Error: {field} must be a valid number.'}), 400

    try:
        for field, value in data.items():
            user_op.update_test_description_field(id, field, value)
        return jsonify({'message': 'Test Description updated successfully!'})
    except ValueError as e:
        return jsonify({'message': f'Invalid update request: {str(e)}'}), 400
    except mysql.connector.IntegrityError as e:
        return jsonify({'message': f'Database integrity error during update: {str(e)}. Test Number might be duplicate.'}), 400
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error updating test description: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/test-descriptions/delete/<int:id>', methods=['DELETE'])
@admin_login_required
def delete_test_description_api(id):
    try:
        user_op.delete_test_description(id)
        return jsonify({'message': 'Test Description deleted successfully!'})
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error deleting test description: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/test-questions/<test_id>', methods=['GET'])
@admin_login_required
def get_test_questions_api(test_id):
    try:
        questions = user_op.get_test_questions_by_test_id(test_id)
        total_questions_count = user_op.get_total_questions_count_for_test_id(test_id)
        test_description = user_op._fetch_one("SELECT total_questions FROM test_description WHERE test_id = %s", (test_id,))
        max_allowed_questions = test_description['total_questions'] if test_description else 0
        return jsonify({
            'questions': questions,
            'current_count': total_questions_count,
            'max_allowed': max_allowed_questions
        })
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error fetching test questions: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/test-questions/add', methods=['POST'])
@admin_login_required
def add_test_question_api():
    data = request.get_json()
    test_id = data.get('test_id')
    section_id = data.get('section_id')
    section_name = data.get('section_name')
    question_type = data.get('question_type')
    correct_option = data.get('correct_option')
    correct_marks = data.get('correct_marks')
    question_text = data.get('question_text') 

    if not test_id or not section_id or not section_name or not question_type or not correct_option or not correct_marks or not question_text:
        missing_fields = []
        if not test_id: missing_fields.append('Test ID')
        if not section_id: missing_fields.append('Section ID')
        if not section_name: missing_fields.append('Section Name')
        if not question_type: missing_fields.append('Question Type')
        if not correct_option: missing_fields.append('Correct Option')
        if not correct_marks: missing_fields.append('Correct Marks')
        if not question_text: missing_fields.append('Question Text')

        return jsonify({'message': f'Error: Missing or empty required fields: {", ".join(missing_fields)}.'}), 400

    test_description_data = user_op._fetch_one("SELECT total_questions FROM test_description WHERE test_id = %s", (test_id,))
    if not test_description_data:
        return jsonify({'message': f'Error: Test ID {test_id} not found in Test Descriptions.'}), 404

    max_allowed_questions = test_description_data['total_questions']
    current_questions_count = user_op.get_total_questions_count_for_test_id(test_id)

    if current_questions_count >= max_allowed_questions:
        return jsonify({'message': f'Error: Maximum questions ({max_allowed_questions}) for Test ID {test_id} already reached. Cannot add more questions.'}), 400

    next_question_number = user_op.get_max_question_number_in_section(test_id, section_id) + 1
    data['question_number'] = next_question_number

    try:
        data['negative_marks'] = _convert_negative_marks(data.get('negative_marks'))
        data['correct_marks'] = float(data['correct_marks']) # Ensure correct_marks is float
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except TypeError:
        return jsonify({'message': 'Correct Marks must be a number.'}), 400


    try:
        user_op.insert_test_question(data)
        return jsonify({'message': 'Test Question added successfully!', 'current_count': current_questions_count + 1}), 201
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error adding test question: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/test-questions/update/<int:id>', methods=['PUT'])
@admin_login_required
def update_test_question_api(id):
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided for update.'}), 400

    if 'negative_marks' in data:
        try:
            data['negative_marks'] = _convert_negative_marks(data['negative_marks'])
        except ValueError as e:
            return jsonify({'message': str(e)}), 400
    if 'correct_marks' in data and data['correct_marks'] is not None and data['correct_marks'] != '':
        try:
            data['correct_marks'] = float(data['correct_marks'])
        except (ValueError, TypeError):
            return jsonify({'message': 'Correct Marks must be a number.'}), 400


    try:
        for field, value in data.items():
            user_op.update_test_question_field(id, field, value)
        return jsonify({'message': 'Test Question updated successfully!'})
    except ValueError as e:
        return jsonify({'message': f'Invalid update request: {str(e)}'}), 400
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error updating test question: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500

@admin_bp.route('/api/test-questions/delete/<int:id>', methods=['DELETE'])
@admin_login_required
def delete_test_question_api(id):
    try:
        user_op.delete_test_question(id)
        return jsonify({'message': 'Test Question deleted successfully!'})
    except mysql.connector.Error as e:
        return jsonify({'message': f'Database error deleting test question: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'An unexpected error occurred: {str(e)}'}), 500