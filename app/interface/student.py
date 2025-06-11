from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from app.interface.auth import login_required
from app.infrastructure.models import User, Profile, Student, Course, Teacher, Enrollment, Grade, Assignment, Attendance
from app.main import db
import os
import time

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard', methods=['GET'])
@login_required('student')
def dashboard():
    """Dashboard principal del estudiante con vista HTML"""
    user_id = session.get('user_id')
    student = Student.query.filter_by(user_id=user_id).first()
    
    if not student:
        flash('No se encontró información del estudiante.', 'error')
        return redirect(url_for('auth.login'))
    
    # Obtener datos básicos para mostrar en el template
    user = User.query.get(user_id)
    profile = Profile.query.filter_by(user_id=user_id).first()
    
    return render_template('student_dashboard.html', 
                         user=user, 
                         profile=profile, 
                         student=student)

@student_bp.route('/')
@login_required('student')
def student_home():
    """Redirige al dashboard del estudiante"""
    return redirect(url_for('student.dashboard'))

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required('student')
def profile():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    profile = Profile.query.filter_by(user_id=user_id).first()
    student = Student.query.filter_by(user_id=user_id).first()
    
    # Obtener enrollments para mostrar en el perfil
    enrollments = []
    if student:
        enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    
    if request.method == 'POST':
        try:
            # Actualizar información personal
            if profile:
                profile.first_name = request.form.get('first_name', profile.first_name)
                profile.last_name = request.form.get('last_name', profile.last_name)
                profile.phone = request.form.get('phone', profile.phone)
                profile.address = request.form.get('address', profile.address)
                profile.emergency_contact = request.form.get('emergency_contact', profile.emergency_contact)
                profile.emergency_phone = request.form.get('emergency_phone', profile.emergency_phone)
                
                # Campos nuevos
                birth_date = request.form.get('birth_date')
                if birth_date:
                    from datetime import datetime
                    profile.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
            
            # Actualizar información académica
            if student:
                student.major = request.form.get('major', student.major)
            
            # Manejo de avatar mejorado
            avatar = request.files.get('avatar')
            if avatar and avatar.filename:
                # Validar archivo
                allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
                ext = os.path.splitext(avatar.filename)[1].lower()
                
                if ext in allowed_extensions:
                    # Crear directorio si no existe
                    upload_dir = os.path.join('app', 'static', 'avatars')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Generar nombre único
                    filename = f'avatar_{user_id}_{int(time.time())}{ext}'
                    filepath = os.path.join(upload_dir, filename)
                    
                    # Verificar tamaño (máx 2MB)
                    avatar.seek(0, 2)  # Ir al final del archivo
                    size = avatar.tell()
                    avatar.seek(0)  # Volver al inicio
                    
                    if size <= 2 * 1024 * 1024:  # 2MB
                        avatar.save(filepath)
                        profile.avatar_url = f'/static/avatars/{filename}'
                        flash('Foto de perfil actualizada correctamente', 'success')
                    else:
                        flash('La imagen es demasiado grande. Máximo 2MB permitido.', 'error')
                else:
                    flash('Formato de imagen no soportado. Use JPG, PNG o GIF.', 'error')
            
            db.session.commit()
            flash('Perfil actualizado correctamente', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el perfil: {str(e)}', 'error')
        
        return redirect(url_for('student.profile'))
    
    return render_template('student_profile.html', 
                         user=user, 
                         profile=profile, 
                         student=student,
                         enrollments=enrollments)

@student_bp.route('/courses')
@login_required('student')
def courses():
    user_id = session.get('user_id')
    student = Student.query.filter_by(user_id=user_id).first()
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    courses = []
    for e in enrollments:
        course = Course.query.get(e.course_id)
        teacher = Teacher.query.get(course.teacher_id)
        teacher_user = User.query.get(teacher.user_id)
        courses.append({
            'id': course.id,
            'course_code': course.course_code,
            'name': course.name,
            'teacher_name': f'{teacher_user.username}',
            'credits': course.credits,
            'status': e.status
        })
    return render_template('student_courses.html', courses=courses)

@student_bp.route('/courses/<int:course_id>')
@login_required('student')
def course_detail(course_id):
    """Vista detallada de un curso específico para el estudiante"""
    try:
        user_id = session.get('user_id')
        student = Student.query.filter_by(user_id=user_id).first()
        
        if not student:
            flash('No se encontró información del estudiante.', 'error')
            return redirect(url_for('student.courses'))
        
        # Verificar que el estudiante está inscrito en el curso
        enrollment = Enrollment.query.filter_by(
            student_id=student.id, 
            course_id=course_id
        ).first()
        
        if not enrollment:
            flash('No tienes acceso a este curso.', 'error')
            return redirect(url_for('student.courses'))
        
        # Obtener información del curso
        course = Course.query.get_or_404(course_id)
        teacher = Teacher.query.get(course.teacher_id)
        teacher_user = User.query.get(teacher.user_id) if teacher else None
        teacher_profile = Profile.query.filter_by(user_id=teacher.user_id).first() if teacher else None
        
        # Obtener calificaciones del estudiante en este curso
        grades = Grade.query.filter_by(
            course_id=course_id,
            student_id=student.id
        ).all()
        
        # Calcular promedio
        course_grades = [grade.score for grade in grades if grade.score is not None]
        course_average = sum(course_grades) / len(course_grades) if course_grades else 0
        
        # Obtener asignaciones/tareas del curso
        assignments = Assignment.query.filter_by(course_id=course_id).all()
        
        # Obtener asistencias del estudiante
        attendances = Attendance.query.filter_by(
            course_id=course_id,
            student_id=student.id
        ).all()
        
        # Calcular estadísticas de asistencia
        total_classes = Attendance.query.filter_by(course_id=course_id).count()
        attended_classes = len([a for a in attendances if a.status == 'present'])
        attendance_rate = (attended_classes / total_classes * 100) if total_classes > 0 else 0
        
        # Información del profesor
        teacher_name = "No asignado"
        if teacher_user and teacher_profile:
            teacher_name = f"{teacher_profile.first_name} {teacher_profile.last_name}"
        elif teacher_user:
            teacher_name = teacher_user.username
        
        return render_template('student_course_detail.html',
                             course=course,
                             enrollment=enrollment,
                             teacher_name=teacher_name,
                             teacher_profile=teacher_profile,
                             grades=grades,
                             course_average=round(course_average, 1),
                             assignments=assignments,
                             attendances=attendances,
                             attendance_rate=round(attendance_rate, 1),
                             total_classes=total_classes)
        
    except Exception as e:
        flash(f'Error al cargar el curso: {str(e)}', 'error')
        return redirect(url_for('student.courses'))

@student_bp.route('/dashboard/data')
@login_required('student')
def dashboard_data():
    """Obtener datos estadísticos para el dashboard del estudiante"""
    try:
        user_id = session.get('user_id')
        student = Student.query.filter_by(user_id=user_id).first()
        
        if not student:
            return jsonify({'error': 'Estudiante no encontrado'}), 404
        
        # Obtener enrollments del estudiante
        enrollments = Enrollment.query.filter_by(student_id=student.id).all()
        
        # Calcular estadísticas
        courses_count = len(enrollments)
        
        # Obtener información detallada de los cursos
        courses_data = []
        total_grades = []
        
        for enrollment in enrollments:
            course = Course.query.get(enrollment.course_id)
            if course:
                teacher = Teacher.query.get(course.teacher_id)
                teacher_user = User.query.get(teacher.user_id) if teacher else None
                teacher_profile = Profile.query.filter_by(user_id=teacher.user_id).first() if teacher else None
                  # Obtener calificaciones del estudiante en este curso
                grades = Grade.query.filter_by(
                    course_id=course.id,
                    student_id=student.id
                ).all()
                
                course_grades = [grade.score for grade in grades if grade.score is not None]
                course_average = sum(course_grades) / len(course_grades) if course_grades else 0
                
                if course_average > 0:
                    total_grades.append(course_average)
                
                # Calcular progreso del curso (basado en fechas o asignaciones completadas)
                progress = min(75 + (len(course_grades) * 5), 100)  # Simulación de progreso
                
                teacher_name = "No asignado"
                if teacher_user and teacher_profile:
                    teacher_name = f"{teacher_profile.first_name} {teacher_profile.last_name}"
                elif teacher_user:
                    teacher_name = teacher_user.username
                
                courses_data.append({
                    'id': course.id,
                    'name': course.name,
                    'course_code': course.course_code,
                    'credits': course.credits,
                    'teacher_name': teacher_name,
                    'progress': progress,
                    'average_grade': round(course_average, 1) if course_average > 0 else 0,
                    'status': enrollment.status
                })
        
        # Calcular promedio general
        general_average = sum(total_grades) / len(total_grades) if total_grades else 0
        
        # Simular datos adicionales
        assignments_count = courses_count * 2  # Aproximación
        upcoming_count = max(1, courses_count // 2)  # Aproximación
        
        return jsonify({
            'courses_count': courses_count,
            'assignments_count': assignments_count,
            'upcoming_count': upcoming_count,
            'general_average': round(general_average, 1),
            'courses': courses_data
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener datos: {str(e)}'}), 500
