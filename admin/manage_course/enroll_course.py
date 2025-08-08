import logging
from flask import render_template, request, url_for, flash, session, jsonify
from extensions import admin_login_required
from admin.manage_course.enroll_course_db import UserOperation
from admin import admin_bp

user_op = UserOperation()

@admin_bp.route('/courses')
@admin_login_required
def manage_courses():
    try:
        courses = user_op.get_all_courses()
        return render_template('admin/manage_course/enroll_course.html', courses=courses)
    except Exception as e:
        flash("An unexpected error occurred while loading the page.", "admin_error")
        return render_template('admin/manage_course/enroll_course.html', courses=[])

@admin_bp.route('/courses/add', methods=['POST'])
@admin_login_required
def add_course():
    if session.get('admin_role') != 'owner':
        return jsonify({'status': 'error', 'message': 'You are not authorized to perform this action.'}), 403
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        if not code or not name or not description:
            return jsonify({'status': 'error', 'message': 'All fields are required.'}), 400
        if user_op.get_course_by_code(code):
            return jsonify({'status': 'error', 'message': f"A course with code '{code}' already exists."}), 409
        if user_op.insert_course(code, name, description):
            return jsonify({
                'status': 'success',
                'message': 'Course added successfully!',
                'course': {'code': code, 'name': name, 'description': description}
            }), 201
        else:
            return jsonify({'status': 'error', 'message': 'Failed to add course due to a database error.'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred.'}), 500

@admin_bp.route('/courses/update/<code>', methods=['POST'])
@admin_login_required
def update_course(code):
    if session.get('admin_role') != 'owner':
        return jsonify({'status': 'error', 'message': 'You are not authorized to perform this action.'}), 403
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        if not name or not description:
            return jsonify({'status': 'error', 'message': 'Name and description cannot be empty.'}), 400
        existing_course = user_op.get_course_by_code(code)
        if not existing_course:
            return jsonify({'status': 'error', 'message': 'Course not found.'}), 404
        if existing_course['name'] == name and existing_course['description'] == description:
            return jsonify({'status': 'info', 'message': 'No changes were detected.'}), 200
        if user_op.update_course(code, name, description):
            return jsonify({'status': 'success', 'message': 'Course updated successfully!'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to update course due to a database error.'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred.'}), 500

@admin_bp.route('/courses/delete/<code>', methods=['POST'])
@admin_login_required
def delete_course(code):
    if session.get('admin_role') != 'owner':
        return jsonify({'status': 'error', 'message': 'You are not authorized to perform this action.'}), 403
    try:
        if not user_op.get_course_by_code(code):
            return jsonify({'status': 'error', 'message': 'Course not found.'}), 404
        if user_op.delete_course(code):
            return jsonify({'status': 'success', 'message': 'Course deleted successfully!'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to delete course due to a database error.'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'An unexpected error occurred.'}), 500
