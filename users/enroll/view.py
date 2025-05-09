from flask import flash, redirect, render_template, session, url_for
import mysql
from config import Config
from users.enroll.user_db import UserOperation
user_op =UserOperation()

from users import users_bp

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
    enrollments = {course['name']: user_op.check_enrollment(email, course['name']) for course in courses}

    return render_template('users/enroll/courses.html', courses=courses, enrollments=enrollments, email=email, username=username)