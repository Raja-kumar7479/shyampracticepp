import logging
from flask import jsonify, render_template, request, flash, redirect, url_for
from admin.manage_purchase.purchase_db import PurchaseOperation
from admin import admin_bp
from typing import Tuple, Any
from extensions import admin_login_required

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

purchase_op = PurchaseOperation()

@admin_bp.route('/manage_purchases', methods=['GET'])
@admin_login_required
def manage_purchases():
    try:
        return render_template('admin/manage_purchase/purchase_handler.html')
    except Exception as e:
        logger.error(f"Error rendering manage_purchases template: {e}", exc_info=True)
        flash("An internal server error occurred while loading the page.", "admin_error")
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/get_all_purchases', methods=['GET'])
@admin_login_required
def get_all_purchases() -> Tuple[Any, int]:
    try:
        logger.info("Fetching all purchase details.")
        purchases = purchase_op.get_all_purchase_details()
        return jsonify(purchases), 200
    except Exception as e:
        logger.error(f"Database error when fetching all purchases: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred while fetching data."}), 500

@admin_bp.route('/search_purchase', methods=['GET'])
@admin_login_required
def search_purchase() -> Tuple[Any, int]:
    email = request.args.get('email')
    payment_id = request.args.get('payment_id')

    if not email or not payment_id:
        logger.warning(f"Search attempt with missing parameters from IP: {request.remote_addr}")
        return jsonify({"error": "Both email and payment_id are required for search."}), 400

    try:
        logger.info(f"Searching for purchase with email: {email} and payment_id: {payment_id}")
        purchase = purchase_op.get_purchase_by_email_and_payment_id(email, payment_id)
        if purchase is None:
            return jsonify({"error": "A database error occurred."}), 500
        return jsonify(purchase), 200
    except Exception as e:
        logger.error(f"Error during purchase search for email '{email}': {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred during the search."}), 500

@admin_bp.route('/delete_purchase/<int:purchase_id>', methods=['DELETE'])
@admin_login_required
def delete_purchase(purchase_id: int) -> Tuple[Any, int]:
    if purchase_id <= 0:
        logger.warning(f"Attempt to delete purchase with invalid ID: {purchase_id}")
        return jsonify({"error": "Invalid purchase ID provided."}), 400

    try:
        logger.info(f"Attempting to delete purchase with ID: {purchase_id}")
        success = purchase_op.delete_purchase_by_id(purchase_id)

        if success:
            logger.info(f"Successfully deleted purchase ID: {purchase_id}")
            return jsonify({"message": "Purchase deleted successfully"}), 200
        else:
            logger.warning(f"Failed to delete purchase ID {purchase_id}. It may not exist or is not in a deletable state (e.g., 'Paid').")
            return jsonify({"error": "Purchase not found or it cannot be deleted."}), 404

    except Exception as e:
        logger.error(f"An unexpected error occurred while deleting purchase ID {purchase_id}: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred during deletion."}), 500

