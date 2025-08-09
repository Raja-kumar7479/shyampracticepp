import logging
import mysql.connector
from mysql.connector import Error
from app import db_pool

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class UserOperation:
    def __init__(self):
        if db_pool is None:
            raise Exception("Database connection pool is not initialized.")

    def count_courses(self):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(buffered=True)
            cursor.execute("SELECT COUNT(*) FROM courses")
            result = cursor.fetchone()
            return result[0] if result else 0
        except mysql.connector.Error as err:
            logger.error(f"Error counting courses: {err}")
            return 0
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_courses_paginated(self, limit=10, offset=0):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = "SELECT code, name, description FROM courses ORDER BY name ASC LIMIT %s OFFSET %s"
            cursor.execute(query, (limit, offset))
            results = cursor.fetchall()
            logger.info(f"Fetched {len(results)} courses with limit {limit} and offset {offset}.")
            return results
        except mysql.connector.Error as err:
            logger.error(f"Error fetching paginated courses: {err}")
            raise err
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_all_courses(self):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT code, name, description FROM courses ORDER BY name ASC")
            results = cursor.fetchall()
            logger.info("Fetched all courses successfully.")
            return results
        except mysql.connector.Error as err:
            logger.error(f"Error fetching all courses: {err}")
            raise err
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_course_by_code(self, code):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute("SELECT code, name, description FROM courses WHERE code = %s", (code,))
            result = cursor.fetchone()
            return result
        except mysql.connector.Error as err:
            logger.error(f"Error fetching course '{code}': {err}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def insert_course(self, code, name, description):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(buffered=True)
            cursor.execute(
                "INSERT INTO courses (code, name, description) VALUES (%s, %s, %s)",
                (code, name, description)
            )
            conn.commit()
            return True
        except mysql.connector.Error as err:
            logger.error(f"Error inserting course '{code}': {err}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def update_course(self, code, name, description):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(buffered=True)
            cursor.execute(
                "UPDATE courses SET name = %s, description = %s WHERE code = %s",
                (name, description, code)
            )
            conn.commit()
            return cursor.rowcount > 0
        except mysql.connector.Error as err:
            logger.error(f"Error updating course '{code}': {err}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def delete_course(self, code):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(buffered=True)
            cursor.execute("DELETE FROM courses WHERE code = %s", (code,))
            conn.commit()
            return cursor.rowcount > 0
        except mysql.connector.Error as err:
            logger.error(f"Error deleting course '{code}': {err}")
            if conn:
                conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()