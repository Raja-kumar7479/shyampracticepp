from decimal import Decimal
from flask import flash, jsonify, redirect, render_template, request, session, url_for, Blueprint
from admin.manage_content.content_db import UserOperation
from extensions import admin_login_required
from admin import admin_bp

user_op = UserOperation()


@admin_bp.route('/manage_content', methods=['GET', 'POST'])
@admin_login_required
def manage_content():
    if request.method == 'POST':
        code = request.form['code'].strip()
        section = request.form['section'].strip()
        title = request.form['title'].strip()
        subtitle = request.form.get('subtitle', '').strip()
        details = request.form.get('details', '').strip()
        label = request.form['label'].strip()
        status = request.form['status'].strip()
        image_url = request.form.get('image_url', '').strip()

        price = 0.00
        if label == 'Paid':
            try:
                price = float(request.form.get('price', 0.00))
                if price <= 0:
                    flash("Price must be greater than 0 for Paid content.", "error")
                    return redirect(url_for('admin.manage_content'))
            except ValueError:
                flash("Invalid price value.", "error")
                return redirect(url_for('admin.manage_content'))

        if not all([code, section, title, label, status]):
            flash("Missing required fields for content insertion.", "error")
            return redirect(url_for('admin.manage_content'))

        insert_result = user_op.insert_content(code, title, subtitle, price, details, label, status, image_url, section)

        if insert_result is False:
            flash(f"A FREE entry already exists for Course Code '{code}' and Section '{section}'. Only one free entry allowed per section.", "error")
        elif insert_result:
            flash(f"Content '{title}' added successfully!", "success")
        else:
            flash("Failed to add content. Please try again.", "error")

        return redirect(url_for('admin.manage_content'))

    all_content = user_op.get_all_content_entries()
    return render_template("admin/manage_content/content_store.html", contents=all_content)



@admin_bp.route('/update_content_field/<int:content_id>', methods=['POST'])
@admin_login_required
def update_content_field(content_id):
    if request.is_json:
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        
        content = user_op.get_content_by_id(content_id)
        if not content:
            return jsonify({"success": False, "message": "Content not found."}), 404

        allowed_fields = ['code', 'title', 'subtitle', 'price', 'details', 'label', 'status', 'image_url', 'section']
        if field not in allowed_fields:
            return jsonify({"success": False, "message": "Invalid field for update."}), 400

        current_content = dict(content)

        if field == 'label':
            current_content[field] = value
            if value == 'Free':
                current_content['price'] = 0.00
            elif value == 'Paid':
                new_price_from_frontend = data.get('price') 
                if new_price_from_frontend is None:
                     return jsonify({"success": False, "message": "Price is required when changing label to 'Paid'."}), 400
                try:
                    new_price_from_frontend = float(new_price_from_frontend)
                    if new_price_from_frontend <= 0:
                        return jsonify({"success": False, "message": "Price must be greater than 0 for Paid content."}), 400
                    current_content['price'] = new_price_from_frontend
                except (ValueError, TypeError):
                    return jsonify({"success": False, "message": "Invalid price value provided for Paid content."}), 400
        elif field == 'price':
            try:
                value = float(value)
                if current_content['label'] == 'Paid' and value <= 0:
                    return jsonify({"success": False, "message": "Price must be greater than 0 for Paid content."}), 400
                current_content[field] = value
            except ValueError:
                return jsonify({"success": False, "message": "Invalid price value."}), 400
        else:
            current_content[field] = value

        update_success = user_op.update_content(
            content_id,
            current_content['code'],
            current_content['title'],
            current_content['subtitle'],
            current_content['price'],
            current_content['details'],
            current_content['label'],
            current_content['status'],
            current_content['image_url'],
            current_content['section'],
            current_content['section_id']
        )

        if update_success:
            updated_content_row = user_op.get_content_by_id(content_id)
            if updated_content_row:
                try:
                    
                    new_price_value = float(updated_content_row['price']) if isinstance(updated_content_row['price'], Decimal) else updated_content_row['price']
                    
                    updated_field_display_value = updated_content_row[field]
                    if field == 'price' and isinstance(updated_field_display_value, Decimal):
                        updated_field_display_value = float(updated_field_display_value)
                    elif field == 'price': # ensure it's a float if it wasn't Decimal
                        updated_field_display_value = float(updated_field_display_value)

                    return jsonify({
                        "success": True,
                        "message": "Content updated successfully.",
                        "updated_field_value": updated_field_display_value,
                        "new_price": new_price_value,
                        "new_section_id": updated_content_row['section_id']
                    })
                except Exception as json_err:
                    user_op.logger.exception(f"ERROR: Failed to jsonify response for content_id {content_id}. Data: {updated_content_row}")
                    return jsonify({"success": False, "message": "Internal server error during response formatting."}), 500
            else:
                user_op.logger.error(f"ERROR: Content updated successfully but failed to re-fetch content for ID {content_id}.")
                return jsonify({"success": False, "message": "Content updated, but failed to re-fetch details."}), 500
        else:
            user_op.logger.error(f"ERROR: Failed to update content for ID {content_id} in DB.")
            return jsonify({"success": False, "message": "Failed to update content due to server error or restriction."}), 500
    return jsonify({"success": False, "message": "Invalid request."}), 400


@admin_bp.route('/delete_content/<int:content_id>', methods=['POST'])
@admin_login_required
def delete_content(content_id):
    if user_op.delete_content(content_id):
        return jsonify({"success": True, "message": "Content deleted successfully."})
    else:
        return jsonify({"success": False, "message": "Failed to delete content. It might not exist."}), 404
