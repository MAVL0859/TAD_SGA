-- Tabla de usuarios (base para autenticación)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(10) NOT NULL CHECK (role IN ('admin', 'student', 'teacher')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Función y trigger para actualizar automáticamente updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at();

-- Tabla de perfiles (información adicional)
CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    avatar_url VARCHAR(255) DEFAULT 'default_avatar.png',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabla de estudiantes (datos específicos)
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    student_code VARCHAR(20) NOT NULL UNIQUE,
    enrollment_date DATE NOT NULL,
    major VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabla de profesores (datos específicos)
CREATE TABLE teachers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    employee_id VARCHAR(20) NOT NULL UNIQUE,
    hire_date DATE NOT NULL,
    department VARCHAR(100) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabla de cursos
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    credits SMALLINT NOT NULL,
    teacher_id INTEGER NOT NULL,
    start_date DATE,
    end_date DATE,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);

-- Tabla de inscripciones (relación estudiantes-cursos)
CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    grade DECIMAL(5,2) CHECK (grade BETWEEN 0 AND 100),
    status VARCHAR(10) DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'completed', 'dropped')),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    UNIQUE (student_id, course_id)
);

-- Tabla de tareas/entregables
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    max_score DECIMAL(5,2) NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- Tabla de entregas de estudiantes
CREATE TABLE submissions (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    student_id INTEGER NOT NULL,
    submission_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    file_url VARCHAR(255) NOT NULL,
    score DECIMAL(5,2),
    feedback TEXT,
    FOREIGN KEY (assignment_id) REFERENCES assignments(id),
    FOREIGN KEY (student_id) REFERENCES students(id)
);

-- Tabla de logs de acceso (opcional para auditoría)
CREATE TABLE access_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    FOREIGN KEY (user_id) REFERENCES users(id)
);


-- MYSQL Script to create the database and tables for an academic management system
-- Asegúrate de ejecutar este script en un entorno MySQL compatible.
-- CREATE DATABASE academia_db;
-- USE academia_db;

-- -- Tabla de usuarios (base para autenticación)
-- CREATE TABLE users (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     username VARCHAR(50) NOT NULL UNIQUE,
--     email VARCHAR(100) NOT NULL UNIQUE,
--     password VARCHAR(255) NOT NULL,
--     role ENUM('admin', 'student', 'teacher') NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
-- );

-- -- Tabla de perfiles (información adicional)
-- CREATE TABLE profiles (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     user_id INT NOT NULL UNIQUE,
--     first_name VARCHAR(50) NOT NULL,
--     last_name VARCHAR(50) NOT NULL,
--     avatar_url VARCHAR(255) DEFAULT 'default_avatar.png',
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
-- );

-- -- Tabla de estudiantes (datos específicos)
-- CREATE TABLE students (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     user_id INT NOT NULL UNIQUE,
--     student_code VARCHAR(20) NOT NULL UNIQUE,
--     enrollment_date DATE NOT NULL,
--     major VARCHAR(100),
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
-- );

-- -- Tabla de profesores (datos específicos)
-- CREATE TABLE teachers (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     user_id INT NOT NULL UNIQUE,
--     employee_id VARCHAR(20) NOT NULL UNIQUE,
--     hire_date DATE NOT NULL,
--     department VARCHAR(100) NOT NULL,
--     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
-- );

-- -- Tabla de cursos
-- CREATE TABLE courses (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     course_code VARCHAR(20) NOT NULL UNIQUE,
--     name VARCHAR(100) NOT NULL,
--     description TEXT,
--     credits TINYINT NOT NULL,
--     teacher_id INT NOT NULL,
--     start_date DATE,
--     end_date DATE,
--     FOREIGN KEY (teacher_id) REFERENCES teachers(id)
-- );

-- -- Tabla de inscripciones (relación estudiantes-cursos)
-- CREATE TABLE enrollments (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     student_id INT NOT NULL,
--     course_id INT NOT NULL,
--     enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     grade DECIMAL(5,2) CHECK (grade BETWEEN 0 AND 100),
--     status ENUM('enrolled', 'completed', 'dropped') DEFAULT 'enrolled',
--     FOREIGN KEY (student_id) REFERENCES students(id),
--     FOREIGN KEY (course_id) REFERENCES courses(id),
--     UNIQUE KEY (student_id, course_id)
-- );

-- -- Tabla de tareas/entregables
-- CREATE TABLE assignments (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     course_id INT NOT NULL,
--     title VARCHAR(100) NOT NULL,
--     description TEXT,
--     due_date DATETIME NOT NULL,
--     max_score DECIMAL(5,2) NOT NULL,
--     FOREIGN KEY (course_id) REFERENCES courses(id)
-- );

-- -- Tabla de entregas de estudiantes
-- CREATE TABLE submissions (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     assignment_id INT NOT NULL,
--     student_id INT NOT NULL,
--     submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     file_url VARCHAR(255) NOT NULL,
--     score DECIMAL(5,2),
--     feedback TEXT,
--     FOREIGN KEY (assignment_id) REFERENCES assignments(id),
--     FOREIGN KEY (student_id) REFERENCES students(id)
-- );

-- -- Tabla de logs de acceso (opcional para auditoría)
-- CREATE TABLE access_logs (
--     id INT AUTO_INCREMENT PRIMARY KEY,
--     user_id INT NOT NULL,
--     action VARCHAR(50) NOT NULL,
--     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     ip_address VARCHAR(45),
--     FOREIGN KEY (user_id) REFERENCES users(id)
-- -- );