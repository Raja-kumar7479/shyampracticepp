from venv import logger
import mysql.connector
from config import Config

class UserOperation:

    def connection(self):
        return mysql.connector.connect(
            host=Config.DATABASE_HOST,
            user=Config.DATABASE_USER,
            password=Config.DATABASE_PASSWORD,
            database=Config.DATABASE_NAME
        )

    def get_all_study_materials(self):
        query = "SELECT * FROM study_materials"
        return self._fetch_all(query)

    def is_test_id_or_key_or_code_duplicate(self, test_id, test_key, test_code, material_id=None):
        query = "SELECT id FROM study_materials WHERE (test_id = %s OR test_key = %s OR test_code = %s)"
        params = [test_id, test_key, test_code]
        if material_id:
            query += " AND id != %s"
            params.append(material_id)
        return self._fetch_one(query, tuple(params))

    def insert_study_material(self, data):
        query = """
            INSERT INTO study_materials
            (name, code, status, label, stream, test_id, test_key, test_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            data['name'], data['code'], data['status'], data['label'],
            data['stream'], data['test_id'], data['test_key'], data['test_code']
        )
        self._execute_query(query, params)

    def update_study_material_field(self, id, field, value):
        # Basic whitelist for fields to prevent direct injection of column names
        allowed_fields = ['name', 'code', 'status', 'label', 'stream', 'test_id', 'test_key', 'test_code']
        if field not in allowed_fields:
            raise ValueError(f"Invalid field for update: {field}")
        query = f"UPDATE study_materials SET {field} = %s WHERE id = %s"
        self._execute_query(query, (value, id))

    def delete_study_material(self, id):
        query = "DELETE FROM study_materials WHERE id = %s"
        self._execute_query(query, (id,))

    def get_test_descriptions_by_test_id(self, test_id):
        query = "SELECT * FROM test_description WHERE test_id = %s ORDER BY test_number"
        return self._fetch_all(query, (test_id,))

    def get_all_test_descriptions(self):
        query = "SELECT * FROM test_description ORDER BY test_id, test_number"
        return self._fetch_all(query)

    def get_max_test_number(self, test_id):
        query = "SELECT MAX(test_number) as max_num FROM test_description WHERE test_id = %s"
        result = self._fetch_one(query, (test_id,))
        return result['max_num'] if result and result['max_num'] is not None else 0

    def insert_test_description(self, data):
        query = """
            INSERT INTO test_description
            (test_id, test_number, subject_title, subject_subtitle, year,
             total_questions, total_marks, total_duration_minutes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            data['test_id'], data['test_number'], data['subject_title'],
            data['subject_subtitle'], data['year'], data['total_questions'],
            data['total_marks'], data['total_duration_minutes']
        )
        self._execute_query(query, params)
    def delete_test_question(self, id):
        query = "DELETE FROM test_questions WHERE id = %s"
        self._execute_query(query, (id,))
        
    def update_test_description_field(self, id, field, value):
        allowed_fields = ['test_number', 'subject_title', 'subject_subtitle', 'year', 'total_questions', 'total_marks', 'total_duration_minutes']
        if field not in allowed_fields:
            raise ValueError(f"Invalid field for update: {field}")
        query = f"UPDATE test_description SET {field} = %s WHERE id = %s"
        self._execute_query(query, (value, id))

    def delete_test_description(self, id):
        query = "DELETE FROM test_description WHERE id = %s"
        self._execute_query(query, (id,))

    def get_test_questions_by_test_id(self, test_id):
        query = "SELECT * FROM test_questions WHERE test_id = %s ORDER BY section_id, question_number"
        return self._fetch_all(query, (test_id,))

    def get_total_questions_count_for_test_id(self, test_id):
        query = "SELECT COUNT(*) as count FROM test_questions WHERE test_id = %s"
        result = self._fetch_one(query, (test_id,))
        return result['count'] if result else 0

    def get_max_question_number_in_section(self, test_id, section_id):
        query = "SELECT MAX(question_number) as max_num FROM test_questions WHERE test_id = %s AND section_id = %s"
        result = self._fetch_one(query, (test_id, section_id))
        return result['max_num'] if result and result['max_num'] is not None else 0

    def insert_test_question(self, data):
        query = """
            INSERT INTO test_questions
            (test_id, section_id, section_name, question_number, question_type, question_text,
             question_image, option_a, option_b, option_c, option_d, correct_option,
             correct_marks, negative_marks, question_level, answer_text, answer_link,
             answer_image, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        params = (
            data['test_id'], data['section_id'], data['section_name'], data['question_number'],
            data['question_type'], data['question_text'], data.get('question_image'),
            data.get('option_a'), data.get('option_b'), data.get('option_c'), data.get('option_d'),
            data['correct_option'], data['correct_marks'], data['negative_marks'],
            data['question_level'], data.get('answer_text'), data.get('answer_link'),
            data.get('answer_image')
        )
        self._execute_query(query, params)

    def update_test_question_field(self, id, field, value):
        allowed_fields = [
            'section_id', 'section_name', 'question_type', 'question_text',
            'question_image', 'option_a', 'option_b', 'option_c', 'option_d',
            'correct_option', 'correct_marks', 'negative_marks', 'question_level',
            'answer_text', 'answer_link', 'answer_image'
        ]
        if field not in allowed_fields:
            raise ValueError(f"Invalid field for update: {field}")
        query = f"UPDATE test_questions SET {field} = %s, updated_at = NOW() WHERE id = %s"
        self._execute_query(query, (value, id))

    def _fetch_one(self, query, params=None):
        conn = self.connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def _fetch_all(self, query, params=None):
        conn = self.connection()
        cursor = conn.cursor(dictionary=True, buffered=True)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def _execute_query(self, query, params=None):
        conn = self.connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
        except mysql.connector.Error as err:
            conn.rollback()
            raise err
        finally:
            cursor.close()
            conn.close()

    # test_feedback user op 

    def get_all_feedback_entries(self):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM test_feedback ORDER BY submission_time DESC")
            return cursor.fetchall()
        except Exception as e:
            logger.exception("Error fetching all feedback entries")
            return []
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def truncate_all_feedback(self):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor()
            cursor.execute("TRUNCATE TABLE test_feedback")
            db.commit()
            return True
        except Exception as e:
            logger.exception("Error truncating test_feedback table")
            if db: db.rollback()
            return False
        finally:
            if cursor: cursor.close()
            if db: db.close()
    
    def get_selected_user_test_logs(self):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor(dictionary=True)
            query = "SELECT email, username, test_id, start_time, end_time FROM user_test_log ORDER BY start_time DESC"
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            logger.exception("Error fetching selected user test logs")
            return []
        finally:
            if cursor: cursor.close()
            if db: db.close()

    def count_unique_test_attempts(self):
        db = None
        cursor = None
        try:
            db = self.connection()
            cursor = db.cursor()
            query = "SELECT COUNT(DISTINCT email, test_id) FROM user_test_log"
            cursor.execute(query)
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            logger.exception("Error counting unique test attempts")
            return 0
        finally:
            if cursor: cursor.close()
            if db: db.close()