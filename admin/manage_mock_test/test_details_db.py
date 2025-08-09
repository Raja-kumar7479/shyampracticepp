import mysql.connector
from mysql.connector import Error
from app import db_pool
import logging

logger = logging.getLogger(__name__)

class UserOperation:
    def __init__(self):
        if db_pool is None:
            raise Exception("Database connection pool is not initialized.")

    def _fetch_one(self, query, params=None):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except mysql.connector.Error as err:
            logger.error(f"Error in _fetch_one: {err}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _fetch_all(self, query, params=None):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except mysql.connector.Error as err:
            logger.error(f"Error in _fetch_all: {err}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def _execute_query(self, query, params=None):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
        except mysql.connector.Error as err:
            logger.error(f"Error in _execute_query: {err}")
            if conn:
                conn.rollback()
            raise err
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_content_for_tests(self):
        query = "SELECT section_id as test_id, title FROM course_content WHERE section = 'mock test' ORDER BY title"
        return self._fetch_all(query)

    def get_test_descriptions_by_test_id(self, test_id):
        query = "SELECT * FROM test_description WHERE test_id = %s"
        return self._fetch_all(query, (test_id,))

    def get_test_description_by_id(self, description_id):
        query = "SELECT * FROM test_description WHERE id = %s"
        return self._fetch_one(query, (description_id,))

    def insert_test_description(self, data):
        query = """
            INSERT INTO test_description
            (test_id, test_key, subject_title, subject_subtitle,
             total_questions, total_marks, total_duration_minutes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            data['test_id'], data['test_key'], data['subject_title'],
            data.get('subject_subtitle'), data['total_questions'],
            data['total_marks'], data['total_duration_minutes']
        )
        self._execute_query(query, params)

    def update_test_description_field(self, id, field, value):
        allowed_fields = [
            'test_key', 'subject_title', 'subject_subtitle', 'total_questions',
            'total_marks', 'total_duration_minutes'
        ]
        if field not in allowed_fields:
            raise ValueError(f"Invalid field for update: {field}")
        query = f"UPDATE test_description SET {field} = %s, updated_at = NOW() WHERE id = %s"
        self._execute_query(query, (value, id))

    def delete_test_description(self, description_id):
        query_questions = "DELETE FROM test_questions WHERE test_description_id = %s"
        self._execute_query(query_questions, (description_id,))
        query_desc = "DELETE FROM test_description WHERE id = %s"
        self._execute_query(query_desc, (description_id,))

    def get_questions_for_description_section(self, description_id, section_id):
        query = "SELECT * FROM test_questions WHERE test_description_id = %s AND section_id = %s ORDER BY question_number"
        return self._fetch_all(query, (description_id, section_id))

    def get_question_count_for_description(self, description_id):
        query = "SELECT COUNT(*) as count FROM test_questions WHERE test_description_id = %s"
        result = self._fetch_one(query, (description_id,))
        return result['count'] if result else 0

    def get_max_question_number_in_section(self, description_id, section_id):
        query = "SELECT MAX(question_number) as max_num FROM test_questions WHERE test_description_id = %s AND section_id = %s"
        result = self._fetch_one(query, (description_id, section_id))
        return result['max_num'] if result and result['max_num'] is not None else 0

    def insert_test_question(self, data):
      query = """
        INSERT INTO test_questions
        (test_id, test_key, test_description_id, section_id, section_name, question_number, question_type, question_text,
         option_a, option_b, option_c, option_d, correct_option, correct_marks,
         negative_marks, question_level, answer_text, answer_link, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
      """
      params = (
        data['test_id'], data['test_key'], data['test_description_id'], data['section_id'], data['section_name'], data['question_number'],
        data['question_type'], data['question_text'], data.get('option_a'),
        data.get('option_b'), data.get('option_c'), data.get('option_d'),
        data['correct_option'], data['correct_marks'], data['negative_marks'],
        data['question_level'], data.get('answer_text'), data.get('answer_link')
      )
      self._execute_query(query, params)

    def update_test_question_field(self, id, field, value):
        allowed_fields = [
            'section_id', 'section_name', 'question_type', 'question_text', 'option_a',
            'option_b', 'option_c', 'option_d', 'correct_option', 'correct_marks',
            'negative_marks', 'question_level', 'answer_text', 'answer_link'
        ]
        if field not in allowed_fields:
            raise ValueError(f"Invalid field for update: {field}")
        query = f"UPDATE test_questions SET {field} = %s, updated_at = NOW() WHERE id = %s"
        self._execute_query(query, (value, id))

    def delete_test_question(self, id):
        query = "DELETE FROM test_questions WHERE id = %s"
        self._execute_query(query, (id,))

    def get_all_feedback_entries(self, page=1, per_page=50):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            offset = (page - 1) * per_page
            query = "SELECT SQL_CALC_FOUND_ROWS * FROM test_feedback ORDER BY submission_time DESC LIMIT %s OFFSET %s"
            cursor.execute(query, (per_page, offset))
            feedbacks = cursor.fetchall()
            cursor.execute("SELECT FOUND_ROWS() as total")
            total = cursor.fetchone()['total']
            return feedbacks, total
        except Exception as e:
            logger.exception("Error fetching all feedback entries")
            return [], 0
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def truncate_all_feedback(self):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor()
            cursor.execute("TRUNCATE TABLE test_feedback")
            conn.commit()
            logger.info("Successfully truncated test_feedback table.")
            return True
        except Exception as e:
            logger.exception("Error truncating test_feedback table")
            if conn: conn.rollback()
            return False
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def get_selected_user_test_logs(self, page=1, per_page=50):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            offset = (page - 1) * per_page
            query = "SELECT SQL_CALC_FOUND_ROWS email, username, test_id, test_key, start_time, end_time FROM user_test_log ORDER BY start_time DESC LIMIT %s OFFSET %s"
            cursor.execute(query, (per_page, offset))
            logs = cursor.fetchall()
            cursor.execute("SELECT FOUND_ROWS() as total")
            total = cursor.fetchone()['total']
            return logs, total
        except Exception as e:
            logger.exception("Error fetching selected user test logs")
            return [], 0
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def count_unique_test_attempts(self):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor()
            query = "SELECT COUNT(DISTINCT email) FROM user_test_log"
            cursor.execute(query)
            result = cursor.fetchone()
            count = result[0] if result else 0
            logger.info(f"Counted {count} unique test attempts by email.")
            return count
        except Exception as e:
            logger.exception("Error counting unique test attempts")
            return 0
        finally:
            if cursor: cursor.close()
            if conn: conn.close()