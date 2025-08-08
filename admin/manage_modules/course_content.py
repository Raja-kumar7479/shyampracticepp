import os
import logging
from decimal import Decimal
from flask import (
    flash, jsonify, redirect, render_template, request, url_for, session
)
from werkzeug.utils import secure_filename
from admin.manage_modules.content_db import UserOperation
from extensions import admin_login_required
from admin.auth.admin_utils import verify_password
from admin import admin_bp

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

user_op = UserOperation()
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@admin_bp.route('/manage_course_content', methods=['GET', 'POST'])
@admin_login_required
def manage_course_content():
    admin_email = session.get('admin_email', 'Unknown')
    admin_role = session.get('admin_role', 'default')

    try:
        if request.method == 'POST':
            code = request.form.get('code', '').strip()
            name = request.form.get('name', '').strip()
            stream = request.form.get('stream', '').strip()
            section = request.form.get('section', '').strip()
            title = request.form.get('title', '').strip()
            subtitle = request.form.get('subtitle', '').strip()
            details = request.form.get('details', '').strip()
            label = request.form.get('label', '').strip()
            status = request.form.get('status', '').strip()
            validity_str = request.form.get('validity_expires_at', '').strip()
            preview_url = request.form.get('preview_url', '').strip()

            if not all([code, name, stream, section, title, label, status]):
                flash("All fields except Subtitle, Details, and Validity are required.", "admin_error")
                return redirect(url_for('admin.manage_course_content'))

            price = 0.00
            validity_expires_at = None
            if label == 'Paid':
                try:
                    price = float(request.form.get('price', 0.00))
                    if price <= 0:
                        flash("Price must be a positive number for Paid content.", "admin_error")
                        return redirect(url_for('admin.manage_course_content'))
                    if validity_str:
                        validity_expires_at = validity_str
                except (ValueError, TypeError):
                    flash("Invalid price format. Please enter a valid number.", "admin_error")
                    return redirect(url_for('admin.manage_course_content'))
            
            image_url = ''
            if 'image_file' in request.files:
                file = request.files['image_file']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    image_url = os.path.join('uploads', filename).replace('\\', '/')

            result = user_op.insert_content(code, name, stream, title, subtitle, price, details, label, status, image_url, section, preview_url, validity_expires_at)
            
            if result:
                logger.info(f"ADMIN ACTION by {admin_email}: Inserted new content '{title}' for course '{code}'.")
                flash(f"Content '{title}' was added successfully!", "admin_success")
            else:
                logger.error(f"ADMIN ACTION by {admin_email}: Database error on content insertion for '{title}'.")
                flash("Failed to add content due to a database error. Please try again.", "admin_error")

            return redirect(url_for('admin.manage_course_content'))

        all_courses = user_op.get_all_courses()
        section_options = user_op.get_enum_values('course_content', 'section')
        
        return render_template(
            "admin/manage_modules/course_content.html", 
            all_courses=all_courses,
            section_options=section_options,
            admin_role=admin_role
        )

    except Exception as e:
        logger.exception(f"ADMIN ACTION by {admin_email}: Unhandled exception in 'manage_course_content'. Error: {e}")
        flash("A critical server error occurred. Please check the logs.", "admin_error")
        return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/get_content_for_course/<string:course_code>', methods=['GET'])
@admin_login_required
def get_content_for_course(course_code):
    try:
        contents = user_op.get_courses_by_code(course_code)
        for content in contents:
            if isinstance(content.get('price'), Decimal):
                content['price'] = float(content['price'])
            if content.get('validity_expires_at'):
                content['validity_expires_at'] = content['validity_expires_at'].strftime('%Y-%m-%dT%H:%M')
        return jsonify(contents)
    except Exception as e:
        logger.exception(f"API CALL Failed to fetch content for '{course_code}'. Error: {e}")
        return jsonify({"error": "Could not retrieve content due to a server error."}), 500

def is_owner_and_password_valid(email, password):
    if not password:
        return False, "Password confirmation is required."
    
    admin_user = user_op.get_admin_by_email(email)
    if not admin_user:
        return False, "Admin user not found."
    
    # Corrected line using the key from your debug output
    stored_password_hash = admin_user['password']
    
    if not verify_password(password, stored_password_hash):
        return False, "Invalid password."
    return True, "Validation successful."\
    
@admin_bp.route('/delete_content/<int:content_id>', methods=['POST'])
@admin_login_required
def delete_content(content_id):
    admin_email = session.get('admin_email')
    admin_role = session.get('admin_role')

    if admin_role != 'owner':
        return jsonify({"success": False, "message": "Permission Denied. You must be an owner."}), 403

    password = request.json.get('password')
    is_valid, message = is_owner_and_password_valid(admin_email, password)
    if not is_valid:
        return jsonify({"success": False, "message": message}), 401
        
    try:
        if user_op.delete_content(content_id):
            logger.info(f"ADMIN ACTION by {admin_email}: Successfully deleted content ID {content_id}.")
            return jsonify({"success": True, "message": "Content has been deleted."})
        else:
            return jsonify({"success": False, "message": "Deletion failed. Content not found."}), 404
    except Exception as e:
        logger.exception(f"Server error during deletion of content ID {content_id}. Error: {e}")
        return jsonify({"success": False, "message": "A server error occurred."}), 500

