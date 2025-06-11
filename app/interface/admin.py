from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from app.interface.auth import login_required
from app.infrastructure.models import User, Student, Teacher, Profile, Course, Enrollment
from app.main import db
from werkzeug.security import generate_password_hash
from datetime import date, datetime, timedelta

admin_bp = Blueprint('admin', __name__)

# Solo admin puede crear usuarios
@admin_bp.route('/register', methods=['POST'])
@login_required('admin')
def register():
    data = request.get_json()
    # Validar y crear usuario según el rol
    # ... lógica para crear usuario, perfil, estudiante o profesor ...
    return jsonify(msg='Usuario registrado'), 201

@admin_bp.route('/users', methods=['GET'])
@login_required('admin')
def list_users():
    role_filter = request.args.get('role')
    
    # Query base con joins para obtener información adicional
    query = db.session.query(User).outerjoin(Profile).outerjoin(Student).outerjoin(Teacher)
    
    # Filtrar por rol si se especifica
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    users = query.all()
    
    users_data = []
    for user in users:
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else None
        }
        
        # Agregar información del perfil si existe
        profile = db.session.query(Profile).filter_by(user_id=user.id).first()
        if profile:
            user_data['profile_info'] = {
                'first_name': profile.first_name,
                'last_name': profile.last_name,
                'avatar_url': profile.avatar_url
            }
        
        # Agregar información específica según el rol
        if user.role == 'teacher':
            teacher = db.session.query(Teacher).filter_by(user_id=user.id).first()
            if teacher:
                user_data['teacher_info'] = {
                    'employee_id': teacher.employee_id,
                    'department': teacher.department,
                    'hire_date': teacher.hire_date.strftime('%Y-%m-%d') if teacher.hire_date else None
                }
        elif user.role == 'student':
            student = db.session.query(Student).filter_by(user_id=user.id).first()
            if student:
                user_data['student_info'] = {
                    'student_code': student.student_code,
                    'major': student.major,
                    'enrollment_date': student.enrollment_date.strftime('%Y-%m-%d') if student.enrollment_date else None
                }
        
        users_data.append(user_data)
    
    return jsonify(users_data)

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required('admin')
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    })

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required('admin')
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.role = data.get('role', user.role)
    # Si se envía una nueva contraseña, la hasheamos
    if data.get('password'):
        user.password = generate_password_hash(data['password'])
    db.session.commit()
    return jsonify(msg='Usuario actualizado')

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(msg='Usuario eliminado')

