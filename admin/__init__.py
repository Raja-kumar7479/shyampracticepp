from flask import Blueprint
admin_bp = Blueprint('admin', __name__)

from .auth import admin_login
from .manage_qpractice import practice_paper
from .manage_course import  enroll_course
from .manage_mock_test import test_details_insert,test_feedback,user_test_log
from .manage_modules import course_content,notes_content,practice_questions
from .manage_purchase import purchase_handle