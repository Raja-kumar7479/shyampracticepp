import logging
from flask import render_template, request, flash, redirect, url_for, session, jsonify
from admin.manage_mock_test.test_details_db import UserOperation
from extensions import admin_login_required
from admin import admin_bp
import math

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

user_op = UserOperation()

@admin_bp.route('/manage_feedback')
@admin_login_required
def manage_feedback():
    try:
        admin_email = session.get('admin_email', 'UnknownAdmin')
        logger.info(f"Admin [{admin_email}] accessed feedback management page.")
        return render_template("admin/manage_mock_test/manage_feedback.html")
    except Exception as e:
        logger.exception(f"Admin [{admin_email}] encountered an error while loading feedback page.")
        flash("An error occurred while loading the page.", "admin_error")
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/get_feedback_data', methods=['GET'])
@admin_login_required
def get_feedback_data():
    try:
        admin_email = session.get('admin_email', 'UnknownAdmin')
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        logger.info(f"Admin [{admin_email}] fetching feedback data for page {page}.")
        
        feedbacks, total = user_op.get_all_feedback_entries(page, per_page)
        
        total_pages = math.ceil(total / per_page)

        return jsonify({
            'feedbacks': feedbacks,
            'total_pages': total_pages,
            'current_page': page,
            'total_records': total
        })
    except Exception as e:
        logger.exception(f"Admin [{admin_email}] failed to fetch feedback data.")
        return jsonify({'error': 'Failed to fetch data'}), 500

@admin_bp.route('/truncate_feedback', methods=['POST'])
@admin_login_required
def truncate_feedback():
    admin_email = session.get('admin_email', 'UnknownAdmin')
    logger.info(f"Admin [{admin_email}] initiated feedback truncation.")
    try:
        if user_op.truncate_all_feedback():
            logger.info(f"Admin [{admin_email}] successfully truncated all feedback.")
            return jsonify({'success': True, 'message': 'All feedback data has been deleted.'})
        else:
            logger.warning(f"Admin [{admin_email}] failed to truncate feedback.")
            return jsonify({'success': False, 'message': 'Failed to delete feedback data.'}), 500
    except Exception as e:
        logger.exception(f"Admin [{admin_email}] encountered an exception during feedback truncation.")
        return jsonify({'success': False, 'message': 'An internal server error occurred.'}), 500