@admin_bp.route('/users', methods=['POST'])
@login_required('admin')
def create_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    
    # Validaciones básicas
    if not username or not email or not password or not role:
        return jsonify({'msg': 'Faltan campos obligatorios'}), 400
    
    if len(password) < 6:
        return jsonify({'msg': 'La contraseña debe tener al menos 6 caracteres'}), 400
    
    if User.query.filter((User.username==username)|(User.email==email)).first():
        return jsonify({'msg': 'Usuario o email ya existe'}), 409
    
    try:
        # Crear usuario principal
        hashed_password = generate_password_hash(password)
        user = User(
            username=username, 
            email=email, 
            password=hashed_password, 
            role=role,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(user)
        db.session.flush()  # Para obtener el ID
        
        # Crear perfil básico
        profile = Profile(
            user_id=user.id, 
            first_name=data.get('first_name', ''), 
            last_name=data.get('last_name', '')
        )
        db.session.add(profile)
        
        # Crear registro específico según el rol
        if role == 'student':
            student_code = data.get('student_code') or f'ST{user.id:04d}'
            enrollment_date_str = data.get('enrollment_date')
            enrollment_date = datetime.strptime(enrollment_date_str, '%Y-%m-%d').date() if enrollment_date_str else date.today()
            
            student = Student(
                user_id=user.id, 
                student_code=student_code, 
                enrollment_date=enrollment_date, 
                major=data.get('major', '')
            )
            db.session.add(student)
            
        elif role == 'teacher':
            employee_id = data.get('employee_id') or f'TE{user.id:04d}'
            hire_date_str = data.get('hire_date')
            hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date() if hire_date_str else date.today()
            
            teacher = Teacher(
                user_id=user.id, 
                employee_id=employee_id, 
                hire_date=hire_date, 
                department=data.get('department', '')
            )
            db.session.add(teacher)
        
        db.session.commit()
        return jsonify({'msg': 'Usuario creado exitosamente'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'Error al crear usuario: {str(e)}'}), 500
        teacher = Teacher(user_id=user.id, employee_id=employee_id, hire_date=hire_date, department=department)
        db.session.add(teacher)
    
    db.session.commit()
    return jsonify({'msg': 'Usuario registrado correctamente'}), 201

@admin_bp.route('/courses', methods=['GET', 'POST'])
@login_required('admin')
def manage_courses():
    if request.method == 'POST':
        course_code = request.form.get('course_code')
        course_name = request.form.get('course_name')
        teacher_id = request.form.get('teacher_id')
        credits = request.form.get('credits')
        description = request.form.get('description')

        if not course_code or not course_name or not teacher_id or not credits:
            flash('Todos los campos obligatorios deben ser completados.', 'danger')
            return redirect(url_for('admin.manage_courses'))

        # Buscar el teacher record, no el user record
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            flash('Docente no válido.', 'danger')
            return redirect(url_for('admin.manage_courses'))

        # Verificar que el código del curso no exista
        existing_course = Course.query.filter_by(course_code=course_code).first()
        if existing_course:
            flash('El código del curso ya existe.', 'danger')
            return redirect(url_for('admin.manage_courses'))

        new_course = Course(
            course_code=course_code,
            name=course_name,
            teacher_id=teacher_id,
            credits=int(credits),
            description=description if description else None
        )
        db.session.add(new_course)
        db.session.commit()

        flash('Curso creado exitosamente.', 'success')
        return redirect(url_for('admin.manage_courses'))

    courses = Course.query.all()
    
    # Obtener teachers con sus perfiles para mostrar nombres completos
    teachers_query = db.session.query(Teacher, User, Profile).join(User, Teacher.user_id == User.id).join(Profile, User.id == Profile.user_id).all()
    teachers = []
    for teacher, user, profile in teachers_query:
        teachers.append({
            'id': teacher.id,
            'first_name': profile.first_name,
            'last_name': profile.last_name,
            'email': user.email
        })
    
    # Obtener estudiantes con sus perfiles para mostrar nombres completos
    students_query = db.session.query(User, Profile).join(Profile, User.id == Profile.user_id).filter(User.role == 'student').all()
    students = []
    for user, profile in students_query:
        students.append({
            'id': user.id,
            'first_name': profile.first_name,
            'last_name': profile.last_name,
            'username': user.username,
            'email': user.email
        })
    
    return render_template('admin_courses.html', courses=courses, teachers=teachers, students=students)

@admin_bp.route('/courses/<int:course_id>/enroll', methods=['POST'])
@login_required('admin')
def enroll_students(course_id):
    student_ids = request.form.getlist('student_ids')
    course = Course.query.get_or_404(course_id)

    enrolled_count = 0
    for student_id in student_ids:
        # Buscar el registro de Student, no el User
        student_user = User.query.filter_by(id=student_id, role='student').first()
        if student_user:
            student = Student.query.filter_by(user_id=student_user.id).first()
            if student:
                # Verificar si ya está inscrito
                existing_enrollment = Enrollment.query.filter_by(
                    student_id=student.id, 
                    course_id=course_id
                ).first()
                
                if not existing_enrollment:
                    # Crear nueva inscripción
                    enrollment = Enrollment(
                        student_id=student.id,
                        course_id=course_id,
                        enrollment_date=datetime.now(),
                        status='enrolled'
                    )
                    db.session.add(enrollment)
                    enrolled_count += 1

    db.session.commit()
    if enrolled_count > 0:
        flash(f'{enrolled_count} estudiantes inscritos exitosamente.', 'success')
    else:
        flash('No se inscribieron estudiantes (ya inscritos o no válidos).', 'warning')
    return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/courses/<int:course_id>/students', methods=['GET'])
@login_required('admin')
def view_course_students(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Obtener estudiantes inscritos con sus perfiles
    enrollments = db.session.query(Enrollment, Student, User, Profile).join(
        Student, Enrollment.student_id == Student.id
    ).join(
        User, Student.user_id == User.id
    ).join(
        Profile, User.id == Profile.user_id
    ).filter(Enrollment.course_id == course_id).all()
    
    enrolled_students = []
    for enrollment, student, user, profile in enrollments:
        enrolled_students.append({
            'enrollment_id': enrollment.id,
            'student_id': student.id,
            'student_code': student.student_code,
            'first_name': profile.first_name,
            'last_name': profile.last_name,
            'email': user.email,
            'enrollment_date': enrollment.enrollment_date,
            'status': enrollment.status,
            'grade': enrollment.grade
        })
    
    return render_template('admin_course_students.html', course=course, enrolled_students=enrolled_students)

@admin_bp.route('/courses/<int:course_id>/enrollments/<int:enrollment_id>/status', methods=['POST'])
@login_required('admin')
def update_enrollment_status(course_id, enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    action = request.form.get('action')
    
    if action == 'withdraw':
        enrollment.status = 'dropped'  # Cambiado de 'withdrawn' a 'dropped' para cumplir constraint
        db.session.commit()
        flash('Estudiante retirado del curso exitosamente.', 'success')
    
    return redirect(url_for('admin.view_course_students', course_id=course_id))

# NOTA: Las calificaciones solo pueden ser gestionadas por los profesores
# La función update_student_grade ha sido removida por seguridad académica

# === SISTEMA DE LOGS DE ACCESO ===

@admin_bp.route('/logs')
@login_required('admin')
def access_logs():
    """Mostrar página de logs de acceso"""
    return render_template('admin_logs.html')

@admin_bp.route('/logs/data')
@login_required('admin')
def get_access_logs():
    """API para obtener logs de acceso con filtros y paginación"""
    from app.infrastructure.models import AccessLog
    
    # Parámetros de filtrado
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    user_filter = request.args.get('user', '')
    action_filter = request.args.get('action', '')
    status_filter = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Construir query base
    query = AccessLog.query.join(User, AccessLog.user_id == User.id, isouter=True)
      # Aplicar filtros
    if user_filter:
        # Usar join con la tabla User para filtrar por username
        query = query.join(User).filter(User.username.ilike(f'%{user_filter}%'))
    
    if action_filter:
        query = query.filter(AccessLog.action.ilike(f'%{action_filter}%'))
    
    if status_filter:
        query = query.filter(AccessLog.status == status_filter)
    
    if date_from:
        query = query.filter(AccessLog.timestamp >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        query = query.filter(AccessLog.timestamp <= datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S'))
    
    # Ordenar por timestamp descendente
    query = query.order_by(AccessLog.timestamp.desc())
    
    # Paginación
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items
    
    # Convertir a JSON
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log.id,
            'username': log.username,
            'action': log.action,
            'endpoint': log.endpoint,
            'ip_address': log.ip_address,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if log.timestamp else '',
            'status': log.status,
            'details': log.details,
            'user_agent': log.user_agent[:100] + '...' if log.user_agent and len(log.user_agent) > 100 else log.user_agent
        })
    
    return jsonify({
        'logs': logs_data,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next
        }
    })

@admin_bp.route('/logs/stats')
@login_required('admin')
def get_logs_stats():
    """API para obtener estadísticas de logs de acceso"""
    from app.infrastructure.models import AccessLog
    from sqlalchemy import func
    
    # Estadísticas generales
    total_logs = AccessLog.query.count()
    failed_logins = AccessLog.query.filter(
        AccessLog.action == 'LOGIN',
        AccessLog.status == 'FAILED'
    ).count()
    
    # Accesos por día (últimos 7 días)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_stats = db.session.query(
        func.date(AccessLog.timestamp).label('date'),
        func.count(AccessLog.id).label('count')
    ).filter(
        AccessLog.timestamp >= seven_days_ago
    ).group_by(
        func.date(AccessLog.timestamp)
    ).order_by(
        func.date(AccessLog.timestamp)
    ).all()
      # Top usuarios activos
    active_users = db.session.query(
        User.username,
        func.count(AccessLog.id).label('access_count')
    ).join(
        AccessLog, User.id == AccessLog.user_id
    ).filter(
        AccessLog.timestamp >= seven_days_ago
    ).group_by(
        User.username
    ).order_by(
        func.count(AccessLog.id).desc()
    ).limit(10).all()
    
    # Acciones más comunes
    top_actions = db.session.query(
        AccessLog.action,
        func.count(AccessLog.id).label('count')
    ).group_by(
        AccessLog.action
    ).order_by(
        func.count(AccessLog.id).desc()
    ).limit(10).all()
    
    return jsonify({
        'total_logs': total_logs,
        'failed_logins': failed_logins,
        'daily_stats': [{'date': str(stat.date), 'count': stat.count} for stat in daily_stats],
        'active_users': [{'username': user.username, 'count': user.access_count} for user in active_users],
        'top_actions': [{'action': action.action, 'count': action.count} for action in top_actions]
    })
