from flask import Flask, render_template, request, jsonify
from admin.mock_test.test_details_db import UserOperation
from extensions import admin_login_required
from admin import admin_bp

user_op = UserOperation()


@admin_bp.route('/manage_test_logs')
@admin_login_required
def manage_test_logs():
    test_logs = user_op.get_selected_user_test_logs()
    # Initial count is fetched here, but subsequent updates will be via AJAX
    unique_attempts_count = user_op.count_unique_test_attempts() 
    return render_template("admin/mock_test/user_test_log.html",
                           test_logs=test_logs,
                           unique_attempts_count=unique_attempts_count)

@admin_bp.route('/get_unique_test_attempts_count', methods=['GET'])
def get_unique_test_attempts_count():
    count = user_op.count_unique_test_attempts()
    return jsonify({"unique_attempts_count": count})