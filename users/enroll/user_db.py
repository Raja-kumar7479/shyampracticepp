import logging
from mysql.connector import Error
from app import db_pool

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class  UserOperation:

    def check_enrollment(self, email, course_code):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(buffered=True)
            query = "SELECT EXISTS (SELECT 1 FROM enrollment WHERE email = %s AND code = %s)"
            cursor.execute(query, (email, course_code))
            result = cursor.fetchone()
            return result[0] if result else 0
        except Error as e:
            logger.error(f"Error checking enrollment for {email}/{course_code}: {e}")
            return 0
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def enroll_user(self, email, course_code, course_name, unique_code):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor()
            query = "INSERT INTO enrollment (email, code, name, unique_code) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (email, course_code, course_name, unique_code))
            conn.commit()
        except Error as e:
            logger.error(f"Error enrolling user {email} in {course_code}: {e}")
            if conn: conn.rollback()
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_enrolled_courses(self, email):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT code, unique_code FROM enrollment WHERE email = %s"
            cursor.execute(query, (email,))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error getting enrolled courses for {email}: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_user_unique_code(self, email, course_code):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT unique_code FROM enrollment WHERE email = %s AND code = %s"
            cursor.execute(query, (email, course_code))
            result = cursor.fetchone()
            return result['unique_code'] if result else None
        except Error as e:
            logger.error(f"Error fetching unique code for {email}/{course_code}: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_all_courses(self):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT code, name, description FROM courses")
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error fetching all courses: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_user_by_email(self, email):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT username FROM auth WHERE email = %s", (email,))
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Error fetching user by email {email}: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def is_course_purchased_securely(self, email, course_code, title, subtitle):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = """
                SELECT status, purchase_code FROM purchase
                WHERE email = %s AND course_code = %s AND title = %s AND subtitle = %s AND status = 'Paid'
            """
            cursor.execute(query, (email, course_code, title, subtitle))
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Error verifying course purchase for {email}: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_content_by_code_title_subtitle(self, course_code, title, subtitle):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM course_content WHERE code = %s AND title = %s AND subtitle = %s"
            cursor.execute(query, (course_code, title, subtitle))
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Error fetching content by code/title/subtitle: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_course_details(self, course_code):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT code, name, description FROM courses WHERE code = %s"
            cursor.execute(query, (course_code,))
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Error fetching course details for {course_code}: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_free_courses_by_code(self, code):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT * FROM course_content
                WHERE code = %s AND status = 'active' AND label = 'Free'
                ORDER BY FIELD(section, 'NOTES', 'PRACTICE BOOK', 'PYQ','MOCK TEST')
            """
            cursor.execute(query, (code,))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error fetching free courses for {code}: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_paid_courses_by_code(self, code):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT * FROM course_content
                WHERE code = %s AND status = 'active' AND label = 'Paid'
                ORDER BY FIELD(section, 'NOTES', 'PRACTICE BOOK', 'PYQ','MOCK TEST')
            """
            cursor.execute(query, (code,))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error fetching paid courses for {code}: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_sections_by_code(self, code):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor()
            query = """
                SELECT DISTINCT section FROM course_content
                WHERE code = %s AND status = 'active'
            """
            cursor.execute(query, (code,))
            return [row[0] for row in cursor.fetchall()]
        except Error as e:
            logger.error(f"Error fetching sections for {code}: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_practice_sections_for_code(self, code):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor()
            query = "SELECT DISTINCT section FROM practice_questions WHERE code = %s"
            cursor.execute(query, (code,))
            sections = [row[0] for row in cursor.fetchall()]
            return sections
        except Error as e:
            logger.error(f"Error fetching practice sections for {code}: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
