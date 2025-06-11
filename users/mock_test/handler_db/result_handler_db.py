import logging
from users.mock_test.handler_db.user_db import UserOperation
from bs4 import BeautifulSoup
from flask import url_for, current_app

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

user_op = UserOperation()

class ResultHandler:
    def _get_total_marks_for_test(self, test_id):
        try:
            query = "SELECT SUM(correct_marks) as total_marks FROM test_questions WHERE test_id = %s"
            result = user_op.fetch_one(query, (test_id,))
            return float(result['total_marks']) if result and result['total_marks'] is not None else 0.0
        except Exception as e:
            logger.exception(f"Error fetching total marks for test_id: {test_id}")
            return 0.0
            
    def _calculate_percentage(self, net_score, total_test_marks):
        if total_test_marks is None or total_test_marks == 0:
            return 0.0
        try:
            percentage = (float(net_score) / float(total_test_marks)) * 100
            return round(percentage, 2)
        except TypeError:
            return 0.0

    def _calculate_width_percentage(self, value, max_value):
        if max_value is None or max_value == 0:
            return 0.0
        try:
            percentage = (float(value) / float(max_value)) * 100
            return round(percentage, 2)
        except (TypeError, ValueError):
            logger.warning(f"Could not calculate width percentage for value: {value}, max_value: {max_value}")
            return 0.0

    def _process_html_content_for_images(self, html_content):
        if not html_content:
            return html_content
        soup = BeautifulSoup(html_content, 'html.parser')
        for img_tag in soup.find_all('img'):
            src = img_tag.get('src')
            if src and not src.startswith(('http://', 'https://', 'data:')):
                if src.startswith('/static/'):
                    filename_path = src[len('/static/'):]
                elif src.startswith('static/'):
                    filename_path = src[len('static/'):]
                else:
                    filename_path = src 
                try:
                    with current_app.app_context():
                        updated_src = url_for('static', filename=filename_path)
                    img_tag['src'] = updated_src
                except RuntimeError as e:
                    logger.warning(f"Could not resolve URL for static file {filename_path} (RuntimeError: {e}).")
        return str(soup)

    def get_topper_list(self, test_id, limit=10):
        try:
            query = """
                SELECT username, net_score, total_time_taken_seconds, accuracy,
                        attempted_questions_count, percentage
                FROM test_result
                WHERE test_id = %s
                ORDER BY net_score DESC, total_time_taken_seconds ASC
                LIMIT %s
            """
            results = user_op.fetch_all(query, (test_id, limit))

            toppers_with_ranker = []
            for i, row_dict in enumerate(results):
                topper = dict(row_dict) 
                topper['ranker'] = i + 1 
                topper['net_score'] = float(topper.get('net_score', 0.0))
                topper['accuracy'] = float(topper.get('accuracy', 0.0))
                topper['percentage'] = float(topper.get('percentage', 0.0))
                toppers_with_ranker.append(topper)
            return toppers_with_ranker
        except Exception as e:
            logger.exception(f"Error fetching topper list for test_id: {test_id}")
            return []

    def get_average_and_topper_performance(self, test_id):
        try:
            query_avg = """
                SELECT AVG(accuracy) as avg_accuracy, AVG(total_time_taken_seconds) as avg_time
                FROM test_result WHERE test_id = %s
            """
            avg_data = user_op.fetch_one(query_avg, (test_id,))

            query_topper = """
                SELECT accuracy, total_time_taken_seconds, net_score
                FROM test_result WHERE test_id = %s
                ORDER BY net_score DESC, total_time_taken_seconds ASC LIMIT 1
            """
            topper_data = user_op.fetch_one(query_topper, (test_id,))

            return {
                "average_accuracy": float(avg_data['avg_accuracy']) if avg_data and avg_data['avg_accuracy'] is not None else 0.0,
                "average_time": float(avg_data['avg_time']) if avg_data and avg_data['avg_time'] is not None else 0.0,
                "topper_accuracy": float(topper_data['accuracy']) if topper_data and topper_data['accuracy'] is not None else 0.0,
                "topper_time": float(topper_data['total_time_taken_seconds']) if topper_data and topper_data['total_time_taken_seconds'] is not None else 0.0,
            }
        except Exception as e:
            logger.exception(f"Error fetching average and topper performance for test_id: {test_id}")
            return {"average_accuracy": 0.0, "average_time": 0.0, "topper_accuracy": 0.0, "topper_time": 0.0}
    
    def get_test_summary_details(self, test_id, email):
        try:
            overall_summary = user_op.fetch_one("""
                SELECT tr.*, td.subject_title, td.subject_subtitle, td.total_questions AS test_total_questions
                FROM test_result tr
                JOIN test_description td ON tr.test_id = td.test_id
                WHERE tr.test_id = %s AND tr.email = %s
            """, (test_id, email))

            if not overall_summary:
                logger.warning(f"No test result found for test_id={test_id} and email={email}")
                return None

            overall_summary['net_score'] = float(overall_summary.get('net_score', 0.0))
            overall_summary['accuracy'] = float(overall_summary.get('accuracy', 0.0))
            overall_summary['total_time_taken_seconds'] = float(overall_summary.get('total_time_taken_seconds', 0.0))
            overall_summary['correctly_answered_questions_count'] = int(overall_summary.get('correctly_answered_questions_count', 0))
            overall_summary['incorrectly_answered_questions_count'] = int(overall_summary.get('incorrectly_answered_questions_count', 0))
            overall_summary['unattempted_questions_count'] = int(overall_summary.get('unattempted_questions_count', 0))
            overall_summary['test_total_questions'] = int(overall_summary.get('test_total_questions', 0))


            total_marks_for_test = self._get_total_marks_for_test(test_id)
            overall_summary['total_marks'] = total_marks_for_test
            overall_summary['percentage'] = self._calculate_percentage(
                overall_summary['net_score'],
                overall_summary['total_marks']
            )

            ranker_calc_query = """
                SELECT email, net_score, total_time_taken_seconds
                FROM test_result
                WHERE test_id = %s
                ORDER BY net_score DESC, total_time_taken_seconds ASC
            """
            all_results_for_ranker = user_op.fetch_all(ranker_calc_query, (test_id,))
            
            user_ranker_value = 'N/A' 
            total_participants = len(all_results_for_ranker)
            for i, result_row in enumerate(all_results_for_ranker):
                if result_row['email'] == email:
                    user_ranker_value = i + 1 
                    break
            
            overall_summary['ranker'] = user_ranker_value
            overall_summary['total_participants'] = total_participants
            
            comparison_data = self.get_average_and_topper_performance(test_id)

            times_for_max = [
                overall_summary['total_time_taken_seconds'],
                comparison_data.get('average_time', 0.0),
                comparison_data.get('topper_time', 0.0)
            ]
            calculated_max_time = max(times_for_max) if times_for_max else 1.0
            if calculated_max_time == 0:
                calculated_max_time = 1.0 

            comparison_data['max_time_for_progress'] = calculated_max_time 

            overall_summary['time_width_percentage'] = self._calculate_width_percentage(
                overall_summary['total_time_taken_seconds'], calculated_max_time
            )
            comparison_data['average_time_width_percentage'] = self._calculate_width_percentage(
                comparison_data.get('average_time', 0.0), calculated_max_time
            )
            comparison_data['topper_time_width_percentage'] = self._calculate_width_percentage(
                comparison_data.get('topper_time', 0.0), calculated_max_time
            )

            overall_summary['accuracy_width_percentage'] = overall_summary['accuracy']
            comparison_data['average_accuracy_width_percentage'] = comparison_data.get('average_accuracy', 0.0)
            comparison_data['topper_accuracy_width_percentage'] = comparison_data.get('topper_accuracy', 0.0)

            attempt_details = user_op.fetch_all("""
                SELECT
                    tad.id AS attempt_id, tad.user_selected_option, tad.user_written_answer,
                    tad.is_correct, tad.marks_awarded, tad.status_of_attempt,
                    tad.time_spent_on_question_seconds,
                    tq.id, tq.test_id, tq.section_id, tq.section_name, tq.question_number, tq.question_type,
                    tq.question_text, tq.question_image, tq.option_a, tq.option_b, tq.option_c, tq.option_d,
                    tq.correct_option, tq.correct_marks, tq.negative_marks, tq.question_level, tq.answer_text
                FROM test_attempt_details tad
                JOIN test_questions tq ON tad.question_id = tq.id
                WHERE tad.test_id = %s AND tad.email = %s
                ORDER BY tq.section_id, tq.question_number
            """, (test_id, email))

            for detail in attempt_details:
                detail['is_bookmarked'] = False 
                
                
                if detail.get('question_image') and detail.get('question_text'):
                    detail['question_text'] = detail['question_text'].replace("[IMAGE: view]", "").strip()
                
                detail['question_text'] = self._process_html_content_for_images(detail.get('question_text'))
                detail['answer_text'] = self._process_html_content_for_images(detail.get('answer_text'))

            section_summary_map = {}
            for detail in attempt_details:
                sec_id = detail['section_id']
                if sec_id not in section_summary_map:
                    section_summary_map[sec_id] = {
                        'section_id': sec_id, 'section_name': detail['section_name'],
                        'attempted': 0, 'unattempted': 0, 'correct': 0, 'incorrect': 0,
                        'questions_in_section': 0 
                    }
                section_summary_map[sec_id]['questions_in_section'] += 1 
                
                if detail['status_of_attempt'] in ['correct', 'incorrect', 'answered', 'answered_review']: 
                    section_summary_map[sec_id]['attempted'] += 1
                    if detail['is_correct']: 
                        section_summary_map[sec_id]['correct'] += 1
                    else: 
                        section_summary_map[sec_id]['incorrect'] += 1

            for sec_id, summary_data_sec in section_summary_map.items():
                summary_data_sec['unattempted'] = summary_data_sec['questions_in_section'] - summary_data_sec['attempted']
            
            actual_total_questions_in_test = overall_summary.get('test_total_questions', 0)
            if actual_total_questions_in_test == 0 and attempt_details:
                unique_question_ids = set(d['id'] for d in attempt_details)
                actual_total_questions_in_test = len(unique_question_ids)

            topper_list = self.get_topper_list(test_id, limit=10) 

            return {
                "overall": overall_summary,
                "details": attempt_details,
                "section_summary": list(section_summary_map.values()),
                "comparison": comparison_data,
                "toppers": topper_list,
                "counts": { 
                    "all": actual_total_questions_in_test, 
                    "correct": overall_summary.get('correctly_answered_questions_count', 0),
                    "incorrect": overall_summary.get('incorrectly_answered_questions_count', 0),
                    "skipped": overall_summary.get('unattempted_questions_count',0)
                }
            }
        except Exception as e:
            logger.exception(f"Error fetching enhanced test summary for test_id: {test_id}, email: {email}")
            return None