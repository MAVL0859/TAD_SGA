from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from app.interface.auth import login_required
from app.infrastructure.models import Assignment, Course, Teacher, Student, Enrollment, db

assignment_bp = Blueprint('assignment', __name__)

# Crear tarea (solo teacher dueño)
@assignment_bp.route('/', methods=['POST'])
@login_required('teacher')
def create_assignment():
    identity = session['user']
    teacher = Teacher.query.filter_by(user_id=identity['id']).first()
    data = request.get_json()
    course = Course.query.get(data['course_id'])
    if not teacher or not course or course.teacher_id != teacher.id:
        return jsonify(msg='No autorizado'), 403
    assignment = Assignment(
        course_id=data['course_id'],
        title=data['title'],
        description=data.get('description'),
        due_date=data['due_date'],
        max_score=data['max_score']
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify(msg='Tarea creada', id=assignment.id), 201

# Listar tareas de un curso (student inscrito o teacher dueño)
@assignment_bp.route('/course/<int:course_id>', methods=['GET'])
@login_required('teacher')
def list_assignments(course_id):
    identity = session['user']
    course = Course.query.get_or_404(course_id)
    if identity['role'] == 'teacher':
        teacher = Teacher.query.filter_by(user_id=identity['id']).first()
        if not teacher or course.teacher_id != teacher.id:
            return jsonify(msg='No autorizado'), 403
    elif identity['role'] == 'student':
        student = Student.query.filter_by(user_id=identity['id']).first()
        enrollment = Enrollment.query.filter_by(student_id=student.id, course_id=course_id).first() if student else None
        if not enrollment:
            return jsonify(msg='No autorizado'), 403
    assignments = Assignment.query.filter_by(course_id=course_id).all()
    return jsonify([
        {'id': a.id, 'title': a.title, 'due_date': str(a.due_date), 'max_score': float(a.max_score)} for a in assignments
    ])

# Actualizar tarea (solo teacher dueño)
@assignment_bp.route('/<int:assignment_id>', methods=['PUT'])
@login_required('teacher')
def update_assignment(assignment_id):
    identity = session['user']
    assignment = Assignment.query.get_or_404(assignment_id)
    course = Course.query.get(assignment.course_id)
    teacher = Teacher.query.filter_by(user_id=identity['id']).first()
    if identity['role'] != 'teacher' or not teacher or course.teacher_id != teacher.id:
        return jsonify(msg='No autorizado'), 403
    data = request.get_json()
    assignment.title = data.get('title', assignment.title)
    assignment.description = data.get('description', assignment.description)
    assignment.due_date = data.get('due_date', assignment.due_date)
    assignment.max_score = data.get('max_score', assignment.max_score)
    db.session.commit()
    return jsonify(msg='Tarea actualizada')

# Eliminar tarea (solo teacher dueño)
@assignment_bp.route('/<int:assignment_id>', methods=['DELETE'])
@login_required('teacher')
def delete_assignment(assignment_id):
    identity = session['user']
    assignment = Assignment.query.get_or_404(assignment_id)
    course = Course.query.get(assignment.course_id)
    teacher = Teacher.query.filter_by(user_id=identity['id']).first()
    if identity['role'] != 'teacher' or not teacher or course.teacher_id != teacher.id:
        return jsonify(msg='No autorizado'), 403
    db.session.delete(assignment)
    db.session.commit()
    return jsonify(msg='Tarea eliminada')
