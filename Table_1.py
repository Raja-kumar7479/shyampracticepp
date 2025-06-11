"""

-- 1. Main test details Table

CREATE TABLE test_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    code VARCHAR(50),
    status ENUM('Active', 'Inactive'),
    label ENUM('Free', 'Paid'),
    stream VARCHAR(255),
    test_id VARCHAR(50),
    test_key VARCHAR(100),
    test_code VARCHAR(50) UNIQUE,

    INDEX idx_name (name),
    INDEX idx_code (code),
    INDEX idx_status (status),
    INDEX idx_label (label),
    INDEX idx_stream (stream),
    INDEX idx_test_id (test_id),
    INDEX idx_test_key (test_key)
) ENGINE=InnoDB;

CREATE TABLE test_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    feedback_software VARCHAR(50),
    feedback_content VARCHAR(255),
    feedback_speed VARCHAR(50),
    suggestions TEXT,
    submission_time DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (test_id) REFERENCES test_details(test_id) ON DELETE CASCADE,

    INDEX idx_test_id (test_id),
    INDEX idx_email (email),
    INDEX idx_feedback_software (feedback_software),
    INDEX idx_submission_time (submission_time)
) ENGINE=InnoDB;



CREATE TABLE test_description (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id VARCHAR(100) NOT NULL UNIQUE,  
    test_number VARCHAR(100) NOT NULL,
    subject_title VARCHAR(255) NOT NULL,
    subject_subtitle VARCHAR(255) NOT NULL,
    year YEAR,
    total_questions INT NOT NULL,
    total_marks FLOAT NOT NULL,
    total_duration_minutes INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (test_id) REFERENCES test_details(test_id) ON DELETE CASCADE,

    INDEX idx_test_number (test_number),
    INDEX idx_subject_title (subject_title),
    INDEX idx_subject_subtitle (subject_subtitle),
    INDEX idx_year (year),
    INDEX idx_total_questions (total_questions),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB;

CREATE TABLE user_test_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    test_id VARCHAR(100) NOT NULL,
    username VARCHAR(100),
    start_time DATETIME,
    end_time DATETIME,
    status VARCHAR(50),
    device_info TEXT,
    attempt_number INT,
    is_checkbox_checked TINYINT(1) DEFAULT 0,
    ready_to_begin TINYINT(1) DEFAULT 0,
    accepted_at DATETIME DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (test_id) REFERENCES test_details(test_id) ON DELETE CASCADE,

    INDEX idx_email (email),
    INDEX idx_test_id (test_id),
    INDEX idx_username (username),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time),
    INDEX idx_end_time (end_time),
    INDEX idx_attempt_number (attempt_number),
    INDEX idx_is_checkbox_checked (is_checkbox_checked),
    INDEX idx_ready_to_begin (ready_to_begin),
    INDEX idx_accepted_at (accepted_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB;


CREATE TABLE test_description (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id VARCHAR(100) NOT NULL UNIQUE,  
    test_number VARCHAR(100) NOT NULL,
    subject_title VARCHAR(255) NOT NULL,
    subject_subtitle VARCHAR(255) NOT NULL,
    year YEAR,
    total_questions INT NOT NULL,
    total_marks FLOAT NOT NULL,
    total_duration_minutes INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (test_id) REFERENCES test_details(test_id) ON DELETE CASCADE,

    INDEX idx_test_number (test_number),
    INDEX idx_subject_title (subject_title),
    INDEX idx_subject_subtitle (subject_subtitle),
    INDEX idx_year (year),
    INDEX idx_total_questions (total_questions),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB;


CREATE TABLE test_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id VARCHAR(50),
    section_id VARCHAR(50),
    section_name VARCHAR(100),
    question_number INT,
    question_type ENUM('MCQ', 'MSQ', 'NAT') NOT NULL,
    question_text TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    question_image VARCHAR(255),
    option_a TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    option_b TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    option_c TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    option_d TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    correct_option VARCHAR(10),
    correct_marks FLOAT,
    negative_marks FLOAT,
    question_level ENUM('Easy', 'Medium', 'Tough') DEFAULT 'Medium',
    answer_text TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
    answer_link VARCHAR(255),
    answer_image VARCHAR(255),
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (test_code) REFERENCES test_details(test_code) ON DELETE CASCADE,

    INDEX idx_test_id (test_id),
    INDEX idx_section_id (section_id),
    INDEX idx_section_name (section_name),
    INDEX idx_question_number (question_number),
    INDEX idx_question_type (question_type),
    INDEX idx_question_level (question_level),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB;

CREATE TABLE test_result (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255),
    username VARCHAR(100),
    test_id VARCHAR(50),
    test_code VARCHAR(50),  
    attempted_questions_count INT,
    unattempted_questions_count INT,
    correctly_answered_questions_count INT,
    incorrectly_answered_questions_count INT,
    marks_for_correct_answers FLOAT,
    penalty_for_incorrect_answers FLOAT,
    net_score FLOAT,
    accuracy FLOAT,
    percentage FLOAT,
    submission_ranker INT,
    total_time_taken_seconds INT,
    submission_timestamp DATETIME,
    FOREIGN KEY (test_code) REFERENCES test_details(test_code) ON DELETE CASCADE,

    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_test_id (test_id),
    INDEX idx_test_code (test_code),
    INDEX idx_net_score (net_score),
    INDEX idx_accuracy (accuracy),
    INDEX idx_percentage (percentage),
    INDEX idx_submission_ranker (submission_ranker),
    INDEX idx_submission_timestamp (submission_timestamp)
) ENGINE=InnoDB;

CREATE TABLE test_attempt_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id VARCHAR(50),
    email VARCHAR(255),
    question_id INT,
    user_selected_option VARCHAR(10),
    user_written_answer TEXT,
    is_correct BOOLEAN,
    marks_awarded FLOAT,
    status_of_attempt VARCHAR(50),
    time_spent_on_question_seconds INT,
    FOREIGN KEY (test_id) REFERENCES test_details(test_id) ON DELETE CASCADE,
    
    INDEX idx_test_id (test_id),
    INDEX idx_email (email),
    INDEX idx_question_id (question_id),
    INDEX idx_is_correct (is_correct),
    INDEX idx_status_of_attempt (status_of_attempt),
    INDEX idx_marks_awarded (marks_awarded),
    INDEX idx_time_spent (time_spent_on_question_seconds)
) ENGINE=InnoDB;

"""