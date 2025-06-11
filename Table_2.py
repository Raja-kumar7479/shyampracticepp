"""

1-

CREATE TABLE auth (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255),
    oauth_id VARCHAR(255),
    auth_type ENUM('manual', 'google', 'both'),
    is_verified BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

2-

CREATE TABLE enrollment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL,                    
    course VARCHAR(100) NOT NULL,                   
    unique_code TEXT NOT NULL,                     
    enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email) REFERENCES auth(email) ON DELETE CASCADE
);


3-

CREATE TABLE coupon (
    coupon_id INT AUTO_INCREMENT PRIMARY KEY,
    coupon_code VARCHAR(50) NOT NULL,
    discount DECIMAL(5,2) NOT NULL,
    min_purchase DECIMAL(10,2) NOT NULL,
    uses_count INT DEFAULT 0,
    status BOOLEAN DEFAULT TRUE,
    expiry_date DATE,
    valid_until DATE,
    email VARCHAR(255),
    FOREIGN KEY (email) REFERENCES auth(email) ON DELETE CASCADE
);

4-

CREATE TABLE purchase (
  id INT NOT NULL AUTO_INCREMENT,
  email VARCHAR(255) NOT NULL,
  username VARCHAR(255) DEFAULT NULL,
  phone VARCHAR(20) DEFAULT NULL,
  course_code VARCHAR(100) NOT NULL,
  section_id VARCHAR(255) DEFAULT NULL,        
  section VARCHAR(255) DEFAULT NULL,
  title VARCHAR(255) NOT NULL,
  subtitle VARCHAR(255) DEFAULT NULL,
  price DECIMAL(10, 2) NOT NULL,
  original_price DECIMAL(10, 2) NOT NULL,
  discount_percent DECIMAL(5, 2) DEFAULT 0.00,
  final_price DECIMAL(10, 2) NOT NULL,
  payment_id VARCHAR(255) NOT NULL,
  payment_mode VARCHAR(50) DEFAULT NULL,
  payment_date DATETIME NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'Pending',
  purchase_code VARCHAR(50) NOT NULL,

  PRIMARY KEY (id),
  INDEX idx_email (email),
  INDEX idx_payment_id (payment_id),
  INDEX idx_course_code (course_code),
  INDEX idx_purchase_code (purchase_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


5-


CREATE TABLE content (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    price DECIMAL(10,2) DEFAULT 0.00,
    details TEXT,
    label ENUM('Free', 'Paid') NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    image_url TEXT,
    section NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


6-


CREATE TABLE questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paper_code VARCHAR(20),
    subject VARCHAR(100),
    topic VARCHAR(100),
    question_id INT NOT NULL,
    question_text TEXT,
    image_path TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_option VARCHAR(5),
    answer_text TEXT,
    question_type ENUM('MCQ', 'MSQ', 'NAT') NOT NULL,
    year INT,
    paper_set VARCHAR(100),
    explanation_link TEXT,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

"""