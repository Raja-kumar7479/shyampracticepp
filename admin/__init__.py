from flask import Blueprint
admin_bp = Blueprint('admin', __name__)

from .auth import login
from .question_practice import question
from .manage_course import  enroll_course
from .mock_test import test_details_insert,test_feedback,user_test_log
from .manage_content import content_show,content_store
from .manage_purchase import purchase_handle