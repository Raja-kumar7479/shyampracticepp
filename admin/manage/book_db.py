import logging
import mysql.connector
from mysql.connector import Error
from config import Config
from contextlib import contextmanager


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    pass

@contextmanager
def DatabaseConnection(dictionary=False):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=Config.DATABASE_HOST,
            user=Config.DATABASE_USER,
            password=Config.DATABASE_PASSWORD,
            database=Config.DATABASE_NAME
        )
        cursor = conn.cursor(dictionary=dictionary, buffered=True)
        yield conn, cursor
        conn.commit()
    except Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise DatabaseError("Database operation failed.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            logger.debug("Database connection closed.")

class UserOperation:

    def get_books_for_course(self, course_code):
        try:
            with DatabaseConnection(dictionary=True) as (conn, cursor):
                query = "SELECT title, url FROM books WHERE code = %s"
                cursor.execute(query, (course_code,))
                results = cursor.fetchall()
                logger.info(f"Fetched {len(results)} books for course: {course_code}")
                return results
        except DatabaseError:
            logger.exception("Failed to fetch books for course.")
            return []

    def insert_book(self, code, title, url):
        try:
            with DatabaseConnection() as (conn, cursor):
                query = "INSERT INTO books (code, title, url) VALUES (%s, %s, %s)"
                cursor.execute(query, (code, title, url))
                logger.info(f"Inserted book: {title} for course: {code}")
        except DatabaseError:
            logger.exception("Failed to insert book.")

    def update_book(self, code, old_title, new_title, new_url):
        try:
            with DatabaseConnection() as (conn, cursor):
                query = "UPDATE books SET title = %s, url = %s WHERE code = %s AND title = %s"
                cursor.execute(query, (new_title, new_url, code, old_title))
                updated = cursor.rowcount > 0
                if updated:
                    logger.info(f"Updated book '{old_title}' to '{new_title}' for course: {code}")
                else:
                    logger.warning(f"No book updated for course: {code}, title: {old_title}")
                return updated
        except DatabaseError:
            logger.exception("Failed to update book.")
            return False

    def delete_book(self, code, title):
        try:
            with DatabaseConnection() as (conn, cursor):
                query = "DELETE FROM books WHERE code = %s AND title = %s"
                cursor.execute(query, (code, title))
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted book: {title} from course: {code}")
                else:
                    logger.warning(f"No book deleted for course: {code}, title: {title}")
                return deleted
        except DatabaseError:
            logger.exception("Failed to delete book.")
            return False
