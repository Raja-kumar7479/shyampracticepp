from flask import flash, jsonify, redirect, render_template, request, session, url_for
from users.enroll.user_db import UserOperation
from extensions import login_required

from users import users_bp
user_op =UserOperation()

@users_bp.route('/dashboard/<course_code>/<unique_code>')
@login_required
def course_dashboard(course_code, unique_code):
    if 'email' not in session:
        flash("You must be logged in to access the dashboard.", "dashboard_alerts")
        return redirect(url_for('users.user_login'))

    email = session['email']
    username = session['username']

    stored_code = user_op.get_user_unique_code(email, course_code)
    if stored_code != unique_code:
        flash("Access Denied! Invalid or unauthorized access.", "dashboard_alerts")
        return redirect(url_for('users.course_page'))

    books = user_op.get_books_for_course(course_code)
    question_sections = {
        "Topic-wise": url_for('users.browse_by_topic', unique_code=unique_code, paper_code=course_code),
        "Subject-wise": url_for('users.browse_by_subject', unique_code=unique_code, paper_code=course_code),
        "Year-wise": url_for('users.browse_by_year', unique_code=unique_code, paper_code=course_code)
    }

    courses = user_op.get_courses_by_code(course_code)
    sections = user_op.get_sections_by_code(course_code)

    return render_template(
        "users/dashboard/practice.html",
        email=email,
        username=username,
        course_code=course_code.upper(),
        unique_code=unique_code,
        books=books,
        question_sections=question_sections,
        courses=courses,  
        sections=sections  
    )
