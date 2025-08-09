'''
CREATE TABLE course_content (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(100),
    stream VARCHAR(255),
    section ENUM('Mock Test','Handwritten Notes','Video Lecture','Community Join') NOT NULL,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    label ENUM('Free', 'Paid') NOT NULL,
    price DECIMAL(10,2) DEFAULT 0.00,
    details TEXT,
    status VARCHAR(20) DEFAULT 'active',
    image_url TEXT,
    section_id VARCHAR(100) NOT NULL UNIQUE,
    preview_url TEXT NULL DEFAULT NULL,
    validity_expires_at DATETIME NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_label (label),
    INDEX idx_status (status),
    INDEX idx_section (section),
    INDEX idx_created_at (created_at),
    INDEX idx_validity_expires_at (validity_expires_at)
) ENGINE=InnoDB;


CREATE TABLE test_description (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id VARCHAR(100) NOT NULL, 
    test_key VARCHAR(100) NOT NULL UNIQUE,
    subject_title VARCHAR(255) NOT NULL,
    subject_subtitle VARCHAR(255) NOT NULL,
    total_questions INT NOT NULL,
    total_marks FLOAT NOT NULL,
    total_duration_minutes INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_test_content
        FOREIGN KEY (test_id) REFERENCES course_content(section_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (code) REFERENCES  enrollment(code) ON DELETE CASCADE
    INDEX idx_test_id (test_id)
) ENGINE=InnoDB;

CREATE TABLE test_questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    test_id VARCHAR(100),
    test_key VARCHAR(100) NOT NULL,
    test_description_id INT,
    section_id VARCHAR(10),
    section_name VARCHAR(100),
    question_number INT,
    question_type VARCHAR(10),
    question_text TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_option VARCHAR(10),
    correct_marks FLOAT,
    negative_marks FLOAT,
    question_level VARCHAR(50),
    answer_text TEXT,
    answer_link TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_test_question_desc
        FOREIGN KEY (test_key)
        REFERENCES test_description(test_key)
        ON DELETE CASCADE,
    INDEX idx_test_key (test_key)
) ENGINE=InnoDB;

CREATE TABLE user_test_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    test_id VARCHAR(100) NOT NULL,
    test_key VARCHAR(100) NOT NULL,
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
    CONSTRAINT fk_user_log_desc
        FOREIGN KEY (test_key)
        REFERENCES test_description(test_key)
        ON DELETE CASCADE,
    INDEX idx_email (email),
    INDEX idx_test_key (test_key)
) ENGINE=InnoDB;

CREATE TABLE test_result (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255),
    username VARCHAR(100),
    test_id VARCHAR(100),
    test_key VARCHAR(100) NOT NULL,
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
    CONSTRAINT fk_test_result_desc
        FOREIGN KEY (test_key)
        REFERENCES test_description(test_key)
        ON DELETE CASCADE,
    INDEX idx_email (email),
    INDEX idx_test_key (test_key)
) ENGINE=InnoDB;

CREATE TABLE test_attempt_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255),
    test_id VARCHAR(100),
    test_key VARCHAR(100) NOT NULL,
    question_id INT,
    user_selected_option VARCHAR(10),
    user_written_answer TEXT,
    is_correct BOOLEAN,
    marks_awarded FLOAT,
    status_of_attempt VARCHAR(50),
    time_spent_on_question_seconds INT,
    CONSTRAINT fk_attempt_desc
        FOREIGN KEY (test_key)
        REFERENCES test_description(test_key)
        ON DELETE CASCADE,
    CONSTRAINT fk_attempt_question
        FOREIGN KEY (question_id)
        REFERENCES test_questions(id)
        ON DELETE CASCADE,
    INDEX idx_email (email),
    INDEX idx_test_key (test_key)
) ENGINE=InnoDB;

CREATE TABLE test_feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    test_id VARCHAR(100) NOT NULL,
    test_key VARCHAR(100) NOT NULL,
    feedback_software VARCHAR(50),
    feedback_content VARCHAR(255),
    feedback_speed VARCHAR(50),
    suggestions TEXT,
    submission_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_feedback_desc
        FOREIGN KEY (test_key)
        REFERENCES test_description(test_key)
        ON DELETE CASCADE,
    INDEX idx_email (email),
    INDEX idx_test_key (test_key)
) ENGINE=InnoDB;

'''