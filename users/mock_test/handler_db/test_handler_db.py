import logging
from users.mock_test.handler_db.user_db import UserOperation

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

user_op = UserOperation()

class TestHandler:

    def complete_user_test(self, email, test_id, device_info, attempt_number=1):
        try:
            query = """
                UPDATE user_test_log
                SET status = 'completed',
                    end_time = NOW(),
                    device_info = %s,
                    attempt_number = %s
                WHERE email = %s AND test_id = %s
            """
            user_op.execute_query(query, (device_info, attempt_number, email, test_id))
            logger.debug(f"Marked test as completed for {email} on test {test_id}")
        except Exception as e:
            logger.exception(f"Failed to update test completion for {email}, test {test_id}")

    def _get_total_marks_for_test(self, test_id):
        """Helper to fetch the total possible marks for a test."""
        try:
            query = "SELECT SUM(correct_marks) as total_marks FROM test_questions WHERE test_id = %s"
            result = user_op.fetch_one(query, (test_id,))
            return float(result['total_marks']) if result and result['total_marks'] is not None else 0.0
        except Exception as e:
            logger.exception(f"Error fetching total marks for test_id: {test_id}")
            return 0.0
        
    def _calculate_percentage(self, net_score, total_test_marks):
        """Helper to calculate percentage."""
        if total_test_marks is None or total_test_marks == 0:
            return 0.0
        try:
            percentage = (float(net_score) / float(total_test_marks)) * 100
            return round(percentage, 2)
        except TypeError:
            return 0.0
        
    def _calculate_submission_ranker(self, cursor, test_id, net_score, total_time_taken_seconds):
        try:
            query = """
                SELECT COUNT(1) + 1 AS submission_ranker_value
                FROM test_result
                WHERE test_id = %s AND
                      (net_score > %s OR (net_score = %s AND total_time_taken_seconds < %s))
            """
            current_net_score = float(net_score)
            current_time_seconds = int(total_time_taken_seconds)

            cursor.execute(query, (test_id, current_net_score, current_net_score, current_time_seconds))
            ranker_result_row = cursor.fetchone() 
            
            if ranker_result_row and 'submission_ranker_value' in ranker_result_row and ranker_result_row['submission_ranker_value'] is not None:
                 return int(ranker_result_row['submission_ranker_value'])
            elif ranker_result_row and isinstance(ranker_result_row, tuple) and ranker_result_row[0] is not None: # if cursor not dictionary=True
                return int(ranker_result_row[0])
            return 1 
        except Exception as e:
            logger.exception(f"Error calculating submission ranker for test_id {test_id}: {e}")
            return 1 
    
    def _save_test_attempt_details(self, cursor, test_id, email, processed_attempt_details):
        details_query = """
           INSERT INTO test_attempt_details (
               test_id, question_id, user_selected_option, user_written_answer,
               is_correct, marks_awarded, status_of_attempt, time_spent_on_question_seconds, email
           ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            for detail in processed_attempt_details:
                cursor.execute(details_query, (
                    test_id, detail['question_id'],
                    detail['user_selected_option'], detail['user_written_answer'],
                    detail['is_correct'], detail['marks_awarded'],
                    detail['status_of_attempt'], detail['time_spent_on_question_seconds'], email
                ))
        except Exception as e:
            logger.exception(f"Error in _save_test_attempt_details for user {email}, test {test_id}: {e}")
            raise 

    def _process_user_answer(self, user_answer, question_details):
        question_id = user_answer.get('question_id')
        user_selected_option = user_answer.get('selected_option')
        user_written_answer = user_answer.get('written_answer')
        time_spent_q = user_answer.get('time_spent_on_question', 0)
        client_status = user_answer.get('status_from_client', 'not_visited')

        if isinstance(user_selected_option, list):
            user_selected_option = ",".join(sorted(str(opt).strip().lower() for opt in user_selected_option))
        elif user_selected_option is not None:
            user_selected_option = str(user_selected_option).strip()

        if isinstance(user_written_answer, list): 
            user_written_answer = ",".join(sorted(str(ans).strip().lower() for ans in user_written_answer))
        elif user_written_answer is not None:
             user_written_answer = str(user_written_answer).strip()

        is_attempted = False
        if client_status in ['answered', 'answered_review', 'correct', 'incorrect']: 
             is_attempted = True
        elif user_selected_option or user_written_answer: 
             is_attempted = True

        marks_awarded_for_q = 0.0
        is_correct_q = None 
        status_of_attempt = client_status 

        if is_attempted:
            correct_db_option = question_details.get('correct_option')
            q_type = question_details.get('question_type')

            if correct_db_option is not None:
                correct_db_option = str(correct_db_option).strip().lower()
            
            user_provided_answer = None
            if q_type in ['MCQ', 'NAT']: 
                 user_provided_answer = str(user_selected_option or user_written_answer or "").strip().lower()
                 is_correct_q = user_provided_answer == correct_db_option
            elif q_type == 'MSQ':
                user_ans_msq = sorted(str(user_selected_option or "").strip().lower().split(',')) if user_selected_option else []
                user_ans_msq = [opt for opt in user_ans_msq if opt] 
                correct_ans_msq = sorted(str(correct_db_option or "").strip().lower().split(',')) if correct_db_option else []
                correct_ans_msq = [opt for opt in correct_ans_msq if opt]
                is_correct_q = user_ans_msq == correct_ans_msq and bool(user_ans_msq) 

            if is_correct_q is True: 
                marks_awarded_for_q = float(question_details.get('correct_marks', 0))
                status_of_attempt = 'correct'
            else: 
                negative_marks_val = float(question_details.get('negative_marks', 0))
                marks_awarded_for_q = -negative_marks_val 
                status_of_attempt = 'incorrect'
        else: 
            marks_awarded_for_q = 0.0 
            is_correct_q = None 
            if client_status not in ['not_visited', 'not_answered', 'marked_review']:
                status_of_attempt = 'unattempted'
            elif client_status == 'marked_review' and not (user_selected_option or user_written_answer):
                status_of_attempt = 'marked_review'

        return {
            'question_id': question_id,
            'user_selected_option': user_selected_option,
            'user_written_answer': user_written_answer,
            'is_correct': is_correct_q, 
            'marks_awarded': marks_awarded_for_q,
            'status_of_attempt': status_of_attempt,
            'time_spent_on_question_seconds': time_spent_q,
            'is_attempted': is_attempted,
            'is_correct_flag': is_correct_q is True 
        }

    def _calculate_test_summary(self, total_questions_in_test, processed_answers):
        attempted_questions_count = sum(1 for a in processed_answers if a['is_attempted'])
        correctly_answered_count = sum(1 for a in processed_answers if a['is_correct_flag'] is True) 
        
        incorrectly_answered_count = 0
        for ans in processed_answers:
            if ans['is_attempted'] and ans['is_correct_flag'] is False:
                incorrectly_answered_count +=1

        marks_for_correct = sum(a['marks_awarded'] for a in processed_answers if a['is_correct_flag'] is True)
        penalty_for_incorrect = sum(a['marks_awarded'] for a in processed_answers if a['is_attempted'] and a['is_correct_flag'] is False)

        net_score = marks_for_correct + penalty_for_incorrect 
        accuracy = (correctly_answered_count / attempted_questions_count * 100) if attempted_questions_count > 0 else 0.0
        unattempted_questions_count = total_questions_in_test - attempted_questions_count

        return {
            'attempted_questions_count': attempted_questions_count,
            'unattempted_questions_count': unattempted_questions_count,
            'correctly_answered_questions_count': correctly_answered_count,
            'incorrectly_answered_questions_count': incorrectly_answered_count,
            'marks_for_correct_answers': round(marks_for_correct, 2),
            'penalty_for_incorrect_answers': round(abs(penalty_for_incorrect), 2), 
            'net_score': round(net_score, 2),
            'accuracy': round(accuracy, 2)
        }

    def _save_test_result_summary(self, cursor, email, username, test_id,
                                  total_time_taken_seconds, summary_data,
                                  percentage, submission_ranker_value): # Changed submission_rank to submission_ranker_value
        
        result_query = """
            INSERT INTO test_result (
                email, username, test_id, attempted_questions_count,
                unattempted_questions_count, correctly_answered_questions_count,
                incorrectly_answered_questions_count, marks_for_correct_answers,
                penalty_for_incorrect_answers, net_score, accuracy,
                percentage, submission_ranker,  -- Changed column name
                total_time_taken_seconds, submission_timestamp
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        try:
            cursor.execute(result_query, (
                email, username, test_id,
                summary_data['attempted_questions_count'],
                summary_data['unattempted_questions_count'],
                summary_data['correctly_answered_questions_count'],
                summary_data['incorrectly_answered_questions_count'],
                summary_data['marks_for_correct_answers'],
                summary_data['penalty_for_incorrect_answers'],
                summary_data['net_score'],
                summary_data['accuracy'],
                percentage,  
                submission_ranker_value, 
                total_time_taken_seconds
            ))
            return cursor.lastrowid
        except Exception as e:
            logger.exception(f"Error in _save_test_result_summary for user {email}, test {test_id}: {e}")
            raise 

    def save_test_submission(self, email, username, test_id, submitted_data):
        db_connection = None
        cursor = None
        try:
            if str(test_id) != str(submitted_data.get('test_id')): 
                logger.error(f"Mismatched test_id in route ({test_id}) and payload ({submitted_data.get('test_id')}).")
                return None, "Test ID mismatch."

            user_answers_from_client = submitted_data.get('answers', [])
            total_time_taken_seconds = submitted_data.get('total_time_taken', 0)

            all_test_questions_raw = user_op.get_all_test_questions(test_id)
            if not all_test_questions_raw:
                logger.error(f"No questions found for test_id {test_id} during submission processing.")
                return None, "Could not retrieve test questions for grading."

            question_details_map = {q['id']: q for q in all_test_questions_raw}
            processed_attempt_details = []

            for ua_client in user_answers_from_client:
                question_id = ua_client.get('question_id')
                q_master_details = question_details_map.get(question_id)

                if not q_master_details:
                    logger.warning(f"Skipping answer for unknown question_id {question_id} in test {test_id}")
                    continue
               
                processed_detail = self._process_user_answer(ua_client, q_master_details)
                processed_attempt_details.append(processed_detail)

            summary_data = self._calculate_test_summary(len(all_test_questions_raw), processed_attempt_details)

            total_test_marks = self._get_total_marks_for_test(test_id)
            calculated_percentage = self._calculate_percentage(summary_data['net_score'], total_test_marks)
            
            db_connection = user_op.connection()
            cursor = db_connection.cursor(dictionary=True) # Ensure dictionary cursor for _calculate_submission_ranker
            db_connection.start_transaction()

            submission_ranker_value = self._calculate_submission_ranker( # Renamed variable
                cursor, 
                test_id,
                summary_data['net_score'],
                total_time_taken_seconds
            )
            
            test_result_id = self._save_test_result_summary(
                cursor, email, username, test_id,
                total_time_taken_seconds, summary_data,
                calculated_percentage, submission_ranker_value # Pass renamed variable
            )

            if not test_result_id: 
                db_connection.rollback()
                logger.error("Failed to get lastrowid for test_result insertion (or error in save).")
                return None, "Database error during result summary saving."

            self._save_test_attempt_details(cursor, test_id, email, processed_attempt_details)
           
            db_connection.commit()
           
            self.complete_user_test(email, test_id, device_info="Submitted via web", attempt_number=1)

            logger.info(f"Test submission for user {email}, test {test_id} saved. Result ID: {test_result_id}, Percentage: {calculated_percentage}%, Submission Ranker: {submission_ranker_value}")
            return test_id, None 
        except Exception as e:
            if db_connection:
                db_connection.rollback()
            logger.exception(f"Error saving test submission for user {email}, test {test_id}: {e}")
            return None, str(e)
        finally:
            if cursor:
                cursor.close()
            if db_connection:
                db_connection.close()
