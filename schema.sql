DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'officer') NOT NULL DEFAULT 'student',
    cgpa DECIMAL(3,2) DEFAULT NULL,
    roll_number VARCHAR(50) DEFAULT NULL UNIQUE,
    department VARCHAR(100) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    python TINYINT NOT NULL DEFAULT 1,
    `sql` TINYINT NOT NULL DEFAULT 1,
    java TINYINT NOT NULL DEFAULT 1,
    dsa TINYINT NOT NULL DEFAULT 1,
    communication TINYINT NOT NULL DEFAULT 1,
    problem_solving TINYINT NOT NULL DEFAULT 1,
    web_dev TINYINT NOT NULL DEFAULT 1,
    ml TINYINT NOT NULL DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_skills_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_python CHECK (python BETWEEN 1 AND 10),
    CONSTRAINT chk_sql_skill CHECK (`sql` BETWEEN 1 AND 10),
    CONSTRAINT chk_java CHECK (java BETWEEN 1 AND 10),
    CONSTRAINT chk_dsa CHECK (dsa BETWEEN 1 AND 10),
    CONSTRAINT chk_communication CHECK (communication BETWEEN 1 AND 10),
    CONSTRAINT chk_problem_solving CHECK (problem_solving BETWEEN 1 AND 10),
    CONSTRAINT chk_web_dev CHECK (web_dev BETWEEN 1 AND 10),
    CONSTRAINT chk_ml CHECK (ml BETWEEN 1 AND 10)
);

CREATE TABLE companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    role VARCHAR(120) NOT NULL,
    ctc_lpa DECIMAL(5,2) NOT NULL,
    min_cgpa DECIMAL(3,2) NOT NULL,
    skills_required VARCHAR(255) NOT NULL,
    drive_date DATE NOT NULL,
    prep_kit_url VARCHAR(255) NOT NULL
);

INSERT INTO users (name, email, password_hash, role, cgpa, roll_number, department) VALUES
('Placement Officer', 'officer@campus.edu', 'pbkdf2:sha256:1000000$iimWEQP95PmXt2n2$ce646592abafb6e74dbe64189e97af042bb0f61f1d69713d34b184d9a5496c14', 'officer', NULL, NULL, 'Placement Cell'),
('Aarav Sharma', 'student1@campus.edu', 'pbkdf2:sha256:1000000$BGmmDuEgEGjPLh9p$ee26c50dce042de9df7e437ba20aff8e7e457a6cad9ccbad5b4a620a4640712e', 'student', 8.20, 'CSE2024001', 'Computer Science'),
('Diya Nair', 'student2@campus.edu', 'pbkdf2:sha256:1000000$p719kLegrkRD3hxM$bc6c6896bb5a270709cdd3695bc8c93c6f6242f962b414fbb05433e3b74911c3', 'student', 7.40, 'ECE2024007', 'Electronics');

INSERT INTO skills (user_id, python, `sql`, java, dsa, communication, problem_solving, web_dev, ml) VALUES
(2, 7, 6, 5, 7, 8, 7, 6, 5),
(3, 6, 7, 6, 6, 8, 7, 5, 4);

INSERT INTO companies (name, role, ctc_lpa, min_cgpa, skills_required, drive_date, prep_kit_url) VALUES
('TCS', 'Graduate Trainee', 3.60, 6.00, 'Aptitude, Communication, Basic Programming', '2026-05-15', 'https://www.tcs.com/careers'),
('Infosys', 'Systems Engineer', 4.20, 6.50, 'Python, SQL, Problem Solving', '2026-05-22', 'https://www.infosys.com/careers'),
('Wipro', 'Project Engineer', 4.00, 6.00, 'Java, DSA, Communication', '2026-06-02', 'https://careers.wipro.com'),
('Zoho', 'Software Developer', 6.50, 7.00, 'Java, Web Dev, DSA', '2026-06-12', 'https://www.zoho.com/careers'),
('Accenture', 'Associate Software Engineer', 4.50, 6.50, 'Problem Solving, SQL, Communication', '2026-06-18', 'https://www.accenture.com/in-en/careers'),
('Capgemini', 'Analyst', 4.25, 6.00, 'Python, SQL, Aptitude', '2026-06-25', 'https://www.capgemini.com/careers'),
('Cognizant', 'Programmer Analyst', 4.40, 6.25, 'Java, Communication, Web Dev', '2026-07-03', 'https://careers.cognizant.com'),
('HCLTech', 'Graduate Engineer Trainee', 4.10, 6.00, 'Problem Solving, Python, SQL', '2026-07-10', 'https://www.hcltech.com/careers'),
('Deloitte', 'Analyst', 7.20, 7.00, 'Communication, SQL, Web Dev', '2026-07-18', 'https://www2.deloitte.com/global/en/careers'),
('Amazon', 'SDE Intern to FTE', 18.00, 7.50, 'DSA, Problem Solving, Machine Learning', '2026-08-01', 'https://leetcode.com/problemset/');
