import logging
import mysql.connector
from config import Config
from contextlib import closing

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

    def get_all_courses(self):
        try:
            with closing(self.connection()) as db, closing(db.cursor(dictionary=True, buffered=True)) as cursor:
                cursor.execute("SELECT * FROM courses")
                results = cursor.fetchall()
                logging.info("Fetched all courses successfully.")
                return results
        except mysql.connector.Error as err:
            logging.error(f"Error fetching all courses: {err}")
            return []

    def get_course_by_code(self, code):
        try:
            with closing(self.connection()) as db, closing(db.cursor(dictionary=True, buffered=True)) as cursor:
                cursor.execute("SELECT * FROM courses WHERE code = %s", (code,))
                result = cursor.fetchone()
                logging.info(f"Fetched course with code '{code}'.")
                return result
        except mysql.connector.Error as err:
            logging.error(f"Error fetching course '{code}': {err}")
            return None

    def insert_course(self, code, name, description):
        try:
            with closing(self.connection()) as db, closing(db.cursor(buffered=True)) as cursor:
                cursor.execute(
                    "INSERT INTO courses (code, name, description) VALUES (%s, %s, %s)",
                    (code, name, description)
                )
                db.commit()
                logging.info(f"Inserted course '{code}' successfully.")
                return True
        except mysql.connector.Error as err:
            logging.error(f"Error inserting course '{code}': {err}")
            return False

    def update_course(self, code, name, description):
        try:
            with closing(self.connection()) as db, closing(db.cursor(buffered=True)) as cursor:
                cursor.execute(
                    "UPDATE courses SET name = %s, description = %s WHERE code = %s",
                    (name, description, code)
                )
                db.commit()
                logging.info(f"Updated course '{code}' successfully.")
                return True
        except mysql.connector.Error as err:
            logging.error(f"Error updating course '{code}': {err}")
            return False

    def delete_course(self, code):
        try:
            with closing(self.connection()) as db, closing(db.cursor(buffered=True)) as cursor:
                cursor.execute("DELETE FROM courses WHERE code = %s", (code,))
                db.commit()
                logging.info(f"Deleted course '{code}' successfully.")
                return True
        except mysql.connector.Error as err:
            logging.error(f"Error deleting course '{code}': {err}")
            return False
