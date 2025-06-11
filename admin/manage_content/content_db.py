import mysql.connector
from config import Config
import logging
from decimal import Decimal # Import Decimal for type checking

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


    def get_content_by_code_title_subtitle(self, course_code, title, subtitle):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            query = """
                SELECT * FROM content
                WHERE code = %s AND title = %s AND subtitle = %s
            """
            cursor.execute(query, (course_code, title, subtitle))
            return cursor.fetchone()
        except Exception as e:
            logger.exception("Error fetching content by code/title/subtitle")
            return None
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def get_course_details(self, course_code):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            query = "SELECT code, name, description FROM courses WHERE code = %s"
            cursor.execute(query, (course_code,))
            return cursor.fetchone()
        except Exception as e:
            logger.exception("Error fetching course details")
            return None
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def get_courses_by_code(self, code):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            query = """
                SELECT * FROM content
                WHERE code = %s AND status = 'active'
                ORDER BY
                    FIELD(section, 'NOTES', 'PRACTICE BOOK', 'PYQ','MOCK TEST'),
                    FIELD(label, 'Free', 'Paid')
            """
            cursor.execute(query, (code,))
            return cursor.fetchall()
        except Exception as e:
            logger.exception("Error fetching courses by code")
            return []
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def get_sections_by_code(self, code):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor()
            query = """
             SELECT DISTINCT section ,section_id
             FROM content
             WHERE code = %s AND status = 'active'
            """
            cursor.execute(query, (code,))
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.exception("Error fetching sections")
            return []
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def get_all_content_entries(self):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM content ORDER BY created_at DESC")
            return cursor.fetchall()
        except Exception as e:
            logger.exception("Error fetching all content entries")
            return []
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def get_content_by_id(self, content_id):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            query = "SELECT * FROM content WHERE id = %s"
            cursor.execute(query, (content_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.exception(f"Error fetching content with ID {content_id}")
            return None
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def get_next_section_id_suffix(self, code, section, label, exclude_content_id=None):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor()
            base_section_id = f"{section.upper().replace(' ', '_')}"
            
            if label == 'Free':
                query = "SELECT COUNT(*) FROM content WHERE code = %s AND section = %s AND label = 'Free'"
                params = (code, section)
                if exclude_content_id:
                    query += " AND id != %s"
                    params += (exclude_content_id,)
                cursor.execute(query, params)
                count = cursor.fetchone()[0]
                if count > 0:
                    return None
                return f"{base_section_id}_1"
            else:
                query = "SELECT MAX(CAST(SUBSTRING_INDEX(section_id, '_', -1) AS UNSIGNED)) FROM content WHERE code = %s AND section = %s AND section_id LIKE %s"
                cursor.execute(query, (code, section, f"{base_section_id}_%"))
                max_suffix = cursor.fetchone()[0]
                next_suffix = 1 if max_suffix is None else max_suffix + 1
                return f"{base_section_id}_{next_suffix}"
        except Exception as e:
            logger.exception(f"Error getting next section_id suffix for section '{section}' and label '{label}'")
            return None
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def insert_content(self, code, title, subtitle, price, details, label, status, image_url, section):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor()

            section_id = self.get_next_section_id_suffix(code, section, label)
            if section_id is False:
                logger.warning(f"Attempted to insert duplicate FREE content for code: {code}, section: {section}")
                return False
            elif section_id is None: # This would be if get_next_section_id_suffix failed internally
                 logger.error(f"Failed to generate section_id for insertion: code={code}, section={section}, label={label}")
                 return None

            query = """
                INSERT INTO content (code, title, subtitle, price, details, label, status, image_url, section, section_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (code, title, subtitle, price, details, label, status, image_url, section, section_id))
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.exception("Error inserting new content")
            if db: db.rollback()
            return None
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def update_content(self, content_id, code, title, subtitle, price, details, label, status, image_url, section, current_section_id_from_db):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor()

            current_content = self.get_content_by_id(content_id)
            if not current_content:
                logger.error(f"Update failed for ID {content_id}: Content not found in DB.")
                return False
            
            current_content = dict(current_content) 

            new_section_id = current_section_id_from_db 

            if current_content['section'] != section or current_content['label'] != label:
                calculated_section_id = self.get_next_section_id_suffix(code, section, label, exclude_content_id=content_id)
                
                if calculated_section_id is None and label == 'Free':
                    logger.warning(f"Update blocked for ID {content_id}: Attempted to change to FREE content for code: {code}, section: {section}, but a FREE entry already exists. No update performed.")
                    return False
                
                if calculated_section_id:
                     new_section_id = calculated_section_id
                
            query = """
                UPDATE content SET
                code = %s, title = %s, subtitle = %s, price = %s, details = %s,
                label = %s, status = %s, image_url = %s, section = %s, section_id = %s
                WHERE id = %s
            """
            params = (code, title, subtitle, price, details, label, status, image_url, section, new_section_id, content_id)
            
            cursor.execute(query, params)
            db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Error updating content with ID {content_id}. Rolling back transaction.")
            if db: db.rollback()
            return False
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def delete_content(self, content_id):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor()
            query = "DELETE FROM content WHERE id = %s"
            cursor.execute(query, (content_id,))
            db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.exception(f"Error deleting content with ID {content_id}")
            if db: db.rollback()
            return False
        finally:
            if cursor: cursor.close()
            if db: db.close()