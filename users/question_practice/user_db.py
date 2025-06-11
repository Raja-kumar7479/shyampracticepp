import mysql.connector
from mysql.connector import Error
from config import Config
from contextlib import contextmanager
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class UserOperation:
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
            logger.debug("Database connection established.")
            yield conn
        except Error as e:
            logger.exception("Database connection error.")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()
                logger.debug("Database connection closed.")

    @contextmanager
    def cursor(self, conn, buffered=False, dictionary=True):
        cursor = None
        try:
            cursor = conn.cursor(buffered=buffered, dictionary=dictionary)
            yield cursor
        finally:
            if cursor:
                cursor.close()

    def fetch_one(self, query, params=(), buffered=False):
        try:
            with self.connection() as conn:
                with self.cursor(conn, buffered=buffered) as cursor:
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    logger.debug(f"Fetched one: {result}")
                    return result
        except Error as e:
            logger.exception(f"Error fetching one: {e}")
            return None

    def fetch_all(self, query, params=()):
        try:
            with self.connection() as conn:
                with self.cursor(conn) as cursor:
                    cursor.execute(query, params)
                    result = cursor.fetchall()
                    logger.debug(f"Fetched all: {len(result)} rows")
                    return result
        except Error as e:
            logger.exception(f"Error fetching all: {e}")
            return []

    def execute_query(self, query, params=()):
        try:
            with self.connection() as conn:
                with self.cursor(conn, dictionary=False) as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    logger.info("Query executed successfully.")
                    return True
        except Error as e:
            logger.exception("Query execution failed.")
            return False

    def check_enrollment(self, email, course_name):
        query = "SELECT EXISTS (SELECT 1 FROM enrollment WHERE email = %s AND course = %s) AS enrolled"
        result = self.fetch_one(query, (email, course_name))
        return result['enrolled'] if result else False

    def enroll_user(self, email, course_name, unique_code):
        query = "INSERT INTO enrollment (email, course, unique_code) VALUES (%s, %s, %s)"
        return self.execute_query(query, (email, course_name, unique_code))

    def get_enrolled_courses(self, email):
        query = "SELECT course FROM enrollment WHERE email = %s"
        rows = self.fetch_all(query, (email,))
        return [row['course'] for row in rows] if rows else []

    def get_user_unique_code(self, email, course_name):
        query = "SELECT unique_code FROM enrollment WHERE email = %s AND course = %s"
        result = self.fetch_one(query, (email, course_name))
        return result['unique_code'] if result else None

    def get_all_courses(self):
        query = "SELECT code, name, description FROM courses"
        return self.fetch_all(query)

    def get_user_by_email(self, email):
        query = "SELECT username FROM auth WHERE email = %s"
        return self.fetch_one(query, (email,))

    def get_books_for_course(self, course_code):
        query = "SELECT title, url FROM books WHERE code = %s"
        return self.fetch_all(query, (course_code.upper(),))

    def get_courses_by_code(self, code):
        query = """
            SELECT * FROM content 
            WHERE code = %s AND status = 'active' 
            ORDER BY 
                FIELD(section, 'NOTES', 'PRACTICE BOOK', 'PYQ'),
                FIELD(label, 'Free', 'Paid')
        """
        return self.fetch_all(query, (code,))

    def is_course_purchased_securely(self, email, course_code, title, subtitle):
        query = """
            SELECT status, purchase_code 
            FROM purchases 
            WHERE email = %s AND course_code = %s AND title = %s AND subtitle = %s AND status = 'Paid'
        """
        result = self.fetch_one(query, (email, course_code, title, subtitle), buffered=True)
        return result

    def get_content_by_code_title_subtitle(self, course_code, title, subtitle):
        query = "SELECT * FROM content WHERE code = %s AND title = %s AND subtitle = %s"
        return self.fetch_one(query, (course_code, title, subtitle))

    def get_unique_code(self, email, course_code):
        query = "SELECT unique_code FROM enrollment WHERE email = %s AND code = %s"
        result = self.fetch_one(query, (email, course_code))
        return result['unique_code'] if result else None

    def get_question_by_id(self, question_id):
        query = "SELECT * FROM questions WHERE question_id = %s"
        return self.fetch_one(query, (question_id,))
