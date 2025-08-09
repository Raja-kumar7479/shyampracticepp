import mysql.connector
from mysql.connector import Error
from app import db_pool
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='app.log')

class PaperOperation:
    def __init__(self):
        if db_pool is None:
            raise Exception("Database connection pool is not initialized.")

    def _get_connection(self):
        return db_pool.get_connection()

    def get_all_paper_codes(self):
        return self._fetch_all("SELECT DISTINCT code FROM course_content WHERE section = 'mock test' ORDER BY code ASC")

    def get_distinct_values(self, column, paper_code, subject=None):
        params = [paper_code]
        query = f"SELECT DISTINCT {column} FROM questions WHERE paper_code = %s"
        if subject:
            query += " AND subject = %s"
            params.append(subject)
        query += f" AND {column} IS NOT NULL AND {column} != '' ORDER BY {column} ASC"
        return self._fetch_all(query, tuple(params))

    def insert_question(self, data):
        query = """
            INSERT INTO questions
            (paper_code, question_id, question_type, subject, topic, question_text,
             option_a, option_b, option_c, option_d, correct_option,
             answer_text, year, paper_set, explanation_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            data['paper_code'], data['question_id'], data['question_type'],
            data.get('subject'), data.get('topic'), data.get('question_text'),
            data.get('option_a'), data.get('option_b'), data.get('option_c'), data.get('option_d'),
            data.get('correct_option'), data.get('answer_text'), data.get('year'),
            data.get('paper_set'), data.get('explanation_link')
        )
        return self._execute_query(query, params, fetch_last_id=True)

    def search_questions(self, paper_code, subject, topic=None):
        base_query = "SELECT * FROM questions WHERE paper_code = %s AND subject = %s"
        params = [paper_code, subject]
        
        if topic and topic.strip():
            base_query += " AND topic = %s"
            params.append(topic)
            
        base_query += " ORDER BY question_id ASC"
        return self._fetch_all(base_query, tuple(params))

    def update_question(self, db_id, data):
        query = """
            UPDATE questions SET
            paper_code = %s, question_id = %s, question_type = %s, subject = %s, topic = %s,
            question_text = %s, option_a = %s, option_b = %s, option_c = %s, option_d = %s,
            correct_option = %s, answer_text = %s, year = %s, paper_set = %s, explanation_link = %s
            WHERE id = %s
        """
        params = (
            data['paper_code'], data['question_id'], data['question_type'],
            data.get('subject'), data.get('topic'), data.get('question_text'),
            data.get('option_a'), data.get('option_b'), data.get('option_c'), data.get('option_d'),
            data.get('correct_option'), data.get('answer_text'), data.get('year'),
            data.get('paper_set'), data.get('explanation_link'), db_id
        )
        self._execute_query(query, params)

    def delete_question(self, db_id):
        query = "DELETE FROM questions WHERE id = %s"
        self._execute_query(query, (db_id,))

    def _fetch_all(self, query, params=None):
        conn = None
        cursor = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except mysql.connector.Error as err:
            logger.error(f"Error in _fetch_all: {err}")
            return []
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def _execute_query(self, query, params=None, fetch_last_id=False):
        conn = None
        cursor = None
        last_id = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if fetch_last_id:
                last_id = cursor.lastrowid
            conn.commit()
            return last_id
        except mysql.connector.Error as err:
            logger.error(f"Database query failed: {err}\nQuery: {query}\nParams: {params}")
            if conn: conn.rollback()
            raise err
        finally:
            if cursor: cursor.close()
            if conn: conn.close()