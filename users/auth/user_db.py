import logging
from mysql.connector import Error
from app import db_pool

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class UserOperation:

    def get_user_by_email(self, email):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = "SELECT * FROM auth WHERE email = %s"
            cursor.execute(query, (email,))
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Error fetching user by email '{email}': {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def update_user_password(self, email, new_password):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor()
            query = "UPDATE auth SET password = %s WHERE email = %s"
            cursor.execute(query, (new_password, email))
            conn.commit()
        except Error as e:
            logger.error(f"Error updating password for {email}: {e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def set_user_password(self, email, hashed_password):
        self.update_user_password(email, hashed_password)

    def get_user_unique_code(self, email, course_name):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = "SELECT unique_code FROM enrollment WHERE email = %s AND course = %s"
            cursor.execute(query, (email, course_name))
            result = cursor.fetchone()
            return result['unique_code'] if result else None
        except Error as e:
            logger.error(f"Error getting unique code for {email}/{course_name}: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def get_all_active_coupons(self, email=None):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
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
        except Error as e:
            logger.error(f"Error getting active coupons: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def insert_user_google(self, username, email, oauth_id):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(buffered=True)
            query = """
                INSERT INTO auth (username, email, oauth_id, auth_type, is_verified)
                VALUES (%s, %s, %s, 'google', TRUE)
            """
            cursor.execute(query, (username, email, oauth_id))
            conn.commit()
            logger.info(f"Google user inserted: {email}")
        except Error as e:
            logger.error(f"Error inserting Google user {email}: {e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def user_signup_insert(self, username, password, email, is_verified=False):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(buffered=True)
            query = """
                INSERT INTO auth (username, password, email, is_verified, auth_type)
                VALUES (%s, %s, %s, %s, 'manual')
            """
            cursor.execute(query, (username, password, email, is_verified))
            conn.commit()
            logger.info(f"Manual signup user inserted: {email}")
        except Error as e:
            logger.error(f"Error inserting manual signup user {email}: {e}")
            if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def update_auth_type_to_both(self, email, oauth_id):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(buffered=True)
            query = "UPDATE auth SET auth_type = 'both', oauth_id = %s WHERE email = %s"
            cursor.execute(query, (oauth_id, email))
            conn.commit()
            return True
        except Error as e:
            logger.error(f"Error updating auth_type to 'both' for {email}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
