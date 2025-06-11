from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.infrastructure.models import Enrollment, Student, Course, Teacher, db

enroll_bp = Blueprint('enroll', __name__)

# Inscribir estudiante a curso (solo admin)
@enroll_bp.route('/', methods=['POST'])
@jwt_required()
def enroll_student():
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        return jsonify(msg='Solo el admin puede inscribir estudiantes'), 403
    data = request.get_json()
    enrollment = Enrollment(
        student_id=data['student_id'],
        course_id=data['course_id']
    )
    db.session.add(enrollment)
    db.session.commit()
    return jsonify(msg='Estudiante inscrito'), 201

# Listar inscripciones de un estudiante (solo el propio estudiante o admin)
@enroll_bp.route('/student/<int:student_id>', methods=['GET'])
@jwt_required()
def list_enrollments_student(student_id):
    identity = get_jwt_identity()
    if identity['role'] != 'admin':
        student = Student.query.filter_by(user_id=identity['id']).first()
        if not student or student.id != student_id:
            return jsonify(msg='No autorizado'), 403
    enrollments = Enrollment.query.filter_by(student_id=student_id).all()
    return jsonify([
        {'course_id': e.course_id, 'status': e.status, 'grade': float(e.grade) if e.grade else None} for e in enrollments
    ])

# Listar inscripciones de un curso (solo teacher dueño o admin)
@enroll_bp.route('/course/<int:course_id>', methods=['GET'])
@jwt_required()
def list_enrollments_course(course_id):
    identity = get_jwt_identity()
    course = Course.query.get_or_404(course_id)
    if identity['role'] != 'admin':
        teacher = Teacher.query.filter_by(user_id=identity['id']).first()
        if not teacher or course.teacher_id != teacher.id:
            return jsonify(msg='No autorizado'), 403
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    return jsonify([
        {'student_id': e.student_id, 'status': e.status, 'grade': float(e.grade) if e.grade else None} for e in enrollments
    ])
