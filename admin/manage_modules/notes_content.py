import logging
import os
from flask import jsonify, render_template, request, url_for, Blueprint, session, flash
from werkzeug.utils import secure_filename
from admin.manage_modules.content_db import UserOperation
from extensions import admin_login_required
from admin import admin_bp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

user_op = UserOperation()

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@admin_bp.route('/notes_upload', methods=['GET', 'POST'])
@admin_login_required
def manage_notes_upload():
    try:
        if request.method == 'POST':
            logger.info("Received POST request to add a new note.")
            test_id = request.form.get('test_id')
            code = request.form.get('code')
            note_type = request.form.get('type')
            heading = request.form.get('heading_input') or request.form.get('heading_select')
            sub_heading = request.form.get('sub_heading_input') or request.form.get('sub_heading_select')
            title = request.form.get('title')
            sub_title = request.form.get('sub_title')
            file_url = request.form.get('file_url')
            uploaded_file = request.files.get('file_upload')

            if not all([test_id, code, note_type, heading, sub_heading, title]):
                logger.warning(f"Note submission failed due to missing fields. Form data: {request.form}")
                flash('All required fields must be filled.', 'admin_error')
                return jsonify({'success': False, 'message': 'All required fields must be filled.'}), 400

            file_path_to_db = ''
            if uploaded_file and uploaded_file.filename:
                filename = secure_filename(uploaded_file.filename)
                full_path = os.path.join(UPLOAD_FOLDER, filename)
                uploaded_file.save(full_path)
                file_path_to_db = os.path.join('uploads', filename).replace("\\", "/")
                logger.info(f"File '{filename}' saved to '{full_path}'.")
            elif file_url:
                file_path_to_db = file_url
                logger.info(f"Using file URL: {file_url}")

            note_id = user_op.insert_note(test_id, code, note_type, heading, sub_heading, title, sub_title, file_path_to_db)
            if not note_id:
                 logger.error("Database error while inserting note.")
                 flash('Database error while inserting note.', 'admin_error')
                 return jsonify({'success': False, 'message': 'Database error while inserting note.'}), 500

            new_note = user_op.get_note_by_id(note_id)

            if new_note:
                logger.info(f"Successfully added new note with ID {note_id} for Test ID {test_id}.")
                new_note['file_url'] = url_for('static', filename=new_note['file_path'], _external=False) if new_note['file_path'] and not new_note['file_path'].startswith('http') else new_note['file_path']
                flash('Note added successfully!', 'admin_success')
                return jsonify({'success': True, 'note': new_note})
            else:
                logger.error(f"Failed to retrieve newly created note with ID {note_id}.")
                flash('Failed to retrieve the newly created note.', 'admin_error')
                return jsonify({'success': False, 'message': 'Failed to retrieve the newly created note.'}), 500

        section_ids = user_op.get_notes_section_ids()
        type_options = user_op.get_enum_values('notes_content', 'type')
        return render_template('admin/manage_modules/notes_content.html',
                               section_ids=section_ids,
                               type_options=type_options)

    except Exception as e:
        logger.exception(f"An unexpected error occurred in manage_notes_upload: {e}")
        flash('An unexpected server error occurred.', 'admin_error')
        return jsonify({'success': False, 'message': 'An unexpected server error occurred.'}), 500
    
@admin_bp.route('/api/code_for_section/<section_id>')
@admin_login_required
def get_code_for_section(section_id):
    try:
        code = user_op.get_code_by_section_id(section_id)
        if code:
            return jsonify({'success': True, 'code': code})
        else:
            return jsonify({'success': False, 'message': 'Code not found for this section ID.'}), 404
    except Exception as e:
        logger.exception(f"Error fetching code for section ID {section_id}: {e}")
        return jsonify({'success': False, 'message': 'Server error.'}), 500

@admin_bp.route('/api/notes', methods=['GET'])
@admin_login_required
def get_notes():
    try:
        test_id = request.args.get('test_id')
        code = request.args.get('code')
        note_type = request.args.get('type')

        if not all([test_id, code, note_type]):
            return jsonify({'success': False, 'message': 'Missing required parameters.'}), 400

        notes = user_op.get_notes_by_criteria(test_id, code, note_type)

        for note in notes:
            if note.get('file_path') and not note['file_path'].startswith('http'):
                note['file_url'] = url_for('static', filename=note['file_path'], _external=False)
            else:
                note['file_url'] = note.get('file_path', '')

        return jsonify({'success': True, 'notes': notes})

    except Exception as e:
        logger.exception(f"Error fetching notes: {e}")
        return jsonify({'success': False, 'message': 'Server error while fetching notes.'}), 500
        
@admin_bp.route('/api/note/delete/<int:note_id>', methods=['POST'])
@admin_login_required
def delete_note(note_id):
    logger.info(f"Attempting to delete note with ID: {note_id}")
    try:
        note = user_op.get_note_by_id(note_id)
        if not note:
            logger.warning(f"Delete failed: Note with ID {note_id} not found.")
            return jsonify({"success": False, "message": "Note not found."}), 404

        file_path = note.get('file_path')
        if file_path and not file_path.startswith('http'):
            full_path = os.path.join('static', file_path)
            logger.info(f"Attempting to delete file: {full_path}")
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                    logger.info(f"Successfully deleted file: {full_path}")
                except OSError as e:
                    logger.exception(f"Error deleting file {full_path}: {e}")
            else:
                logger.warning(f"File not found at path, skipping deletion: {full_path}")
        
        if user_op.delete_note_by_id(note_id):
            logger.info(f"Successfully deleted note ID {note_id} from database.")
            return jsonify({"success": True, "message": "Note deleted successfully."})
        else:
            logger.error(f"Failed to delete note ID {note_id} from database.")
            return jsonify({"success": False, "message": "Database delete failed."}), 500
            
    except Exception as e:
        logger.exception(f"An unexpected error occurred while deleting note ID {note_id}: {e}")
        return jsonify({"success": False, "message": "An internal server error occurred."}), 500

@admin_bp.route('/api/notes/headings', methods=['GET'])
@admin_login_required
def get_headings():
    try:
        test_id = request.args.get('test_id')
        code = request.args.get('code')
        note_type = request.args.get('type')
        headings = user_op.get_distinct_headings(test_id, code, note_type)
        return jsonify({'success': True, 'headings': headings})
    except Exception as e:
        logger.exception(f"Error fetching distinct headings: {e}")
        return jsonify({'success': False, 'message': 'Server error.'}), 500

@admin_bp.route('/api/notes/sub_headings', methods=['GET'])
@admin_login_required
def get_sub_headings():
    try:
        test_id = request.args.get('test_id')
        code = request.args.get('code')
        note_type = request.args.get('type')
        heading = request.args.get('heading')
        sub_headings = user_op.get_distinct_sub_headings(test_id, code, note_type, heading)
        return jsonify({'success': True, 'sub_headings': sub_headings})
    except Exception as e:
        logger.exception(f"Error fetching distinct sub-headings: {e}")
        return jsonify({'success': False, 'message': 'Server error.'}), 500