@admin_bp.route('/update_content_field/<int:content_id>', methods=['POST'])
@admin_login_required
def update_content_field(content_id):
    admin_email = session.get('admin_email')
    admin_role = session.get('admin_role')

    if admin_role != 'owner':
        return jsonify({"success": False, "message": "Permission Denied. You must be an owner."}), 403
    
    if not request.is_json:
        return jsonify({"success": False, "message": "Invalid request."}), 400

    data = request.get_json()
    field, value, password = data.get('field'), data.get('value'), data.get('password')
    
    is_valid, message = is_owner_and_password_valid(admin_email, password)
    if not is_valid:
        return jsonify({"success": False, "message": message}), 401

    forbidden_fields = ['code', 'section', 'id', 'section_id']
    if field in forbidden_fields:
        return jsonify({"success": False, "message": f"The '{field}' field cannot be updated directly."}), 400
    
    try:
        current_content = user_op.get_content_by_id(content_id)
        if not current_content:
            return jsonify({"success": False, "message": "Content not found."}), 404
        
        content_dict = dict(current_content)
        content_dict[field] = value if value else None
        
        if field == 'label':
            if value == 'Free':
                content_dict['price'] = 0.00
                content_dict['validity_expires_at'] = None
            elif value == 'Paid':
                 pass
                
        if field == 'price':
            content_dict['price'] = float(value) if value else 0.00
            
        if field == 'preview_url' and value:
            # If a file is uploaded, handle it here
            if 'preview_file' in request.files:
                file = request.files['preview_file']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    content_dict['preview_url'] = url_for('static', filename=os.path.join('uploads', filename).replace('\\', '/'))
            else:
                 content_dict['preview_url'] = value
        else:
            content_dict['preview_url'] = None # If value is empty, remove the URL
                
        success = user_op.update_content(
            content_id, content_dict['name'], content_dict['stream'],
            content_dict['title'], content_dict['subtitle'], content_dict['price'],
            content_dict['details'], content_dict['label'], content_dict['status'],
            content_dict['image_url'], content_dict.get('preview_url'), content_dict.get('validity_expires_at')
        )

        if not success:
            return jsonify({"success": False, "message": "Database update failed."}), 500
        
        updated = user_op.get_content_by_id(content_id)
        logger.info(f"ADMIN ACTION by {admin_email}: Updated field '{field}' for content ID {content_id}.")
        
        updated_value = updated.get(field)
        if isinstance(updated_value, Decimal):
            updated_value = float(updated_value)
        elif field == 'validity_expires_at' and updated_value:
            updated_value = updated_value.strftime('%Y-%m-%dT%H:%M')

        return jsonify({
            "success": True, 
            "message": "Update successful.",
            "updated_field_value": updated_value,
            "new_price": float(updated['price']),
        })

    except Exception as e:
        logger.exception(f"Exception while updating content field for ID {content_id}. Error: {e}")
        return jsonify({"success": False, "message": "Server error during update."}), 500

@admin_bp.route('/update_content_image/<int:content_id>', methods=['POST'])
@admin_login_required
def update_content_image(content_id):
    admin_email = session.get('admin_email', 'Unknown')
    try:
        content = user_op.get_content_by_id(content_id)
        if not content: return jsonify({"success": False, "message": "Content not found."}), 404

        file = request.files.get('image_file')
        if not file or not file.filename: return jsonify({"success": False, "message": "No file uploaded."}), 400
        
        if content.get('image_url'):
            old_path = os.path.join('static', content['image_url'])
            if os.path.exists(old_path): os.remove(old_path)
        
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        new_url = os.path.join('uploads', filename).replace('\\', '/')

        if user_op.update_content_image(content_id, new_url):
            logger.info(f"ADMIN ACTION by {admin_email}: Updated image for content ID {content_id}.")
            return jsonify({"success": True, "message": "Image updated successfully.", "new_image_url": url_for('static', filename=new_url)})
        return jsonify({"success": False, "message": "Failed to update image link in database."}), 500

    except Exception as e:
        logger.exception(f"ADMIN ACTION by {admin_email}: Exception during image update for content ID {content_id}. Error: {e}")
        return jsonify({"success": False, "message": "Internal server error during image update."}), 500

@admin_bp.route('/delete_content_image/<int:content_id>', methods=['POST'])
@admin_login_required
def delete_content_image(content_id):
    admin_email = session.get('admin_email', 'Unknown')
    try:
        content = user_op.get_content_by_id(content_id)
        if not content or not content.get('image_url'):
            return jsonify({"success": False, "message": "Content or image not found."}), 404
        
        os.remove(os.path.join('static', content['image_url']))

        if user_op.update_content_image(content_id, ''):
            logger.info(f"ADMIN ACTION by {admin_email}: Deleted image for content ID {content_id}.")
            return jsonify({"success": True, "message": "Image deleted."})
        return jsonify({"success": False, "message": "Failed to update database after image deletion."}), 500
    except Exception as e:
        logger.exception(f"ADMIN ACTION by {admin_email}: Error deleting image for content ID {content_id}. Error: {e}")
        return jsonify({"success": False, "message": "Internal error during image deletion."}), 500