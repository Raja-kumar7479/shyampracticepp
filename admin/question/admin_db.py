import mysql.connector
from mysql.connector import Error
from config import Config
from contextlib import contextmanager
import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

class UserOperation:
    def __init__(self):
        self.allowed_fields = [
            'question_id', 'paper_code', 'subject', 'topic', 'year',
            'question_type', 'paper_set', 'question_text', 'option_a',
            'option_b', 'option_c', 'option_d', 'correct_option',
            'answer_text', 'explanation_link', 'image_path'
        ]

    @contextmanager
    def connection(self):
        conn = None
        try:
            conn = mysql.connector.connect(
                host=Config.DATABASE_HOST,
                user=Config.DATABASE_USER,
                password=Config.DATABASE_PASSWORD,
                database=Config.DATABASE_NAME
            )
            yield conn
        except Error as e:
            logging.error("Database connection error: %s", str(e))
            raise
        finally:
            if conn:
                conn.close()

    @contextmanager
    def cursor(self, conn, dictionary=False):
        cur = conn.cursor(dictionary=dictionary)
        try:
            yield cur
        finally:
            cur.close()

    def get_next_question_id(self):
        try:
            query = "SELECT MAX(CAST(question_id AS UNSIGNED)) AS max_id FROM questions"
            row = self.fetch_one(query)
            next_id = (int(row['max_id']) if row and row.get('max_id') else 0) + 1
            logging.info("Next question_id calculated: %s", next_id)
            return next_id
        except Exception as e:
            logging.error("Error getting next question_id: %s", str(e))
            return 1

    def check_question_exists_by_id(self, question_id):
        query = "SELECT 1 FROM questions WHERE question_id = %s"
        exists = self.fetch_one(query, (question_id,)) is not None
        logging.info("Check exists by ID %s: %s", question_id, exists)
        return exists

    def check_question_exists_by_text(self, question_text):
        query = "SELECT 1 FROM questions WHERE question_text = %s"
        exists = self.fetch_one(query, (question_text,)) is not None
        logging.info("Check exists by text: %s -> %s", question_text[:30], exists)
        return exists

    def insert_question(self, data):
        try:
            data = {k: v for k, v in data.items() if k in self.allowed_fields}
            if not data:
                return False, "No valid fields provided"

            data['last_updated'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            fields = ', '.join(data.keys())
            placeholders = ', '.join(['%s'] * len(data))
            values = tuple(data.values())

            query = f"INSERT INTO questions ({fields}) VALUES ({placeholders})"
            success, error = self._execute_query(query, values)
            if success:
                logging.info("Question inserted successfully.")
            else:
                logging.error("Insert failed: %s", error)
            return success, error

        except Exception as e:
            logging.exception("Error inserting question")
            return False, str(e)

    def fetch_questions(self, paper_code, subject=None, topic=None):
        try:
            query = "SELECT * FROM questions WHERE paper_code = %s"
            params = [paper_code]

            if subject:
                query += " AND subject = %s"
                params.append(subject)
            if topic:
                query += " AND topic = %s"
                params.append(topic)

            questions = self.fetch_all(query, tuple(params))
            logging.info("Fetched %d questions", len(questions))
            return questions
        except Exception as e:
            logging.exception("Error fetching questions")
            return []

    def delete_question_by_id(self, question_id):
        query = "DELETE FROM questions WHERE question_id = %s"
        success, error = self._execute_query(query, (question_id,))
        if success:
            logging.info("Deleted question_id %s", question_id)
        else:
            logging.error("Delete failed for question_id %s: %s", question_id, error)
        return success, error

    def update_question_by_id(self, original_id, updates):
        try:
            updates = {k: v for k, v in updates.items() if k in self.allowed_fields}
            if not updates:
                return False, "No valid fields provided to update"

            updates['last_updated'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            set_clauses = [f"{field} = %s" for field in updates.keys()]
            values = list(updates.values())
            values.append(original_id)

            query = f"UPDATE questions SET {', '.join(set_clauses)} WHERE question_id = %s"
            success, error = self._execute_query(query, tuple(values))
            if success:
                logging.info("Updated question_id %s", original_id)
            else:
                logging.error("Update failed for question_id %s: %s", original_id, error)
            return success, error

        except Exception as e:
            logging.exception("Error updating question")
            return False, str(e)

    def fetch_all(self, query, params=None):
        try:
            with self.connection() as conn:
                with self.cursor(conn, dictionary=True) as cur:
                    cur.execute(query, params or [])
                    result = cur.fetchall()
                    return result
        except Error as e:
            logging.error("fetch_all error: %s", str(e))
            return []

    def fetch_one(self, query, params=None):
        try:
            with self.connection() as conn:
                with self.cursor(conn, dictionary=True) as cur:
                    cur.execute(query, params or [])
                    return cur.fetchone()
        except Error as e:
            logging.error("fetch_one error: %s", str(e))
            return None

    def _execute_query(self, query, params):
        try:
            with self.connection() as conn:
                with self.cursor(conn) as cur:
                    cur.execute(query, params)
                    conn.commit()
                    return True, None
        except Error as e:
            logging.error("Query execution error: %s | Query: %s | Params: %s", str(e), query, params)
            return False, str(e)
