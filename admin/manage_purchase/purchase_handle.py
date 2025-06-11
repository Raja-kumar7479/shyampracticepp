
from flask import flash, jsonify,redirect, render_template, request, session, url_for
from admin.manage_purchase.purchase_db import PurchaseOperation
from admin import admin_bp
from flask_mail import Mail
from collections import defaultdict

mail = Mail()

purchase_op = PurchaseOperation()

@admin_bp.route('/manage_purchases', methods=['GET'])
def manage_purchases():
    return render_template('admin/manage_purchase/purchase_handler.html')

@admin_bp.route('/get_purchases', methods=['GET'])
def get_purchases():
    status = request.args.get('status')
    if status not in ['Paid', 'Pending']:
        return jsonify({"error": "Invalid status provided"}), 400

    purchases = purchase_op.get_purchases_by_status(status)
    return jsonify(purchases)

@admin_bp.route('/delete_purchase/<int:purchase_id>', methods=['DELETE'])
def delete_purchase(purchase_id):
    success = purchase_op.delete_purchase_by_id(purchase_id)
    if success:
        return jsonify({"message": "Purchase deleted successfully"}), 200
    else:
        return jsonify({"error": "Failed to delete purchase or purchase not found/not pending"}), 400
