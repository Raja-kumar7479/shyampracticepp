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
            yield conn
        except Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_user_by_email(self, email):
        db = None
        cursor = None
        try:
            with self.connection() as db:
                cursor = db.cursor(buffered=True)
                query = "SELECT * FROM auth WHERE email = %s"
                cursor.execute(query, (email,))
                return cursor.fetchone()
        except Exception as e:
            logger.exception("Error fetching user by email")
            return None
        finally:
            if cursor:
                cursor.close()

    def user_signup_insert(self, username, password, email, is_verified=False):
        db = None
        cursor = None
        try:
            with self.connection() as db:
                cursor = db.cursor()
                query = """
                    INSERT INTO auth (username, password, email, is_verified)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (username, password, email, is_verified))
                db.commit()
        except Exception as e:
            logger.exception("Error inserting user")
        finally:
            if cursor:
                cursor.close()

    def update_user_password(self, email, new_password):
        db = None
        cursor = None
        try:
            with self.connection() as db:
                cursor = db.cursor()
                query = "UPDATE auth SET password = %s WHERE email = %s"
                cursor.execute(query, (new_password, email))
                db.commit()
        except Exception as e:
            logger.exception("Error updating password")
        finally:
            if cursor:
                cursor.close()

    def set_user_password(self, email, hashed_password):
        self.update_user_password(email, hashed_password)

    def get_user_unique_code(self, email, course_name):
        db = None
        cursor = None
        try:
            with self.connection() as db:
                cursor = db.cursor(dictionary=True, buffered=True)
                cursor.execute(
                    "SELECT unique_code FROM enrollment WHERE email = %s AND course = %s",
                    (email, course_name)
                )
                result = cursor.fetchone()
                return result['unique_code'] if result else None
        except Exception as e:
            logger.exception("Error in get_user_unique_code")
            return None
        finally:
            if cursor:
                cursor.close()

    def get_all_active_coupons(self, email=None):
        db = None
        cursor = None
        try:
            with self.connection() as db:
                cursor = db.cursor(dictionary=True, buffered=True)
                if email:
                    query = """
                        SELECT * FROM coupone
                        WHERE status = 1
                          AND (email IS NULL OR email = %s)
                          AND (valid_until IS NULL OR valid_until > NOW())
                          AND (expiry_date IS NULL OR expiry_date > NOW())
                    """
                    cursor.execute(query, (email,))
                else:
                    query = """
                        SELECT * FROM coupone
                        WHERE status = 1
                          AND email IS NULL
                          AND (valid_until IS NULL OR valid_until > NOW())
                          AND (expiry_date IS NULL OR expiry_date > NOW())
                    """
                    cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            logger.exception("Error in get_all_active_coupons")
            return []
        finally:
            if cursor:
                cursor.close()
