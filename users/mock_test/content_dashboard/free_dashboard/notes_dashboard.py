from flask import abort, redirect, render_template, request, url_for, send_file, current_app, session
from collections import defaultdict
import datetime
import os
from users.mock_test.handler_db.user_db import UserOperation
from users.mock_test.content_dashboard.content_db import ContentOperation
from users.mock_test.utils_dashboard import get_user_session
from users.mock_test.handler_db.result_handler_db import ResultHandler
from users.mock_test.content_dashboard.free_dashboard.utils_dashboard import prepare_mock_test_data_free
from users.mock_test.content_dashboard.paid_dashboard.utils_dashboard import prepare_mock_test_data_paid
from users.mock_test.decorator import secure_access_required
from extensions import user_login_required
from users import users_bp
import logging

user_op = UserOperation()
content_op = ContentOperation()
result_handler = ResultHandler()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


@users_bp.route('/open/hnotes/<section_id>/<course_code>/<unique_code>')
@user_login_required
@secure_access_required(('unique_code', 'course_code'))
def open_hnotes_section(section_id, course_code, unique_code):

    username = session.get('user_username')
    email = session.get('user_email')

    if not username or not email:
        abort(403, "Session expired or invalid. Please log in again.")

    section_details = content_op.get_course_section_details(section_id)
    if not section_details:
        abort(404, "Course section not found.")

    section_label = section_details.get('label', 'Free')
    section_title = section_details.get('title', 'Notes Dashboard')

    notes = content_op.get_notes_for_display(section_id)
    
    structured_data = {}
    for note in notes:
        headings = structured_data.setdefault(note['type'], {})
        sub_headings = headings.setdefault(note['heading'], {})
        titles = sub_headings.setdefault(note['sub_heading'], {})
        
        title_key = note['title']
        if title_key not in titles:
            titles[title_key] = {'subtitles': []}

        if not note.get('sub_title'):
            titles[title_key]['main_path'] = note['file_path']
        else:
            titles[title_key]['subtitles'].append({
                'name': note['sub_title'],
                'path': note['file_path']
            })

    return render_template(
        'users/mock_test/content_dashboard/test_dashboard/notes_dashboard.html', 
        structured_data=structured_data, 
        section_label=section_label,
        section_title=section_title,
        test_id=section_id,
        username=username,   
        email=email           
    )


@users_bp.route('/view_note_file/<path:filepath>')
@user_login_required
def view_note_file(filepath):
    if '..' in filepath or filepath.startswith('/'):
        abort(404)
    
    file_path = os.path.join(current_app.static_folder, filepath)
    
    if not os.path.exists(file_path):
        abort(404)

    return send_file(file_path, as_attachment=False)
