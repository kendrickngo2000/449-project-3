CREATE TABLE Student (
    s_first_name VARCHAR(255), 
    s_last_name VARCHAR(255), 
    student_username VARCHAR(255) PRIMARY KEY
);

CREATE TABLE Instructor (
    instructor_username VARCHAR(255) PRIMARY KEY,
    i_first_name VARCHAR(255),
    i_last_name VARCHAR(255)
);

CREATE TABLE Class (
    class_code CHAR(7),
    section_number CHAR(2),
    class_name VARCHAR(255),
    department VARCHAR(255),
    auto_enrollment BOOLEAN,
    max_enrollment TINYINT,
    max_waitlist TINYINT,
    c_instructor_username VARCHAR(255),
    PRIMARY KEY (class_code, section_number),
    FOREIGN KEY (c_instructor_username) REFERENCES Instructor(instructor_username)
);

CREATE TABLE Enroll (
    e_student_username VARCHAR(8),
    e_class_code CHAR(7),
    e_section_number CHAR(2),
    PRIMARY KEY (e_student_username, e_class_code, e_section_number),
    FOREIGN KEY (e_student_username) REFERENCES Student(student_username),
    FOREIGN KEY (e_class_code, e_section_number) REFERENCES Class(class_code, section_number)
);

CREATE TABLE Waitlist (
    w_student_username VARCHAR(8),
    w_class_code CHAR(7),
    w_section_number CHAR(2),
    timestamp DATETIME,
    PRIMARY KEY (w_student_username, w_class_code, w_section_number),
    FOREIGN KEY (w_student_username) REFERENCES Student(student_username),
    FOREIGN KEY (w_class_code, w_section_number) REFERENCES Class(class_code, section_number)
);

CREATE TABLE Dropped (
    d_student_username VARCHAR(8),
    d_class_code CHAR(7),
    d_section_number CHAR(2),
    PRIMARY KEY (d_student_username, d_class_code, d_section_number),
    FOREIGN KEY (d_student_username) REFERENCES Student(student_username),
    FOREIGN KEY (d_class_code, d_section_number) REFERENCES Class(class_code, section_number)
);

-- Insert six students with names starting with 'S'
INSERT INTO Student (s_first_name, s_last_name, student_username)
VALUES
    ('Sam', 'Doe', 'SamDoe123'),
    ('Samantha', 'Smith', 'SamathaSmith123'),
    ('Sandra', 'Johnson', 'SandraJohnson123'),
    ('Steve', 'Brown', 'SteveBrown123'),
    ('Sylvia', 'Wilson', 'SylviaWilson123'),
    ('Scott', 'Davis', 'ScottDavis123');

-- Insert three professors with names starting with 'I'
INSERT INTO Instructor (instructor_username, i_first_name, i_last_name)
VALUES
    ('IreneDoe100', 'Irene', 'Doe'),
    ('IsaacSmit101', 'Isaac', 'Smith'),
    ('IsabellaJohnson102', 'Isabella', 'Johnson');

-- Insert six courses
INSERT INTO Class (class_code, section_number, class_name, department, auto_enrollment, max_enrollment, max_waitlist, c_instructor_username)
VALUES
    ('CPSC449', '01', 'Database Systems', 'Computer Science', TRUE, 30, 15, 'IreneDoe100'),
    ('CPSC449', '02', 'Database Systems', 'Computer Science', TRUE, 30, 15, 'IsaacSmit101'),
    ('MATH101', '01', 'Introduction to Calculus', 'Mathematics', TRUE, 25, 15, 'IsabellaJohnson102'),
    ('MATH101', '02', 'Introduction to Calculus', 'Mathematics', TRUE, 2, 15, 'IsabellaJohnson102'),
    ('ENGL205', '01', 'American Literature', 'English', TRUE, 3, 3, 'IreneDoe100'),
    ('PHYS202', '01', 'Physics II', 'Physics', TRUE, 40, 15, 'IsaacSmit101'),
    ('PHYS202', '02', 'Physics II', 'Physics', TRUE, 3, 15, 'IsaacSmit101'),
    ('CHEM101', '01', 'Introduction to Chemistry', 'Chemistry', TRUE, 20, 15, 'IsabellaJohnson102'),
    ('CHEM101', '02', 'Introduction to Chemistry', 'Chemistry', TRUE, 1, 5, 'IsabellaJohnson102');

-- Enroll every student in two classes
INSERT INTO Enroll (e_student_username, e_class_code, e_section_number)
VALUES
    ('SamDoe123', 'CPSC449', '01'),
    ('SylviaWilson123', 'CPSC449', '01'),
    ('SamathaSmith123', 'CPSC449', '02'),

    ('SamDoe123', 'MATH101', '01'),
    ('SandraJohnson123', 'MATH101', '01'),
    ('SamathaSmith123', 'MATH101', '02'),
    ('SteveBrown123', 'MATH101', '02'),

    ('SamathaSmith123', 'ENGL205', '01'),
    ('SteveBrown123', 'ENGL205', '01'),
    ('ScottDavis123', 'ENGL205', '01'),

    ('SandraJohnson123', 'PHYS202', '01'),
    ('SylviaWilson123', 'PHYS202', '01'),
    ('SamDoe123', 'PHYS202', '02'),
    ('SamathaSmith123', 'PHYS202', '02'),
    ('SteveBrown123', 'PHYS202', '02'),

    ('SteveBrown123', 'CHEM101', '01'),
    ('ScottDavis123', 'CHEM101', '01'),
    ('SylviaWilson123', 'CHEM101', '02');


-- Add students to the waitlist of classes they are not enrolled in
-- Each student is added to the waitlist of a class they are not enrolled in
INSERT INTO Waitlist (w_student_username, w_class_code, w_section_number, timestamp)
VALUES
    ('SamDoe123', 'ENGL205', '01', '2023-09-15 10:00:00'),
    ('SteveBrown123', 'ENGL205', '01', '2023-09-15 13:00:00'),
    ('SylviaWilson123', 'ENGL205', '01', '2023-09-15 14:00:00'),
    ('ScottDavis123', 'PHYS202', '02', '2023-09-15 15:00:00'),
    ('SamathaSmith123', 'CHEM101', '02', '2023-09-15 11:00:00'),
    ('SandraJohnson123', 'CHEM101', '02', '2023-09-15 12:00:00');
    

-- Have every student drop one class they are not enrolled in
INSERT INTO Dropped (d_student_username, d_class_code, d_section_number)
VALUES
    ('SamDoe123', 'CHEM101', '01'),
    ('SamathaSmith123', 'CPSC449', '01'),
    ('SandraJohnson123', 'ENGL205', '01'),
    ('SteveBrown123', 'MATH101', '01'),
    ('SylviaWilson123', 'CHEM101', '01'),
    ('ScottDavis123', 'MATH101', '01');

