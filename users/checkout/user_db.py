import logging
from mysql.connector import Error
from app import db_pool

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class UserOperation: 
  
    def get_user_unique_code(self, email, course_code):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = "SELECT unique_code FROM enrollment WHERE email = %s AND code = %s"
            cursor.execute(query, (email, course_code))
            result = cursor.fetchone()
            return result['unique_code'] if result else None
        except Error as e:
            logger.error(f"Error getting unique code for {email}/{course_code}: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_all_active_coupons(self, email=None):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            if email:
                query = """
                    SELECT * FROM coupone WHERE status = 1
                      AND (email IS NULL OR email = %s)
                      AND (valid_until IS NULL OR valid_until > NOW())
                      AND (expiry_date IS NULL OR expiry_date > NOW())
                """
                cursor.execute(query, (email,))
            else:
                query = """
                    SELECT * FROM coupone WHERE status = 1
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
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_coupon_by_code(self, code, email=None):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = """
                SELECT * FROM coupone WHERE coupon_code = %s AND status = 1
                  AND (email IS NULL OR email = %s)
                  AND (valid_until IS NULL OR valid_until > NOW())
                  AND (expiry_date IS NULL OR expiry_date > NOW())
            """
            cursor.execute(query, (code, email))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error getting coupon by code '{code}': {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def add_purchase_transactional(self, purchases_data):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(buffered=True)
            conn.start_transaction()
            query = """
                INSERT INTO purchase (
                    email, username, phone, title, subtitle, price, original_price,
                    discount_percent, final_price, payment_date, payment_id, status,
                    purchase_code, course_code, section, section_id, payment_mode
                ) VALUES (
                    %(email)s, %(username)s, %(phone)s, %(title)s, %(subtitle)s, %(price)s,
                    %(original_price)s, %(discount_percent)s, %(final_price)s, %(payment_date)s,
                    %(payment_id)s, %(status)s, %(purchase_code)s, %(course_code)s,
                    %(section)s, %(section_id)s, %(payment_mode)s
                )
            """
            for purchase_data in purchases_data:
                cursor.execute(query, purchase_data)
            conn.commit()
            return True
        except Error as e:
            if conn: conn.rollback()
            payment_id = purchases_data[0].get('payment_id') if purchases_data else 'N/A'
            logger.error(f"Transactional error for payment_id {payment_id}: {e}")
            return False
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_all_purchases(self, email):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = """
                SELECT p.*, cc.validity_expires_at FROM purchase AS p
                LEFT JOIN course_content AS cc ON p.section_id = cc.section_id
                WHERE p.email = %s
                ORDER BY p.section_id ASC, p.payment_date DESC
            """
            cursor.execute(query, (email,))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error getting all purchases for {email}: {e}")
            return []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_content_by_code_title_subtitle(self, course_code, title, subtitle):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = "SELECT * FROM course_content WHERE code = %s AND title = %s AND subtitle = %s"
            cursor.execute(query, (course_code, title, subtitle))
            return cursor.fetchone()
        except Error as e:
            logger.error(f"Error getting content by code/title/subtitle: {e}")
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
                WHERE email = %s AND course_code = %s AND title = %s
                  AND subtitle = %s AND status = 'Paid'
            """
            cursor.execute(query, (email, course_code, title, subtitle))
            results = cursor.fetchall()
            return results[0] if results else None
        except Error as e:
            logger.error(f"Error checking secure purchase for {email}: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def get_purchase_by_payment_id(self, email, payment_id):
        conn = None
        cursor = None
        try:
            conn = db_pool.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            query = "SELECT * FROM purchase WHERE email = %s AND payment_id = %s"
            cursor.execute(query, (email, payment_id))
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Error getting purchase by payment_id {payment_id}: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
