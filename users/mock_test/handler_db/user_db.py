import logging
import mysql.connector
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class UserOperation:

    def connection(self):
        return mysql.connector.connect(
            host=Config.DATABASE_HOST,
            user=Config.DATABASE_USER,
            password=Config.DATABASE_PASSWORD,
            database=Config.DATABASE_NAME
        )

    def fetch_one(self, query, params=None):
        db = self.connection()
        cursor = db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()
            db.close()

    def fetch_all(self, query, params=None):
        db = self.connection()
        cursor = db.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
            db.close()

    def execute_query(self, query, params=None):
        db = self.connection()
        cursor = db.cursor(buffered=True)
        try:
            cursor.execute(query, params or ())
            db.commit()
        finally:
            cursor.close()
            db.close()


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

    def get_mock_tests(self, course_code, user_email): 
        try:
            query = """
                SELECT
                    sm.test_id, sm.test_code, sm.code,
                    sm.name AS course_name, sm.stream,
                    td.test_number, td.subject_title, td.subject_subtitle,
                    td.total_questions, td.total_marks AS question_marks, td.total_duration_minutes AS duration, td.year,
                    COALESCE(utl.status, 'not_started') AS user_test_status, 
                    utl.attempt_number 
                FROM test_details sm
                JOIN test_description td ON sm.test_id = td.test_id
                LEFT JOIN user_test_log utl ON sm.test_id = utl.test_id AND utl.email = %s 
                WHERE sm.code = %s AND sm.label = 'Free'
                ORDER BY td.test_number
            """
            return self.fetch_all(query, (user_email, course_code)) # Pass user_email to query
        except Exception as e:
            logger.exception("Error fetching tests for mock test")
            return []

    def get_test_details(self, test_id):
        try:
            query = """
                SELECT sm.test_code, sm.test_key, td.subject_title,
                        td.total_questions, td.total_marks, td.total_duration_minutes
                FROM test_details sm
                JOIN test_description td ON sm.test_id = td.test_id
                WHERE sm.test_id = %s
            """
            result = self.fetch_one(query, (test_id,))
            logger.debug(f"Test details for test_id {test_id}: {result}")
            return result
        except Exception as e:
            logger.exception(f"Error fetching test details for test_id: {test_id}")
            return None

    def validate_test_credentials(self, test_id, test_key, test_code):
        try:
            query = """
                SELECT test_id FROM test_details
                WHERE test_id = %s AND test_key = %s AND test_code = %s
            """
            result = self.fetch_one(query, (test_id, test_key, test_code))
            logger.debug(f"Validation result for test_id {test_id}, test_key {test_key}, test_code {test_code}: {result}")
            return result
        except Exception as e:
            logger.exception(f"Error validating credentials for test_id {test_id}")
            return None

    def check_test_already_taken(self, email, test_id):
        try:
            query = """
            SELECT id FROM user_test_log
            WHERE email = %s AND test_id = %s AND status = 'completed'
            """
            result = self.fetch_one(query, (email, test_id))
            taken = result is not None
            logger.debug(f"Check if test already taken by {email} for test_id {test_id}: {taken}")
            return taken
        except Exception as e:
            logger.exception(f"Error checking if test already taken by {email} for test_id {test_id}")
            return False

    def get_test_status_for_user(self, email, test_id):
        try:
            query = """
                SELECT status, start_time FROM user_test_log
                WHERE email = %s AND test_id = %s
                ORDER BY start_time DESC LIMIT 1 
            """
            result = self.fetch_one(query, (email, test_id))
            
            if result:
                return {
                    'status': result['status'],
                    'start_time': result['start_time'] 
                }
            else:
                return {'status': 'not_started', 'start_time': None}
        except Exception as e:
            logger.exception(f"Error fetching test status for user {email}, test_id {test_id}")
            return {'status': 'not_started', 'start_time': None}

    def store_user_test_start(self, email, test_id, username, is_checkbox_checked=False, ready_to_begin=False):
        try:
            
            existing_unperformed_test = self.fetch_one(
                "SELECT id FROM user_test_log WHERE email = %s AND test_id = %s AND status = 'unperformed'",
                (email, test_id)
            )

            if existing_unperformed_test:
            
                query = """
                    UPDATE user_test_log
                    SET
                        start_time = NOW(),
                        is_checkbox_checked = %s,
                        ready_to_begin = %s,
                        accepted_at = NOW(),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE email = %s AND test_id = %s AND status = 'unperformed'
                """
                self.execute_query(query, (
                    int(is_checkbox_checked), int(ready_to_begin),
                    email, test_id
                ))
                logger.debug(f"Updated existing unperformed test log for user {email}, test_id {test_id}")
            else:
                query = """
                    INSERT INTO user_test_log (
                        email, test_id, username,
                        start_time, status, device_info,
                        attempt_number, end_time,
                        is_checkbox_checked, ready_to_begin, accepted_at
                    )
                    VALUES (
                        %s, %s, %s,
                        NOW(), 'unperformed', NULL,
                        1, NULL, # Assuming first attempt or increment logic needed elsewhere for subsequent
                        %s, %s, NOW()
                    )
                """
                self.execute_query(query, (
                    email, test_id, username,
                    int(is_checkbox_checked), int(ready_to_begin)
                ))
                logger.debug(f"Stored new unperformed test log (with readiness) for user {email}, test_id {test_id}")
        except Exception as e:
            logger.exception(f"Error storing/updating test log with readiness for user {email}, test_id {test_id}")


    def complete_user_test(self, email, test_id, device_info, attempt_number=1):
        try:
            query = """
                UPDATE user_test_log
                SET status = 'completed',
                    end_time = NOW(),
                    device_info = %s,
                    attempt_number = %s
                WHERE email = %s AND test_id = %s AND status = 'unperformed'
            """
            self.execute_query(query, (device_info, attempt_number, email, test_id))
            logger.debug(f"Marked test as completed for {email} on test {test_id}")
        except Exception as e:
            logger.exception(f"Failed to update test completion for {email}, test {test_id}")

    def get_test_basic_details(self, test_id):
        try:
            query = """
                SELECT sm.code, sm.stream, td.subject_title, td.total_duration_minutes
                FROM test_details sm
                JOIN test_description td ON sm.test_id = td.test_id
                WHERE sm.test_id = %s
            """
            return self.fetch_one(query, (test_id,))
        except Exception as e:
            logger.exception(f"Error fetching basic test details for test_id: {test_id}")
            return None

    def get_all_test_questions(self, test_id):
        try:
            query = """
                SELECT id, test_id, section_id, section_name, question_number, question_type,
                        question_text, question_image, option_a, option_b, option_c, option_d,
                        correct_option, correct_marks, negative_marks, question_level, answer_text
                FROM test_questions
                WHERE test_id = %s
                ORDER BY section_id, question_number
            """
            return self.fetch_all(query, (test_id,))
        except Exception as e:
            logger.exception(f"Error fetching all questions for test_id: {test_id}")
            return []

    def get_test_sections(self, test_id):
        try:
            query = """
                SELECT section_id, section_name,
                        SUM(CASE WHEN correct_marks = 1 THEN 1 ELSE 0 END) AS one_mark_questions,
                        SUM(CASE WHEN correct_marks = 2 THEN 1 ELSE 0 END) AS two_mark_questions,
                        SUM(correct_marks) AS section_total_marks
                FROM test_questions
                WHERE test_id = %s
                GROUP BY section_id, section_name
                ORDER BY section_id
            """
            return self.fetch_all(query, (test_id,))
        except Exception as e:
            logger.exception(f"Error fetching sections for test_id: {test_id}")
            return []

    def terminate_user_test_log(self, email, test_id):
        query = """
            UPDATE user_test_log
            SET status = 'unperformed', 
                end_time = NOW()
            WHERE email = %s AND test_id = %s
        """
        self.execute_query(query, (email, test_id))
        logger.warning(f"Test {test_id} terminated for user {email} due to excessive violations")

    def get_completed_tests_for_user(self, email):
        """Fetches all tests that a user has completed."""
        try:
            query = """
                SELECT
                    tr.test_id,
                    tr.test_code,
                    td.subject_title,
                    td.test_number,
                    tr.submission_timestamp,
                    tr.net_score,
                    tr.percentage
                FROM test_result tr
                JOIN test_description td ON tr.test_id = td.test_id
                WHERE tr.email = %s
                ORDER BY tr.submission_timestamp DESC
            """
            return self.fetch_all(query, (email,))
        except Exception as e:
            logger.exception(f"Error fetching completed tests for user {email}")
            return []