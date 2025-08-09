import os
import logging
from datetime import timedelta

from flask import Flask, jsonify, render_template, session
from flask_session import Session
from flask_mail import Mail
from dotenv import load_dotenv

import mysql.connector
from mysql.connector import pooling, Error
from config import Config
from extensions import init_limiter

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', filename='app.log')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

db_pool = None
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="main_app_pool",
        pool_size=5,
        pool_reset_session=True,
        host=Config.DATABASE_HOST,
        user=Config.DATABASE_USER,
        password=Config.DATABASE_PASSWORD,
        database=Config.DATABASE_NAME,
        charset='utf8mb4'
    )
    logger.info("Successfully created shared database connection pool.")
except Error as e:
    logger.critical(f"FATAL: Could not create the shared database pool. The application will not work. Error: {e}")
    db_pool = None

#Admin-side Database Operations
from admin.auth.admin_db import UserOperation as AdminDb
from admin.manage_modules.content_db import UserOperation as ContentUserOperation
from admin.manage_course.enroll_course_db import UserOperation as EnrollUserOperation
from admin.manage_mock_test.test_details_db import UserOperation as MockTestUserOperation
from admin.manage_purchase.purchase_db import PurchaseOperation
from admin.manage_qpractice.practice_paper_db import PaperOperation

#User-side Database Operations
from users.auth.user_db import UserOperation as UserAuthOp
from users.checkout.user_db import UserOperation as UserCheckoutOp
from users.enroll.user_db import UserOperation as UserEnrollOp
from users.mock_test.content_dashboard.content_db import ContentOperation as UserContentOp
from users.mock_test.handler_db.user_db import UserOperation as UserMockTestHandlerOp
from users.mock_test.handler_db.result_handler_db import ResultHandler
from users.mock_test.handler_db.test_handler_db import TestHandler
from users.question_practice.user_db import UserOperation as UserQuestionPracticeOp


if db_pool:
    # Instantiate Admin-side objects
    admin_db_op = AdminDb()
    content_op = ContentUserOperation()
    enroll_op = EnrollUserOperation()
    mock_test_op = MockTestUserOperation()
    purchase_op = PurchaseOperation()
    paper_op = PaperOperation()

    # Instantiate User-side objects
    user_auth_op = UserAuthOp()
    user_checkout_op = UserCheckoutOp()
    user_enroll_op = UserEnrollOp()
    user_content_op = UserContentOp()
    user_mock_test_handler_op = UserMockTestHandlerOp()
    result_handler_op = ResultHandler()
    test_handler_op = TestHandler()
    user_question_practice_op = UserQuestionPracticeOp()

else:
    # Set all to None if the pool failed
    admin_db_op, content_op, enroll_op, mock_test_op, purchase_op, paper_op = (None,) * 6
    user_auth_op, user_checkout_op, user_enroll_op, user_content_op, user_mock_test_handler_op, result_handler_op, test_handler_op, user_question_practice_op = (None,) * 8
    logger.error("Database operation objects could not be created because the pool is not available.")

Session(app)
mail = Mail(app)
init_limiter(app)

from admin import admin_bp
from users import users_bp

app.register_blueprint(admin_bp)
app.register_blueprint(users_bp)

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)

@app.after_request
def add_security_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    return render_template('users/index/index.html')

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}")
    return jsonify({"error": "500 Internal Server Error", "message": "An internal error occurred."}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "404 Not Found", "message": "The requested URL was not found."}), 404

if __name__ == '__main__':
    app.run(debug=False)
