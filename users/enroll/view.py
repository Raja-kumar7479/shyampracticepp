from flask import flash, redirect, render_template, session, url_for
from users.enroll.user_db import UserOperation
from extensions import login_required
user_op =UserOperation()

from users import users_bp

@users_bp.route('/my_courses', methods=['GET'])
@login_required
def my_courses():
    if 'email' not in session:
        flash('Please log in first!', 'course_alerts')
        return redirect(url_for('users.user_login'))

    email = session['email']
    username = session.get('username')

    if not username:
        user_data = user_op.get_user_by_email(email)
        if user_data:
            username = user_data['username']
            session['username'] = username 
        else:
            flash('User data not found. Please log in again.', 'course_alerts')
            return redirect(url_for('users.user_login'))

    enrolled_courses_data = user_op.get_enrolled_courses(email)

    enrolled_courses = []
    for item in enrolled_courses_data:
        course_code = item['code']
        unique_code = item['unique_code']
        course_details = user_op.get_course_details(course_code)
        if course_details:
            course_details['unique_code'] = unique_code
            enrolled_courses.append(course_details)

    return render_template('users/enroll/my_courses.html',
                           enrolled_courses=enrolled_courses,
                           email=email,
                           username=username)

@users_bp.route('/course', methods=['GET'])
def course_view():
    if 'email' not in session:
        flash('Please log in first!', 'course_alerts')
        return redirect(url_for('users.user_login'))

    email = session['email']
    username = session.get('username')

    if not username:
        user_data = user_op.get_user_by_email(email)
        if user_data:
            username = user_data['username']
            session['username'] = username 
        else:
            flash('User data not found. Please log in again.', 'course_alerts')
            return redirect(url_for('users.user_login'))

    courses = user_op.get_all_courses()

    enrollments = {
        course['code']: user_op.check_enrollment(email, course['code'])
        for course in courses
    }

    return render_template(
        'users/enroll/courses.html',
        courses=courses,
        enrollments=enrollments,
        email=email,
        username=username
    )
