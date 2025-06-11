import logging
import mysql.connector
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class ContentOperation:

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

   
    def get_mock_tests_paid(self, course_code, user_email):
        try:
            query = """
                SELECT
                    sm.test_id, sm.test_code, sm.code,
                    sm.name AS course_name, sm.stream,
                    td.test_number, td.subject_title, td.subject_subtitle,
                    td.total_questions, td.total_marks AS question_marks, td.total_duration_minutes AS duration, td.year,
                    COALESCE(utl.status, 'not_started') AS user_test_status,
                    utl.attempt_number,
                    sm.label  
                FROM study_materials sm
                JOIN test_description td ON sm.test_id = td.test_id
                LEFT JOIN user_test_log utl ON sm.test_id = utl.test_id AND utl.email = %s
                WHERE sm.code = %s AND sm.label = 'Paid'
                ORDER BY td.test_number
            """
            return self.fetch_all(query, (user_email, course_code))
        except Exception as e:
            logger.exception("Error fetching tests for mock test")
            return []

    # You'll need a similar function for free tests, ensuring 'sm.label' is selected
    def get_mock_tests_free(self, course_code, user_email):
        try:
            query = """
                SELECT
                    sm.test_id, sm.test_code, sm.code,
                    sm.name AS course_name, sm.stream,
                    td.test_number, td.subject_title, td.subject_subtitle,
                    td.total_questions, td.total_marks AS question_marks, td.total_duration_minutes AS duration, td.year,
                    COALESCE(utl.status, 'not_started') AS user_test_status,
                    utl.attempt_number,
                    sm.label 
                FROM study_materials sm
                JOIN test_description td ON sm.test_id = td.test_id
                LEFT JOIN user_test_log utl ON sm.test_id = utl.test_id AND utl.email = %s
                WHERE sm.code = %s AND sm.label = 'Free' 
                ORDER BY td.test_number
            """
            return self.fetch_all(query, (user_email, course_code))
        except Exception as e:
            logger.exception("Error fetching tests for mock test")
            return []