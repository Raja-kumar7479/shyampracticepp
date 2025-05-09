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

    def check_enrollment(self, email, course_name):
        try:
            db = self.connection()
            cursor = db.cursor(buffered=True)
            query = "SELECT EXISTS (SELECT 1 FROM enrollment WHERE email = %s AND course = %s)"
            cursor.execute(query, (email, course_name))
            result = cursor.fetchone()[0]
            logger.info(f"Enrollment check for {email} in {course_name}: {result}")
            return result
        except Exception as e:
            logger.exception("Error checking enrollment")
            return 0
        finally:
            cursor.close()
            db.close()

    def enroll_user(self, email, course_name, unique_code):
        try:
            db = self.connection()
            cursor = db.cursor()
            query = "INSERT INTO enrollment (email, course, unique_code) VALUES (%s, %s, %s)"
            cursor.execute(query, (email, course_name, unique_code))
            db.commit()
            logger.info(f"User {email} enrolled in {course_name}")
        except Exception as e:
            logger.exception("Error enrolling user")
        finally:
            cursor.close()
            db.close()

    def get_enrolled_courses(self, email):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            query = "SELECT course FROM enrollment WHERE email = %s"
            cursor.execute(query, (email,))
            return [row['course'] for row in cursor.fetchall()]
        except Exception as e:
            logger.exception("Error getting enrolled courses")
            return []
        finally:
            cursor.close()
            db.close()

    def get_user_unique_code(self, email, course_name):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            query = "SELECT unique_code FROM enrollment WHERE email = %s AND course = %s"
            cursor.execute(query, (email, course_name))
            result = cursor.fetchone()
            return result['unique_code'] if result else None
        except Exception as e:
            logger.exception("Error fetching user unique code")
            return None
        finally:
            cursor.close()
            db.close()

    def get_all_courses(self):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT code, name, description FROM courses")
            return cursor.fetchall()
        except Exception as e:
            logger.exception("Error fetching all courses")
            return []
        finally:
            cursor.close()
            db.close()

    def get_user_by_email(self, email):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT username FROM auth WHERE email = %s", (email,))
            return cursor.fetchone()
        except Exception as e:
            logger.exception("Error fetching user by email")
            return None
        finally:
            cursor.close()
            db.close()

    def get_books_for_course(self, course_code):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            query = "SELECT title, url FROM books WHERE code = %s"
            cursor.execute(query, (course_code.upper(),))
            return cursor.fetchall()
        except Exception as e:
            logger.exception("Error fetching books for course")
            return []
        finally:
            cursor.close()
            db.close()

    def get_courses_by_code(self, code):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            query = """
                SELECT * FROM content 
                WHERE code = %s AND status = 'active' 
                ORDER BY 
                    FIELD(section, 'NOTES', 'PRACTICE BOOK', 'PYQ'),
                    FIELD(label, 'Free', 'Paid')
            """
            cursor.execute(query, (code,))
            return cursor.fetchall()
        except Exception as e:
            logger.exception("Error fetching courses by code")
            return []
        finally:
            cursor.close()
            db.close()

    def is_course_purchased_securely(self, email, course_code, title, subtitle):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True, buffered=True)
            query = """
                SELECT status, purchase_code 
                FROM purchase 
                WHERE email = %s AND course_code = %s AND title = %s AND subtitle = %s AND status = 'Paid'
            """
            cursor.execute(query, (email, course_code, title, subtitle))
            return cursor.fetchone()
        except Exception as e:
            logger.exception("Error verifying course purchase")
            return None
        finally:
            cursor.close()
            db.close()

    def get_content_by_code_title_subtitle(self, course_code, title, subtitle):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            query = """
                SELECT * FROM content
                WHERE code = %s AND title = %s AND subtitle = %s
            """
            cursor.execute(query, (course_code, title, subtitle))
            return cursor.fetchone()
        except Exception as e:
            logger.exception("Error fetching content by code/title/subtitle")
            return None
        finally:
            cursor.close()
            db.close()
