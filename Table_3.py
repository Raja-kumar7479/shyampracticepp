"""

1-
CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    code VARCHAR(100) NOT NULL UNIQUE,

    INDEX idx_name (name),
    INDEX idx_code (code)
) ENGINE=InnoDB;


CREATE TABLE practice_questions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(100) NOT NULL,
    section ENUM('Topic-wise', 'Subject-wise', 'Year-wise') NOT NULL,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_code (code)
) ENGINE=InnoDB;

2-

CREATE TABLE auth_admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('owner', 'admin') NOT NULL DEFAULT 'admin',
    created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),           
    INDEX idx_username (username),     
    INDEX idx_role (role),             
    INDEX idx_created (created)        
) ENGINE=InnoDB;


3-

INSERT INTO auth_admin (username, email, role, created)
VALUES
  ('Raja kumar ', 'rajakumarshyam@shyampp.com', 'owner', '2025-08-06 03:30:00'), 
  ('Apoorv Rathore', 'apoorvrathore699@shyampp.com', 'admin', '2025-08-06 03:30:00');

"""