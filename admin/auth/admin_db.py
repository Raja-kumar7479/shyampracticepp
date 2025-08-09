import mysql.connector
from mysql.connector import Error
from app import db_pool
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class UserOperation:
    def __init__(self):
        if db_pool is None:
            raise Exception("Admin database connection pool is not initialized.")

    def get_admin_by_email(self, email):
        """Fetch admin data by email"""
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, email, password, role FROM auth_admin WHERE email = %s", (email,))
            result = cursor.fetchone()
            logging.info(f"Fetched admin for email: {email}")
            return result
        except Error as e:
            logging.error(f"Error fetching admin by email: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def set_admin_password(self, email, hashed_password):
        """Update admin password by email"""
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=False)
            cursor.execute("UPDATE auth_admin SET password = %s WHERE email = %s", (hashed_password, email))
            conn.commit()
            logging.info(f"Password updated for admin: {email}")
            return True
        except Error as e:
            logging.error(f"Error updating password for admin: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()