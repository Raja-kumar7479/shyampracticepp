import logging
from mysql.connector import Error
from app import db_pool

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class ContentOperation:

    def fetch_one(self, query, params=None):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Error in fetch_one: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def fetch_all(self, query, params=None):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error in fetch_all: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def execute_query(self, query, params=None):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(buffered=True)
            cursor.execute(query, params or ())
            conn.commit()
        except Error as e:
            logger.error(f"Error in execute_query: {e}")
            if conn: conn.rollback()
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_user_unique_code(self, email, course_code):
        query = "SELECT unique_code FROM enrollment WHERE email = %s AND code = %s"
        result = self.fetch_one(query, (email, course_code))
        return result['unique_code'] if result else None

    def get_course_section_details(self, section_id):
        query = "SELECT label, title FROM course_content WHERE section_id = %s LIMIT 1"
        return self.fetch_one(query, (section_id,))

    def get_mock_tests_paid(self, section_id, course_code, user_email):
        query = """
            SELECT
                c.name AS course_name, c.stream, c.label, c.code,
                td_desc.test_id, td_desc.test_key,
                td_desc.subject_title, td_desc.subject_subtitle,
                td_desc.total_questions, td_desc.total_marks,
                td_desc.total_duration_minutes,
                td_desc.created_at, td_desc.updated_at,
                COALESCE(utl.status, 'not_started') AS user_test_status,
                utl.attempt_number
            FROM course_content c
            JOIN test_description td_desc ON c.section_id = td_desc.test_id
            LEFT JOIN user_test_log utl ON td_desc.test_key = utl.test_key AND utl.email = %s
            WHERE c.section_id = %s AND c.code = %s AND c.label = 'Paid'
            ORDER BY td_desc.id
        """
        return self.fetch_all(query, (user_email, section_id, course_code))

    def get_mock_tests_free(self, section_id, course_code, user_email):
        query = """
            SELECT
                c.name AS course_name, c.stream, c.label, c.code,
                td_desc.test_id, td_desc.test_key,
                td_desc.subject_title, td_desc.subject_subtitle,
                td_desc.total_questions, td_desc.total_marks,
                td_desc.total_duration_minutes,
                td_desc.created_at, td_desc.updated_at,
                COALESCE(utl.status, 'not_started') AS user_test_status,
                utl.attempt_number
            FROM course_content c
            JOIN test_description td_desc ON c.section_id = td_desc.test_id
            LEFT JOIN user_test_log utl ON td_desc.test_key = utl.test_key AND utl.email = %s
            WHERE c.section_id = %s AND c.code = %s AND c.label = 'Free'
            ORDER BY td_desc.id
        """
        return self.fetch_all(query, (user_email, section_id, course_code))

    def get_notes_for_display(self, test_id):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT * FROM notes_content
                WHERE test_id = %s
                ORDER BY type, heading, sub_heading, title, sub_title
            """
            cursor.execute(query, (test_id,))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error fetching notes for display for test_id={test_id}: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
    
    def get_user_unique_code(self, email, course_code):
        query = "SELECT unique_code FROM enrollment WHERE email = %s AND code = %s"
        result = self.fetch_one(query, (email, course_code))
        return result['unique_code'] if result else None

    def get_section_label(self, section_id):
        query = "SELECT label FROM course_content WHERE section_id = %s"
        result = self.fetch_one(query, (section_id,))
        return result['label'] if result else None
