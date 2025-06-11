"""

-- 1. Main Study Materials Table

CREATE TABLE test_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    code VARCHAR(50),
    status ENUM('Active', 'Inactive'),
    label ENUM('Free', 'Paid'),
    stream VARCHAR(255),
    test_id VARCHAR(50),
    test_key VARCHAR(100),
    test_code VARCHAR(50) UNIQUE
) ENGINE=InnoDB;


-- 2. Test Description Table (Only One Entry Per test_id)

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
    FOREIGN KEY (test_code) REFERENCES study_materials(test_code) ON DELETE CASCADE
)ENGINE=InnoDB;


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
    UNIQUE KEY unique_user_test (email, test_id),
    FOREIGN KEY (test_id) REFERENCES study_materials(test_id) ON DELETE CASCADE
) ENGINE=InnoDB;



-- 3. Test Questions Table (Multiple questions per test_id)

CREATE TABLE test_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id VARCHAR(50),
    section_id VARCHAR(50),
    section_name VARCHAR(100),
    question_number INT,
    question_type ENUM('MCQ', 'MSQ', 'NAT') NOT NULL,
    question_text TEXT,
    question_image VARCHAR(255),
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_option VARCHAR(10),
    correct_marks FLOAT,
    negative_marks FLOAT,
    question_level ENUM('Easy', 'Medium', 'Tough') DEFAULT 'Medium',
    answer_text TEXT,
    answer_link VARCHAR(255),
    answer_image VARCHAR(255),
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (test_code) REFERENCES study_materials(test_code) ON DELETE CASCADE
) ENGINE=InnoDB;


-- 4. User Test Results status Table (Per user per test_id)

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
    FOREIGN KEY (test_code) REFERENCES study_materials(test_code) ON DELETE CASCADE
) ENGINE=InnoDB;


-- 5. Track if user has already taken test

CREATE TABLE user_test_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255),
    username VARCHAR(100),
    test_id VARCHAR(50),
    is_checkbox_checked TINYINT(1) DEFAULT 0,
    ready_to_begin TINYINT(1) DEFAULT 0,
    accepted_at DATETIME DEFAULT NULL,
    start_time DATETIME,
    end_time DATETIME,
    status VARCHAR(50),
    device_info TEXT,
    attempt_number INT,
    created_at DATETIME,
    updated_at DATETIME,
    termination_reason TEXT,
    FOREIGN KEY (test_id) REFERENCES study_materials(test_id) ON DELETE CASCADE
) ENGINE=InnoDB;

--6 Track user test result attempt Table 

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
    FOREIGN KEY (test_id) REFERENCES study_materials(test_id) ON DELETE CASCADE
) ENGINE=InnoDB;

"""