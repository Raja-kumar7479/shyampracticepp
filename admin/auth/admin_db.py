import mysql.connector
from mysql.connector import Error
from config import Config
import logging
from contextlib import contextmanager


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class UserOperation:

    def connection(self):
        """Establish database connection"""
        return mysql.connector.connect(
            host=Config.DATABASE_HOST,
            user=Config.DATABASE_USER,
            password=Config.DATABASE_PASSWORD,
            database=Config.DATABASE_NAME
        )

    @contextmanager
    def db_cursor(self):
        """Context manager for database connection and buffered cursor"""
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor(buffered=True)
            yield db, cursor
        except Error as e:
            logging.error(f"MySQL error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()
                logging.info("Database connection closed.")

    def get_admin_by_email(self, email):
        """Fetch admin data by email"""
        try:
            with self.db_cursor() as (db, cursor):
                cursor.execute("SELECT id, username, email, password, role FROM auth_admin WHERE email = %s", (email,))
                result = cursor.fetchone()
                logging.info(f"Fetched admin for email: {email}")
                return result
        except Exception as e:
            logging.error(f"Error fetching admin by email: {e}")
            return None

    def set_admin_password(self, email, hashed_password):
        """Update admin password by email"""
        try:
            with self.db_cursor() as (db, cursor):
                cursor.execute("UPDATE auth_admin SET password = %s WHERE email = %s", (hashed_password, email))
                db.commit()
                logging.info(f"Password updated for admin: {email}")
                return True
        except Exception as e:
            logging.error(f"Error updating password for admin: {e}")
            return False
