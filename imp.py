
"""
1-

CREATE DATABASE user_admin_system 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;


2-

CREATE TABLE auth (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,         
    username VARCHAR(100) NOT NULL,          
    password VARCHAR(255) NOT NULL,             
    is_verified BOOLEAN DEFAULT FALSE,         
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

3-

CREATE TABLE enrollment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL,                    
    course VARCHAR(100) NOT NULL,                   
    unique_code TEXT NOT NULL,                     
    enrollment_date DATE DEFAULT CURRENT_DATE,      
    FOREIGN KEY (email) REFERENCES auth(email) ON DELETE CASCADE
);


4-

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

5-

CREATE TABLE purchase (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    price FLOAT NOT NULL,  
    original_price FLOAT NOT NULL,  
    discount_percent FLOAT NOT NULL,  
    final_price FLOAT NOT NULL,  
    payment_date DATETIME NOT NULL,
    payment_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL, 
    purchase_code VARCHAR(100) UNIQUE NOT NULL,
    course_code VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (email) REFERENCES auth(email) ON DELETE CASCADE
);

6-

CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(100) NOT NULL ,              
    title VARCHAR(255) NOT NULL,     
    url TEXT,                        
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  
);



7-

CREATE TABLE content (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(100) NOT NULL ,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    price DECIMAL(10,2) DEFAULT 0.00,
    details TEXT,
    label ENUM('Free', 'Paid') NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    url TEXT,
    image_url TEXT,
    section ENUM('NOTES', 'PRACTICE BOOK', 'PYQ') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


8-

CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,        
    name VARCHAR(255) NOT NULL,                
    description TEXT,                        
    code VARCHAR(100) UNIQUE NOT NULL         
);


9-
CREATE TABLE auth_admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('owner', 'admin') NOT NULL DEFAULT 'admin',
    created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

10-

INSERT INTO auth_admin (username, email, role, created)
VALUES
  ('Raja kumar', 'rajakumarshyam7479@gmail.com', 'owner', '2025-04-14 03:23:59'), 
  ('Apoorv Rathore', 'apoorvrathore699@gmail.com', 'admin', '2025-04-14 03:23:59');

11-
"""
