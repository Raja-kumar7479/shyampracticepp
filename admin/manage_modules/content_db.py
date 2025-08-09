import mysql.connector
from mysql.connector import Error
from app import db_pool
import logging
import uuid
import os
from decimal import Decimal

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='app.log')

class UserOperation:
    def __init__(self):
        if db_pool is None:
            raise Exception("Database connection pool is not initialized.")

    def _get_connection(self):
        return db_pool.get_connection()

    def get_admin_by_email(self, email):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(buffered=True, dictionary=True)
            query = "SELECT * FROM auth_admin WHERE email = %s"
            cursor.execute(query, (email,))
            return cursor.fetchone()
        except Exception as e:
            logger.exception(f"Error fetching admin by email: {email}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def generate_unique_section_id(self, code, section, label):
        unique_part = uuid.uuid4().hex[:16]
        clean_code = code.lower().strip()
        clean_label = label.lower().strip()
        clean_section = section.lower().replace(' ', '').strip()
        return f"{clean_code}{clean_label}{clean_section}{unique_part}"

    def insert_content(self, code, name, stream, title, subtitle, price, details, label, status, image_url, section, preview_url, validity_expires_at=None):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(buffered=True)
            section_id = self.generate_unique_section_id(code, section, label)
            query = """
                INSERT INTO course_content
                (code, name, stream, title, subtitle, price, details, label, status, image_url, section, section_id, preview_url, validity_expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (code, name, stream, title, subtitle, price, details, label, status, image_url, section, section_id, preview_url, validity_expires_at)
            cursor.execute(query, params)
            conn.commit()
            logger.info(f"Successfully inserted new content '{title}' with ID {cursor.lastrowid}.")
            return cursor.lastrowid
        except Exception as e:
            logger.exception(f"Error inserting new content for code {code}. Error: {e}")
            if conn: conn.rollback()
            return None
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def update_content(self, content_id, name, stream, title, subtitle, price, details, label, status, image_url, preview_url, validity_expires_at=None):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(buffered=True)
            query = """
                UPDATE course_content SET
                name = %s, stream = %s, title = %s, subtitle = %s, price = %s, details = %s,
                label = %s, status = %s, image_url = %s, preview_url = %s, validity_expires_at = %s
                WHERE id = %s
            """
            params = (name, stream, title, subtitle, price, details, label, status, image_url, preview_url, validity_expires_at, content_id)
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Error updating content with ID {content_id}. Rolling back. Error: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def get_content_by_id(self, content_id):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = "SELECT * FROM course_content WHERE id = %s"
            cursor.execute(query, (content_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.exception(f"Error fetching content with ID {content_id}. Error: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def get_courses_by_code(self, code):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = """
                SELECT * FROM course_content
                WHERE code = %s
                ORDER BY
                    FIELD(section, 'hnotes', 'mock test', 'vlecture', 'jcommunity'),
                    FIELD(label, 'Free', 'Paid'),
                    created_at DESC
            """
            cursor.execute(query, (code,))
            return cursor.fetchall()
        except Exception as e:
            logger.exception(f"Error fetching course content for code '{code}'. Error: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def delete_content(self, content_id):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            content = self.get_content_by_id(content_id)
            if content and content.get('image_url'):
                try:
                    image_path_native = os.path.join('static', content['image_url'])
                    if os.path.exists(image_path_native):
                        os.remove(image_path_native)
                        logger.info(f"Successfully deleted physical image file: {image_path_native}")
                except OSError as e:
                    logger.error(f"Error removing image file {image_path_native}: {e}")
            delete_cursor = conn.cursor()
            query = "DELETE FROM course_content WHERE id = %s"
            delete_cursor.execute(query, (content_id,))
            conn.commit()
            return delete_cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Error deleting content with ID {content_id}. Error: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if 'delete_cursor' in locals() and delete_cursor: delete_cursor.close()
            if cursor: cursor.close()
            if conn: conn.close()
            
    def get_all_courses(self):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = "SELECT code, name FROM courses ORDER BY name ASC"
            cursor.execute(query)
            logger.info("Successfully fetched all courses from the database.")
            return cursor.fetchall()
        except Exception as e:
            logger.exception(f"FATAL: Could not fetch courses from database. Error: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
            
    def get_distinct_course_codes(self):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = "SELECT code, name FROM courses ORDER BY name ASC"
            cursor.execute(query)
            logger.info("Successfully fetched distinct course codes from the database.")
            return cursor.fetchall()
        except Exception as e:
            logger.exception(f"FATAL: Could not fetch distinct course codes from database. Error: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def get_enum_values(self, table_name, column_name):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = f"SHOW COLUMNS FROM `{table_name}` LIKE %s"
            cursor.execute(query, (column_name,))
            result = cursor.fetchone()
            if result and 'Type' in result:
                column_type = result['Type']
                if isinstance(column_type, bytes):
                    column_type = column_type.decode('utf-8')
                if column_type.startswith("enum("):
                    enum_values = column_type[len("enum("):-1].replace("'", "").split(',')
                    return enum_values
            return []
        except Exception as e:
            logger.exception(f"Error fetching ENUM values for {table_name}.{column_name}. Error: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def update_content_image(self, content_id, image_url):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(buffered=True)
            query = "UPDATE course_content SET image_url = %s WHERE id = %s"
            cursor.execute(query, (image_url, content_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Error updating image URL for content ID {content_id}. Error: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    
    def delete_expired_content(self):
        conn = None
        deleted_rows = 0
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            query = "DELETE FROM course_content WHERE validity_expires_at IS NOT NULL AND validity_expires_at <= NOW()"
            cursor.execute(query)
            deleted_rows = cursor.rowcount
            conn.commit()
            cursor.close()
        except mysql.connector.Error as err:
            logger.error(f"Database error during scheduled cleanup: {err}")
            if conn: conn.rollback()
        finally:
            if conn and conn.is_connected():
                conn.close()
        return deleted_rows
    
    def get_questions_by_code(self, code):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM practice_questions WHERE code = %s ORDER BY id DESC"
            cursor.execute(query, (code,))
            return cursor.fetchall()
        except Exception as e:
            logger.exception(f"Error fetching practice questions for code '{code}'. Error: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def get_notes_section_ids(self):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT section_id, title, code FROM course_content WHERE section = 'hnotes' ORDER BY created_at DESC"
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            logger.exception(f"Error fetching notes section IDs: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def get_code_by_section_id(self, section_id):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT code FROM course_content WHERE section_id = %s"
            cursor.execute(query, (section_id,))
            result = cursor.fetchone()
            return result['code'] if result else None
        except Exception as e:
            logger.exception(f"Error fetching code for section ID {section_id}: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def insert_note(self, test_id, code, note_type, heading, sub_heading, title, sub_title, file_path):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO notes_content (test_id, code, type, heading, sub_heading, title, sub_title, file_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (test_id, code, note_type, heading, sub_heading, title, sub_title, file_path))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.exception(f"Error inserting note: {e}")
            if conn: conn.rollback()
            return None
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
            
    def get_note_by_id(self, note_id):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM notes_content WHERE id = %s"
            cursor.execute(query, (note_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.exception(f"Error fetching note by ID {note_id}: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
            
    def get_notes_by_criteria(self, test_id, code, note_type):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM notes_content WHERE test_id = %s AND code = %s AND type = %s"
            cursor.execute(query, (test_id, code, note_type))
            return cursor.fetchall()
        except Exception as e:
            logger.exception(f"Error fetching notes by criteria: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
            
    def delete_note_by_id(self, note_id):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            query = "DELETE FROM notes_content WHERE id = %s"
            cursor.execute(query, (note_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Error deleting note by ID {note_id}: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def get_distinct_headings(self, test_id, code, note_type):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT DISTINCT heading FROM notes_content WHERE test_id = %s AND code = %s AND type = %s"
            cursor.execute(query, (test_id, code, note_type))
            return [row['heading'] for row in cursor.fetchall()]
        except Exception as e:
            logger.exception(f"Error fetching distinct headings: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
            
    def get_distinct_sub_headings(self, test_id, code, note_type, heading):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT DISTINCT sub_heading FROM notes_content WHERE test_id = %s AND code = %s AND type = %s AND heading = %s"
            cursor.execute(query, (test_id, code, note_type, heading))
            return [row['sub_heading'] for row in cursor.fetchall()]
        except Exception as e:
            logger.exception(f"Error fetching distinct sub-headings: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def get_course_section_details(self, section_id):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT label, title FROM course_content WHERE section_id = %s LIMIT 1"
            cursor.execute(query, (section_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.exception(f"Error fetching course section details for section_id {section_id}: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    
    def get_notes_for_display(self, test_id):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM notes_content WHERE test_id = %s ORDER BY heading, sub_heading, title, id"
            cursor.execute(query, (test_id,))
            return cursor.fetchall()
        except Exception as e:
            logger.exception(f"Error fetching notes for display by test_id: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def insert_question(self, code, section, title):
        """Inserts a new practice question into the database."""
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            query = "INSERT INTO practice_questions (code, section, title) VALUES (%s, %s, %s)"
            cursor.execute(query, (code, section, title))
            conn.commit()
            logger.info(f"Successfully inserted practice question '{title}' with ID {cursor.lastrowid}.")
            return cursor.lastrowid
        except Exception as e:
            logger.exception(f"Error inserting practice question for code {code}. Error: {e}")
            if conn: conn.rollback()
            return None
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    
    def get_question_by_id(self, question_id):
        """Fetches a single practice question by its ID."""
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM practice_questions WHERE id = %s"
            cursor.execute(query, (question_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.exception(f"Error fetching practice question with ID {question_id}. Error: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    
    def update_question_field(self, question_id, field, value):
        """Updates a specific field of a practice question."""
        conn = None
        cursor = None
        # Whitelist of editable fields to prevent SQL injection
        allowed_fields = ['title', 'section']
        if field not in allowed_fields:
            logger.warning(f"Attempt to update a non-allowed field '{field}' for question ID {question_id}.")
            return False
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Safely format the query
            query = f"UPDATE practice_questions SET {field} = %s WHERE id = %s"
            cursor.execute(query, (value, question_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Error updating question ID {question_id}. Error: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    def delete_question(self, question_id):
        """Deletes a practice question from the database."""
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            query = "DELETE FROM practice_questions WHERE id = %s"
            cursor.execute(query, (question_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Error deleting question ID {question_id}. Error: {e}")
            if conn: conn.rollback()
            return False
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

