from flask import Flask, render_template, request, jsonify
from admin.mock_test.test_details_db import UserOperation
from extensions import admin_login_required
from admin import admin_bp

user_op = UserOperation()


@admin_bp.route('/manage_feedback')
@admin_login_required
def manage_feedback():
    all_feedback = user_op.get_all_feedback_entries()
    return render_template("admin/mock_test/manage_feedback.html", feedbacks=all_feedback)

@admin_bp.route('/truncate_feedback', methods=['POST'])
@admin_login_required
def truncate_feedback():
    if user_op.truncate_all_feedback():
        return jsonify({"success": True, "message": "All feedback data deleted successfully."})
    else:
        return jsonify({"success": False, "message": "Failed to delete feedback data."}), 500
