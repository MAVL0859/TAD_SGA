from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from app.interface.auth import login_required
from app.infrastructure.models import Course, Teacher, Student, Enrollment, db

course_bp = Blueprint('course', __name__)

# Crear curso (solo admin o teacher)
@course_bp.route('/', methods=['POST'])
@login_required()
def create_course():
    identity = session['user']
    if identity['role'] not in ['admin', 'teacher']:
        return jsonify(msg='No autorizado'), 403
    data = request.get_json()
    course = Course(
        course_code=data['course_code'],
        name=data['name'],
        description=data.get('description'),
        credits=data['credits'],
        teacher_id=data['teacher_id'],
        start_date=data.get('start_date'),
        end_date=data.get('end_date')
    )
    db.session.add(course)
    db.session.commit()
    return jsonify(msg='Curso creado', id=course.id), 201

# Listar cursos (admin ve todos, teacher ve propios, student ve inscritos)
@course_bp.route('/', methods=['GET'])
@login_required()
def list_courses():
    if 'user_id' not in session or 'role' not in session:
        flash('Por favor, inicie sesión para acceder a esta página.', 'warning')
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    role = session['role']

    if role == 'admin':
        courses = Course.query.all()
    elif role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        courses = Course.query.filter_by(teacher_id=teacher.id).all() if teacher else []
    elif role == 'student':
        student = Student.query.filter_by(user_id=user_id).first()
        courses = [enrollment.course for enrollment in student.enrollments] if student else []
    else:
        courses = []

    return render_template('courses.html', courses=courses)

# Obtener curso
@course_bp.route('/<int:course_id>', methods=['GET'])
@login_required()
def get_course(course_id):
    course = Course.query.get_or_404(course_id)
    return jsonify({
        'id': course.id,
        'course_code': course.course_code,
        'name': course.name,
        'description': course.description,
        'credits': course.credits,
        'teacher_id': course.teacher_id,
        'start_date': str(course.start_date),
        'end_date': str(course.end_date)
    })

# Actualizar curso (solo admin o teacher dueño)
@course_bp.route('/<int:course_id>', methods=['PUT'])
@login_required()
def update_course(course_id):
    identity = session['user']
    course = Course.query.get_or_404(course_id)
    if identity['role'] == 'admin' or (identity['role'] == 'teacher' and course.teacher_id == Teacher.query.filter_by(user_id=identity['id']).first().id):
        data = request.get_json()
        course.name = data.get('name', course.name)
        course.description = data.get('description', course.description)
        course.credits = data.get('credits', course.credits)
        db.session.commit()
        return jsonify(msg='Curso actualizado')
    return jsonify(msg='No autorizado'), 403

# Eliminar curso (solo admin)
@course_bp.route('/<int:course_id>', methods=['DELETE'])
@login_required()
def delete_course(course_id):
    identity = session['user']
    if identity['role'] != 'admin':
        return jsonify(msg='Solo el admin puede eliminar cursos'), 403
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    return jsonify(msg='Curso eliminado')
