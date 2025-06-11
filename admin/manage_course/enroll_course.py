from flask import render_template, request, redirect, url_for, flash
from extensions import admin_login_required
from admin.manage_course.enroll_course_db import UserOperation
from admin import admin_bp

user_op = UserOperation()

@admin_bp.route('/courses')
@admin_login_required
def manage_courses():
    courses = user_op.get_all_courses()
    return render_template('admin/manage_course/enroll_course.html', courses=courses)

@admin_bp.route('/courses/add', methods=['POST'])
@admin_login_required
def add_course():
    code = request.form['code'].strip()
    name = request.form['name'].strip()
    description = request.form['description'].strip()

    if user_op.get_course_by_code(code):
        flash("Course with this code already exists!", "error")
    else:
        user_op.insert_course(code, name, description)
        flash("Course added successfully!", "success")

    return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/courses/update/<code>', methods=['POST'])
@admin_login_required
def update_course(code):
    name = request.form['name'].strip()
    description = request.form['description'].strip()

    current = user_op.get_course_by_code(code)
    if not current:
        flash("Course not found!", "error")
    elif name == current['name'].strip() and description == current['description'].strip():
        flash("No changes detected!", "warning")
    else:
        user_op.update_course(code, name, description)
        flash("Course updated successfully!", "success")

    return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/courses/delete/<code>', methods=['POST'])
@admin_login_required
def delete_course(code):
    user_op.delete_course(code)
    flash("Course deleted successfully!", "success")
    return redirect(url_for('admin.manage_courses'))
