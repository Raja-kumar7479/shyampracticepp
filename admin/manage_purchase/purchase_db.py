import logging
import mysql.connector
from mysql.connector import Error
from app import db_pool

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class PurchaseOperation:
    def __init__(self):
        if db_pool is None:
            raise Exception("Database connection pool is not initialized.")

    def _get_connection(self):
        return db_pool.get_connection()

    def get_all_purchase_details(self):
        db = None
        cursor = None
        try:
            db = self._get_connection()
            cursor = db.cursor(dictionary=True, buffered=True)
            query = """
                SELECT id, email, username, phone, course_code, title, subtitle, price,
                        original_price, discount_percent, final_price, payment_id,
                        payment_mode, payment_date, purchase_code, status
                FROM purchase
                ORDER BY payment_date DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error in get_all_purchase_details: {e}", exc_info=True)
            return []
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    def get_purchase_by_email_and_payment_id(self, email, payment_id):
        db = None
        cursor = None
        try:
            db = self._get_connection()
            cursor = db.cursor(dictionary=True, buffered=True)
            query = """
                SELECT id, email, username, phone, course_code, title, subtitle, price,
                        original_price, discount_percent, final_price, payment_id,
                        payment_mode, payment_date, purchase_code, status
                FROM purchase
                WHERE email = %s AND payment_id = %s
            """
            cursor.execute(query, (email, payment_id))
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error in get_purchase_by_email_and_payment_id: {e}", exc_info=True)
            return None
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    def delete_purchase_by_id(self, purchase_id):
        db = None
        cursor = None
        try:
            db = self._get_connection()
            cursor = db.cursor(buffered=True)
            cursor.execute("DELETE FROM purchase WHERE id = %s AND status = 'Pending'", (purchase_id,))
            db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting purchase with ID: {purchase_id}", exc_info=True)
            if db:
                db.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()