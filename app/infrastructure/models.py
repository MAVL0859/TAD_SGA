from app.main import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True))
    updated_at = db.Column(db.DateTime(timezone=True))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    student_code = db.Column(db.String(20), unique=True, nullable=False)
    enrollment_date = db.Column(db.Date, nullable=False)
    major = db.Column(db.String(100))

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    hire_date = db.Column(db.Date, nullable=False)
    department = db.Column(db.String(100), nullable=False)

class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    avatar_url = db.Column(db.String(255), default='default_avatar.png')
    phone = db.Column(db.String(20))  # Campo para teléfono

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    credits = db.Column(db.SmallInteger, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    semester = db.Column(db.String(20))  # e.g., "2024-1", "2024-2"
    is_active = db.Column(db.Boolean, default=True)
    
    # Para compatibilidad con las rutas
    @property
    def code(self):
        return self.course_code

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime(timezone=True))
    grade = db.Column(db.Numeric(5,2))
    status = db.Column(db.String(10), default='enrolled')

class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime(timezone=True), nullable=False)
    max_score = db.Column(db.Numeric(5,2), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    created_date = db.Column(db.DateTime(timezone=True), nullable=False)

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    submission_date = db.Column(db.DateTime(timezone=True))
    file_url = db.Column(db.String(255), nullable=False)
    score = db.Column(db.Numeric(5,2))
    feedback = db.Column(db.Text)

class Grade(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    assignment_name = db.Column(db.String(100), nullable=False)  # Nombre de la tarea o evaluación
    score = db.Column(db.Numeric(5,2), nullable=False)  # Puntuación obtenida
    max_score = db.Column(db.Numeric(5,2), nullable=False, default=100)  # Puntuación máxima
    date = db.Column(db.DateTime(timezone=True), nullable=False)  # Fecha de la calificación
    comments = db.Column(db.Text)  # Comentarios del profesor
    
    # Relationships
    course = db.relationship('Course', backref=db.backref('grades', lazy=True))
    student = db.relationship('Student', backref=db.backref('grades', lazy=True))

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)  # Fecha de la clase
    status = db.Column(db.String(10), nullable=False)  # 'present', 'absent', 'late', 'excused'
    notes = db.Column(db.Text)  # Notas adicionales
    
    # Relationships
    course = db.relationship('Course', backref=db.backref('attendance_records', lazy=True))
    student = db.relationship('Student', backref=db.backref('attendance_records', lazy=True))
    
    # Unique constraint to prevent duplicate records for same student, course, and date
    __table_args__ = (db.UniqueConstraint('course_id', 'student_id', 'date', name='unique_attendance_record'),)

class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # LOGIN, LOGOUT, VIEW_PAGE, etc.
    endpoint = db.Column(db.String(100))  # URL endpoint accessed
    ip_address = db.Column(db.String(45))  # IPv4/IPv6
    user_agent = db.Column(db.String(255))  # Browser info
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.String(20), default='SUCCESS')  # SUCCESS, FAILED, BLOCKED
    details = db.Column(db.Text)  # Additional details
    
    # Relationship to User
    user = db.relationship('User', backref=db.backref('access_logs', lazy=True))
    
    @property
    def username(self):
        """Obtener el username desde la relación con User"""
        return self.user.username if self.user else 'Desconocido'
