"""

1-

CREATE TABLE courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    code VARCHAR(100) NOT NULL UNIQUE
);


2-

CREATE TABLE auth_admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('owner', 'admin') NOT NULL DEFAULT 'admin',
    created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);


3-

INSERT INTO auth_admin (username, email, role, created)
VALUES
  ('Raja kumar', 'rajakumarshyam@gmail.com', 'owner', '2025-04-14 03:23:59'), 
  ('Apoorv Rathore', 'apoorvrathore699@gmail.com', 'admin', '2025-04-14 03:23:59');

  

"""