import logging
import mysql.connector
from config import Config


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class UserOperation:
    def connection(self):
        """Establish and return a new database connection"""
        return mysql.connector.connect(
            host=Config.DATABASE_HOST,
            user=Config.DATABASE_USER,
            password=Config.DATABASE_PASSWORD,
            database=Config.DATABASE_NAME
        )

    def get_user_unique_code(self, email, course_code):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                "SELECT unique_code FROM enrollment WHERE email = %s AND code = %s",
                (email, course_code)
            )
            result = cursor.fetchone()
            return result['unique_code'] if result else None
        except Exception as e:
            logging.exception("Error in get_user_unique_code")
            return None
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def get_all_active_coupons(self, email=None):
        try:
            db = self.connection()
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
        except Exception:
            logging.exception("Error in get_all_active_coupons")
            return []
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def get_coupon_by_code(self, code, email=None):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT * FROM coupone
                WHERE coupon_code = %s
                  AND status = 1
                  AND (email IS NULL OR email = %s)
                  AND (valid_until IS NULL OR valid_until > NOW())
                  AND (expiry_date IS NULL OR expiry_date > NOW())
                """,
                (code, email)
            )
            return cursor.fetchall()
        except Exception:
            logging.exception("Error in get_coupon_by_code")
            return []
        finally:
            if cursor: cursor.close()
            if db: db.close()
    
    def add_purchase_transactional(self, purchases_data):
        """
        Adds multiple purchases within a single database transaction.
        Rolls back all insertions if any single insertion fails.
        """
        db = self.connection()
        cursor = db.cursor(buffered=True)
        try:
            db.start_transaction()
            for purchase_data in purchases_data:
                cursor.execute(
                    """
                    INSERT INTO purchase (
                        email, username, phone, title, subtitle, price, original_price,
                        discount_percent, final_price, payment_date, payment_id, status,
                        purchase_code, course_code, section, section_id, payment_mode
                    )
                    VALUES (%(email)s, %(username)s, %(phone)s, %(title)s, %(subtitle)s, %(price)s, %(original_price)s,
                            %(discount_percent)s, %(final_price)s, %(payment_date)s, %(payment_id)s, %(status)s,
                            %(purchase_code)s, %(course_code)s, %(section)s, %(section_id)s, %(payment_mode)s)
                    """,
                    purchase_data
                )
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logging.exception(f"Error in add_purchase_transactional for payment_id {purchases_data[0].get('payment_id')}: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if db:
                db.close()

    def get_all_purchases(self, email):
        try:
            db= self.connection()
            cursor = db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT title, subtitle, price, payment_date, payment_id, phone, section, section_id, status, payment_mode
                FROM purchase
                WHERE email = %s
                ORDER BY section_id ASC, payment_date DESC
                """,
                (email,)
            )
            return cursor.fetchall()
        except Exception:
            logging.exception("Error in get_all_purchases")
            return []
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def get_content_by_code_title_subtitle(self, course_code, title, subtitle):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT * FROM content
                WHERE code = %s AND title = %s AND subtitle = %s
                """,
                (course_code, title, subtitle)
            )
            return cursor.fetchone()
        except Exception:
            logging.exception("Error in get_content_by_code_title_subtitle")
            return None
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def is_course_purchased_securely(self, email, course_code, title, subtitle):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                """
                SELECT status, purchase_code
                FROM purchase
                WHERE email = %s AND course_code = %s AND title = %s AND subtitle = %s AND status = 'Paid'
                """,
                (email, course_code, title, subtitle)
            )
            results = cursor.fetchall()
            return results[0] if results else None
        except Exception:
            logging.exception("Error in is_course_purchased_securely")
            return None
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def get_purchase_by_payment_id(self, email, payment_id):
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True, buffered=True)
            cursor.execute(
                "SELECT * FROM purchase WHERE email = %s AND payment_id = %s",
                (email, payment_id)
            )
            result = cursor.fetchall()
            return result if result else None
        except Exception:
            logging.exception("Error in get_purchase_by_payment_id")
            return None
        finally:
            if cursor: cursor.close()
            if db: db.close()
    
    