import logging
import mysql.connector
from database_pool import db_pool

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class UserOperation:
    def __init__(self):
        if db_pool is None:
            raise Exception("Database connection pool is not initialized.")

    def get_connection(self):
        return db_pool.get_connection()

    def fetch_one(self, query, params=None):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchone()
        except mysql.connector.Error as e:
            logger.error(f"Database error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def fetch_all(self, query, params=None):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchall()
        except mysql.connector.Error as e:
            logger.error(f"Database error: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_query(self, query, params=None):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(buffered=True)
            cursor.execute(query, params or ())
            conn.commit()
        except mysql.connector.Error as e:
            logger.error(f"Database error: {e}")
            if conn:
                conn.rollback()  
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    # ... (all other UserOperation methods, like get_user_unique_code, get_user_by_email, etc., would follow here) ...
    def get_user_unique_code(self, email, course_code):
        try:
            query = "SELECT unique_code FROM enrollment WHERE email = %s AND code = %s"
            result = self.fetch_one(query, (email, course_code))
            return result['unique_code'] if result else None
        except Exception as e:
            logger.exception("Error fetching user unique code")
            return None

    def get_user_by_email(self, email):
        try:
            query = "SELECT username FROM auth WHERE email = %s"
            return self.fetch_one(query, (email,))
        except Exception as e:
            logger.exception("Error fetching user by email")
            return None

    def validate_test_credentials(self, test_key, submitted_key):
        try:
            query = "SELECT id FROM test_description WHERE test_key = %s AND test_key = %s"
            result = self.fetch_one(query, (test_key, submitted_key))
            return result is not None
        except Exception as e:
            logger.exception(f"Error validating credentials for test_key {test_key}")
            return False

    def check_test_already_taken(self, email, test_key):
        try:
            query = "SELECT id FROM user_test_log WHERE email = %s AND test_key = %s AND status = 'completed'"
            result = self.fetch_one(query, (email, test_key))
            return result is not None
        except Exception as e:
            logger.exception(f"Error checking if test {test_key} was taken by {email}")
            return False

    def get_test_status_for_user(self, email, test_key):
        try:
            query = "SELECT status, start_time FROM user_test_log WHERE email = %s AND test_key = %s ORDER BY start_time DESC LIMIT 1"
            result = self.fetch_one(query, (email, test_key))
            return result if result else {'status': 'not_started', 'start_time': None}
        except Exception as e:
            logger.exception(f"Error fetching test status for user {email}, test_key {test_key}")
            return {'status': 'not_started', 'start_time': None}

    def store_user_test_start(self, email, test_key, username, is_checkbox_checked=False, ready_to_begin=False):
        try:
            test_info = self.get_test_details(test_key)
            if not test_info:
                raise Exception("Test details not found for storing log.")
            
            existing_unperformed_test = self.fetch_one(
                "SELECT id FROM user_test_log WHERE email = %s AND test_key = %s AND status = 'unperformed'",
                (email, test_key)
            )
            if existing_unperformed_test:
                query = """
                    UPDATE user_test_log SET start_time = NOW(), is_checkbox_checked = %s, ready_to_begin = %s, accepted_at = NOW(), updated_at = CURRENT_TIMESTAMP
                    WHERE email = %s AND test_key = %s AND status = 'unperformed'
                """
                self.execute_query(query, (int(is_checkbox_checked), int(ready_to_begin), email, test_key))
            else:
                query = """
                    INSERT INTO user_test_log (email, test_id, test_key, username, start_time, status, attempt_number, is_checkbox_checked, ready_to_begin, accepted_at)
                    VALUES (%s, %s, %s, %s, NOW(), 'unperformed', 1, %s, %s, NOW())
                """
                self.execute_query(query, (email, test_info['test_id'], test_key, username, int(is_checkbox_checked), int(ready_to_begin)))
        except Exception as e:
            logger.exception(f"Error storing/updating test log for user {email}, test_key {test_key}")

    def complete_user_test(self, email, test_key, device_info, attempt_number=1):
        try:
            query = """
                UPDATE user_test_log SET status = 'completed', end_time = NOW(), device_info = %s, attempt_number = %s
                WHERE email = %s AND test_key = %s AND status = 'unperformed'
            """
            self.execute_query(query, (device_info, attempt_number, email, test_key))
        except Exception as e:
            logger.exception(f"Failed to update test completion for {email}, test {test_key}")

    def get_test_details(self, test_key):
        try:
            query = """
                SELECT test_id, test_key, subject_title, subject_subtitle,
                        total_questions, total_marks, total_duration_minutes
                FROM test_description
                WHERE test_key = %s
            """
            return self.fetch_one(query, (test_key,))
        except Exception as e:
            logger.exception(f"Error fetching test details for test_key: {test_key}")
            return None

    def get_all_test_questions(self, test_key):
        try:
            query = """
                SELECT id, test_id, test_key, section_id, section_name, question_number, question_type,
                        question_text, option_a, option_b, option_c, option_d,
                        correct_option, correct_marks, negative_marks, question_level, answer_text, answer_link
                FROM test_questions
                WHERE test_key = %s
                ORDER BY section_id, question_number
            """
            return self.fetch_all(query, (test_key,))
        except Exception as e:
            logger.exception(f"Error fetching all questions for test_key: {test_key}")
            return []
            
    def get_course_info_by_test_id(self, test_id):
        try:
            query = "SELECT code, stream, name FROM course_content WHERE section_id = %s"
            result = self.fetch_one(query, (test_id,))
            return result if result else None
        except Exception as e:
            logger.exception(f"Error fetching course info for test_id: {test_id}")
            return None
    
    def get_test_sections(self, test_key):
        try:
            query = """
                SELECT section_id, section_name,
                        SUM(CASE WHEN correct_marks = 1 THEN 1 ELSE 0 END) AS one_mark_questions,
                        SUM(CASE WHEN correct_marks = 2 THEN 1 ELSE 0 END) AS two_mark_questions,
                        SUM(correct_marks) AS section_total_marks
                FROM test_questions WHERE test_key = %s GROUP BY section_id, section_name ORDER BY section_id
            """
            return self.fetch_all(query, (test_key,))
        except Exception as e:
            logger.exception(f"Error fetching sections for test_key: {test_key}")
            return []

    def terminate_user_test_log(self, email, test_key):
        query = "UPDATE user_test_log SET status = 'unperformed', end_time = NOW() WHERE email = %s AND test_key = %s"
        self.execute_query(query, (email, test_key))

    def get_completed_tests_for_user(self, email, section_id):
        try:
            query = """
                SELECT 
                    tr.test_id, 
                    td.test_key, 
                    td.subject_title, 
                    td.subject_subtitle,
                    tr.submission_timestamp, 
                    tr.net_score, 
                    tr.percentage
                FROM test_result tr
                JOIN test_description td ON tr.test_key = td.test_key
                WHERE tr.email = %s AND td.test_id = %s
                ORDER BY tr.submission_timestamp DESC
            """
            return self.fetch_all(query, (email, section_id))
        except Exception as e:
            logger.exception(f"Error fetching completed tests for user {email} and section {section_id}")
            return []
            
    def get_course_code_from_test_id(self, test_id):
        try:
            query = "SELECT code,stream,name  FROM course_content WHERE section_id = %s"
            result = self.fetch_one(query, (test_id,))
            return result['code'] if result else None
        except Exception as e:
            logger.exception(f"Error fetching course code for test_id: {test_id}")
            return None