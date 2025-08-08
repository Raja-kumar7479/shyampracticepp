import logging
from flask import render_template, request, flash, redirect, url_for, session, jsonify
from admin.manage_mock_test.test_details_db import UserOperation
from extensions import admin_login_required
from admin import admin_bp
import math

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

user_op = UserOperation()

@admin_bp.route('/manage_test_logs')
@admin_login_required
def manage_test_logs():
    try:
        admin_email = session.get('admin_email', 'UnknownAdmin')
        logger.info(f"Admin [{admin_email}] accessed user test log page.")
        unique_attempts_count = user_op.count_unique_test_attempts()
        return render_template("admin/manage_mock_test/user_test_log.html", unique_attempts_count=unique_attempts_count)
    except Exception as e:
        logger.exception(f"Admin [{admin_email}] failed to load test logs page.")
        flash("An error occurred while loading the page.", "admin_error")
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/get_test_log_data', methods=['GET'])
@admin_login_required
def get_test_log_data():
    try:
        admin_email = session.get('admin_email', 'UnknownAdmin')
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        logger.info(f"Admin [{admin_email}] fetching user test log data for page {page}.")

        test_logs, total = user_op.get_selected_user_test_logs(page, per_page)
        total_pages = math.ceil(total / per_page)

        return jsonify({
            'test_logs': test_logs,
            'total_pages': total_pages,
            'current_page': page,
            'total_records': total
        })
    except Exception as e:
        logger.exception(f"Admin [{admin_email}] failed to fetch user test log data.")
        return jsonify({'error': 'Failed to fetch data'}), 500

@admin_bp.route('/get_unique_test_attempts_count', methods=['GET'])
@admin_login_required
def get_unique_test_attempts_count():
    admin_email = session.get('admin_email', 'UnknownAdmin')
    try:
        count = user_op.count_unique_test_attempts()
        logger.info(f"Admin [{admin_email}] fetched unique test attempts count: {count}")
        return jsonify({"unique_attempts_count": count})
    except Exception as e:
        logger.exception(f"Admin [{admin_email}] failed to fetch unique test attempts count.")
        return jsonify({"error": "Failed to fetch count"}), 500
