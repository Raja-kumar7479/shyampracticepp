import mysql.connector
from mysql.connector import Error
from database_pool import db_pool
import datetime

class UserOperation:
    
    def __init__(self):
        if db_pool is None:
            raise Exception("Database connection pool is not initialized.")

    def fetch_one(self, query, params=()):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result
        except Error as e:
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def fetch_all(self, query, params=()):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params)
            result = cursor.fetchall()
            return result
        except Error as e:
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_query(self, query, params=()):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return True
        except Error as e:
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def report_question_issue(self, question_id, problem_description, user_email):
        try:
            select_query = "SELECT report_count, report_problem FROM questions WHERE question_id = %s"
            question_report = self.fetch_one(select_query, (question_id,))
            if not question_report:
                return False
            current_count = question_report.get('report_count', 0)
            existing_problems = question_report.get('report_problem') or ""
            new_count = current_count + 1
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_problem_entry = f"Report from '{user_email}' at {timestamp}:\n{problem_description}\n{'-'*20}\n"
            updated_problems = new_problem_entry + existing_problems
            update_query = "UPDATE questions SET report_count = %s, report_problem = %s WHERE question_id = %s"
            success = self.execute_query(update_query, (new_count, updated_problems, question_id))
            return success
        except Exception as e:
            return False

    def check_enrollment(self, email, course_name):
        try:
            query = "SELECT EXISTS (SELECT 1 FROM enrollment WHERE email = %s AND code = %s) AS enrolled"
            result = self.fetch_one(query, (email, course_name))
            return result['enrolled'] if result and 'enrolled' in result else False
        except Error as e:
            return False

    def enroll_user(self, email, course_name, unique_code):
        try:
            query = "INSERT INTO enrollment (email, code, unique_code) VALUES (%s, %s, %s)"
            return self.execute_query(query, (email, course_name, unique_code))
        except Error as e:
            return False

    def get_enrolled_courses(self, email):
        try:
            query = "SELECT code FROM enrollment WHERE email = %s"
            rows = self.fetch_all(query, (email,))
            return [row['code'] for row in rows] if rows else []
        except Error as e:
            return []

    def get_user_unique_code(self, email, course_name):
        try:
            query = "SELECT unique_code FROM enrollment WHERE email = %s AND code = %s"
            result = self.fetch_one(query, (email, course_name))
            return result['unique_code'] if result else None
        except Error as e:
            return None

    def get_all_courses(self):
        try:
            query = "SELECT code, name, description FROM courses"
            return self.fetch_all(query)
        except Error as e:
            return []

    def get_user_by_email(self, email):
        try:
            query = "SELECT username FROM auth WHERE email = %s"
            return self.fetch_one(query, (email,))
        except Error as e:
            return None

    def get_books_for_course(self, course_code):
        try:
            query = "SELECT title, url FROM books WHERE code = %s"
            return self.fetch_all(query, (course_code.upper(),))
        except Error as e:
            return []

    def get_courses_by_code(self, code):
        try:
            query = """
                SELECT * FROM content
                WHERE code = %s AND status = 'active'
                ORDER BY
                    FIELD(section, 'NOTES', 'PRACTICE BOOK', 'PYQ'),
                    FIELD(label, 'Free', 'Paid')
            """
            return self.fetch_all(query, (code,))
        except Error as e:
            return []

    def is_course_purchased_securely(self, email, course_code, title, subtitle):
        try:
            query = """
                SELECT status, purchase_code
                FROM purchases
                WHERE email = %s AND course_code = %s AND title = %s AND subtitle = %s AND status = 'Paid'
            """
            return self.fetch_one(query, (email, course_code, title, subtitle))
        except Error as e:
            return None

    def get_content_by_code_title_subtitle(self, course_code, title, subtitle):
        try:
            query = "SELECT * FROM content WHERE code = %s AND title = %s AND subtitle = %s"
            return self.fetch_one(query, (course_code, title, subtitle))
        except Error as e:
            return None

    def get_unique_code(self, email, course_code):
        try:
            query = "SELECT unique_code FROM enrollment WHERE email = %s AND code = %s"
            result = self.fetch_one(query, (email, course_code))
            return result['unique_code'] if result else None
        except Error as e:
            return None

    def get_question_by_id(self, question_id):
        try:
            query = "SELECT * FROM questions WHERE question_id = %s"
            return self.fetch_one(query, (question_id,))
        except Error as e:
            return None
