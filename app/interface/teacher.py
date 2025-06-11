from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from app.interface.auth import login_required
from app.infrastructure.models import User, Profile, Teacher, Course, Enrollment, Student, Grade, Assignment, Attendance, Submission
from app.main import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import os

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/')
@login_required('teacher')
def teacher_home():
    return render_template('teacher/home.html')

@teacher_bp.route('/dashboard', methods=['GET'])
@login_required('teacher')
def dashboard():
    """Dashboard principal del profesor con vista HTML"""
    user_id = session.get('user_id')
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    
    if not teacher:
        flash('No se encontró información del profesor.', 'error')
        return redirect(url_for('auth.login'))
    
    # Obtener datos básicos para mostrar en el template
    user = User.query.get(user_id)
    profile = Profile.query.filter_by(user_id=user_id).first()
    
    return render_template('teacher_dashboard.html', 
                         user=user, 
                         profile=profile, 
                         teacher=teacher)

@teacher_bp.route('/profile', methods=['GET', 'POST'])
@login_required('teacher')
def profile():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    profile = Profile.query.filter_by(user_id=user_id).first()
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    
    # Obtener estadísticas adicionales para el perfil del profesor
    courses_count = Course.query.filter_by(teacher_id=teacher.id).count() if teacher else 0
    total_students = 0
    if teacher:
        total_students = db.session.query(func.count(Enrollment.id)).join(
            Course, Enrollment.course_id == Course.id
        ).filter(Course.teacher_id == teacher.id).scalar() or 0
    
    if request.method == 'POST':
        # Actualizar datos
        if profile:
            profile.first_name = request.form.get('first_name', profile.first_name)
            profile.last_name = request.form.get('last_name', profile.last_name)
            profile.phone = request.form.get('phone', profile.phone)
        
        if teacher:
            teacher.department = request.form.get('department', teacher.department)
        
        # Manejo de avatar
        avatar = request.files.get('avatar')
        if avatar and avatar.filename:
            ext = os.path.splitext(avatar.filename)[1]
            filename = f'avatar_{user_id}{ext}'
            path = os.path.join('app', 'static', 'avatars', filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            avatar.save(path)
            if profile:
                profile.avatar_url = f'/static/avatars/{filename}'
        
        db.session.commit()
        flash('Perfil actualizado correctamente', 'success')
        return redirect(url_for('teacher.profile'))
    
    return render_template('teacher_profile.html', 
                         user=user, 
                         profile=profile, 
                         teacher=teacher,
                         courses_count=courses_count,
                         total_students=total_students)

@teacher_bp.route('/courses')
@login_required('teacher')
def courses():
    user_id = session.get('user_id')
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    courses = Course.query.filter_by(teacher_id=teacher.id).all()
    return render_template('teacher_courses.html', courses=courses)

# Nuevas rutas API para el sistema profesional de cursos

@teacher_bp.route('/courses/data')
@login_required('teacher')
def courses_data():
    """Obtener datos de cursos con estadísticas para el dashboard"""
    try:
        user_id = session.get('user_id')
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        
        if not teacher:
            return jsonify({'error': 'Profesor no encontrado'}), 404
        
        # Obtener cursos del profesor
        courses = Course.query.filter_by(teacher_id=teacher.id).all()
        
        # Calcular estadísticas generales
        total_courses = len(courses)
        total_students = 0
        pending_assignments = 0
        general_average = 0
        
        courses_data = []
        
        for course in courses:
            # Contar estudiantes en el curso
            students_count = Enrollment.query.filter_by(course_id=course.id).count()
            total_students += students_count
            
            # Obtener tareas pendientes 
            try:
                pending_count = Assignment.query.filter_by(
                    course_id=course.id,
                    status='active'
                ).count()
                pending_assignments += pending_count
            except:
                pending_count = 0
            
            # Calcular promedio del curso
            try:
                avg_grade = db.session.query(func.avg(Grade.score)).filter_by(course_id=course.id).scalar()
                course_average = round(avg_grade, 2) if avg_grade else 0
            except:
                course_average = 0
            
            # Calcular progreso del curso
            progress = min(85 + (course.id % 15), 100)  # Simulado por ahora
            
            courses_data.append({
                'id': course.id,
                'name': course.name,
                'course_code': course.course_code,
                'description': course.description or 'Sin descripción',
                'credits': course.credits,
                'semester': course.semester or '2024-1',
                'students_count': students_count,
                'pending_assignments': pending_count,
                'average': course_average,
                'progress': progress,
                'status': 'active' if course.is_active else 'inactive'
            })
          # Calcular promedio general
        if courses_data:
            general_average = round(sum(c['average'] for c in courses_data) / len(courses_data), 2)
        
        stats = {
            'active_courses': total_courses,
            'total_students': total_students,
            'pending_assignments': pending_assignments,
            'general_average': general_average
        }
        
        return jsonify({
            'success': True,
            'stats': stats,
            'courses': courses_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@teacher_bp.route('/courses/<int:course_id>/grades', methods=['GET', 'POST'])
@login_required('teacher')
def manage_grades(course_id):
    """Gestionar calificaciones de un curso"""
    try:
        user_id = session.get('user_id')
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        
        if not teacher:
            return jsonify({'error': 'Profesor no encontrado'}), 404
        
        course = Course.query.get_or_404(course_id)
        
        # Verificar que el curso pertenece al profesor
        if course.teacher_id != teacher.id:
            return jsonify({'error': 'No autorizado para este curso'}), 403
        
        if request.method == 'GET':
            # Obtener calificaciones existentes
            try:
                grades = db.session.query(Grade, Student, User, Profile).join(
                    Student, Grade.student_id == Student.id
                ).join(
                    User, Student.user_id == User.id
                ).join(
                    Profile, User.id == Profile.user_id
                ).filter(
                    Grade.course_id == course_id
                ).all()
                
                grades_data = []
                for grade, student, user, profile in grades:
                    grades_data.append({
                        'id': grade.id,
                        'student_id': student.id,
                        'student_name': f'{profile.first_name} {profile.last_name}',
                        'student_code': student.student_code,
                        'assignment_name': grade.assignment_name,
                        'score': grade.score,
                        'max_score': grade.max_score,
                        'percentage': round((grade.score / grade.max_score * 100), 2) if grade.max_score > 0 else 0,
                        'date': grade.date.strftime('%Y-%m-%d') if grade.date else '',
                        'comments': grade.comments
                    })
                
                return jsonify({
                    'success': True,
                    'grades': grades_data
                })
            
            except Exception as e:
                return jsonify({'error': f'Error al obtener calificaciones: {str(e)}'}), 500
        
        elif request.method == 'POST':
            # Crear nueva calificación
            try:
                data = request.json
                
                new_grade = Grade(
                    course_id=course_id,
                    student_id=data['student_id'],
                    assignment_name=data['assignment_name'],
                    score=data['score'],
                    max_score=data['max_score'],
                    date=datetime.now(),
                    comments=data.get('comments', '')
                )
                
                db.session.add(new_grade)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Calificación agregada exitosamente'
                })
                
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': f'Error al guardar calificación: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@teacher_bp.route('/courses/<int:course_id>/assignments', methods=['GET', 'POST'])
@login_required('teacher')
def manage_assignments(course_id):
    """Gestionar tareas de un curso"""
    try:
        user_id = session.get('user_id')
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        
        if not teacher:
            return jsonify({'error': 'Profesor no encontrado'}), 404
        
        course = Course.query.get_or_404(course_id)
        
        # Verificar que el curso pertenece al profesor
        if course.teacher_id != teacher.id:
            return jsonify({'error': 'No autorizado para este curso'}), 403
        
        if request.method == 'GET':
            # Obtener tareas del curso
            assignments = Assignment.query.filter_by(course_id=course_id).all()
            
            assignments_data = []
            for assignment in assignments:
                # Contar entregas
                submissions_count = Submission.query.filter_by(assignment_id=assignment.id).count()
                
                assignments_data.append({
                    'id': assignment.id,
                    'title': assignment.title,
                    'description': assignment.description,
                    'due_date': assignment.due_date.strftime('%Y-%m-%d %H:%M') if assignment.due_date else '',
                    'max_score': assignment.max_score,
                    'status': assignment.status,
                    'submissions_count': submissions_count,
                    'created_date': assignment.created_date.strftime('%Y-%m-%d') if assignment.created_date else ''
                })
            
            return jsonify({
                'success': True,
                'assignments': assignments_data
            })
        
        elif request.method == 'POST':
            # Crear nueva tarea
            try:
                data = request.json
                
                new_assignment = Assignment(
                    course_id=course_id,
                    title=data['title'],
                    description=data.get('description', ''),
                    due_date=datetime.strptime(data['due_date'], '%Y-%m-%d %H:%M'),
                    max_score=data['max_score'],
                    status='active',
                    created_date=datetime.now()
                )
                
                db.session.add(new_assignment)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Tarea creada exitosamente'
                })
                
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': f'Error al crear tarea: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@teacher_bp.route('/courses/<int:course_id>/attendance', methods=['GET', 'POST'])
@login_required('teacher')
def manage_attendance(course_id):
    """Gestionar asistencias de un curso"""
    try:
        user_id = session.get('user_id')
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        
        if not teacher:
            return jsonify({'error': 'Profesor no encontrado'}), 404
        
        course = Course.query.get_or_404(course_id)
        
        # Verificar que el curso pertenece al profesor
        if course.teacher_id != teacher.id:
            return jsonify({'error': 'No autorizado para este curso'}), 403
        
        if request.method == 'GET':
            # Obtener asistencias del curso
            try:
                # Obtener estudiantes del curso
                enrollments = db.session.query(Enrollment, Student, User, Profile).join(
                    Student, Enrollment.student_id == Student.id
                ).join(
                    User, Student.user_id == User.id
                ).join(
                    Profile, User.id == Profile.user_id
                ).filter(
                    Enrollment.course_id == course_id
                ).all()
                
                students_attendance = []
                
                for enrollment, student, user, profile in enrollments:
                    # Obtener registros de asistencia del estudiante
                    attendance_records = Attendance.query.filter_by(
                        course_id=course_id,
                        student_id=student.id
                    ).order_by(desc(Attendance.date)).limit(10).all()
                    
                    # Calcular estadísticas de asistencia
                    total_classes = Attendance.query.filter_by(
                        course_id=course_id,
                        student_id=student.id
                    ).count()
                    
                    present_count = Attendance.query.filter_by(
                        course_id=course_id,
                        student_id=student.id,
                        status='present'
                    ).count()
                    
                    attendance_rate = round((present_count / total_classes * 100), 1) if total_classes > 0 else 0
                    
                    students_attendance.append({
                        'student_id': student.id,
                        'student_code': student.student_code,
                        'student_name': f'{profile.first_name} {profile.last_name}',
                        'total_classes': total_classes,
                        'present_count': present_count,
                        'attendance_rate': attendance_rate,
                        'recent_records': [
                            {
                                'date': record.date.strftime('%Y-%m-%d') if record.date else '',
                                'status': record.status,
                                'notes': record.notes
                            } for record in attendance_records
                        ]
                    })
                
                return jsonify({
                    'success': True,
                    'attendance': students_attendance
                })
                
            except Exception as e:
                return jsonify({'error': f'Error al obtener asistencias: {str(e)}'}), 500
        
        elif request.method == 'POST':
            # Registrar nueva asistencia
            try:
                data = request.json
                
                new_attendance = Attendance(
                    course_id=course_id,
                    student_id=data['student_id'],
                    date=datetime.strptime(data['date'], '%Y-%m-%d'),
                    status=data['status'],
                    notes=data.get('notes', '')
                )
                
                db.session.add(new_attendance)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Asistencia registrada exitosamente'
                })
                
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': f'Error al registrar asistencia: {str(e)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Mantener la ruta original para compatibilidad
@teacher_bp.route('/courses/<int:course_id>/students')
@login_required('teacher')
def course_students(course_id):
    """Vista HTML de estudiantes inscritos en un curso específico"""
    try:
        course = Course.query.get_or_404(course_id)
        
        # Asegurarse que el profesor solo vea sus cursos
        teacher = Teacher.query.filter_by(user_id=session['user_id']).first()
        if not teacher or course.teacher_id != teacher.id:
            flash('Acceso no autorizado al curso.', 'danger')
            return redirect(url_for('teacher.courses'))

        # Obtener estudiantes inscritos con información completa
        enrollments = db.session.query(Enrollment, Student, User, Profile).join(
            Student, Enrollment.student_id == Student.id
        ).join(
            User, Student.user_id == User.id
        ).left_join(
            Profile, User.id == Profile.user_id
        ).filter(
            Enrollment.course_id == course_id
        ).all()
        
        students_in_course = []
        for enrollment, student, user, profile in enrollments:
            # Calcular promedio del estudiante en este curso
            try:
                avg_grade = db.session.query(func.avg(Grade.score)).filter_by(
                    course_id=course_id,
                    student_id=student.id
                ).scalar()
                average = round(avg_grade, 2) if avg_grade else 0
            except:
                average = 0
            
            # Calcular asistencias
            try:
                total_classes = Attendance.query.filter_by(course_id=course_id).count()
                attended_classes = Attendance.query.filter_by(
                    course_id=course_id,
                    student_id=student.id,
                    status='present'
                ).count()
                attendance_rate = round((attended_classes / total_classes * 100), 1) if total_classes > 0 else 0
            except:
                attendance_rate = 0
                
            # Preparar nombre del estudiante
            if profile:
                student_name = f'{profile.first_name} {profile.last_name}'
                phone = profile.phone or 'No especificado'
            else:
                student_name = user.username
                phone = 'No especificado'
            
            students_in_course.append({
                'id': student.id,
                'user_id': user.id,
                'student_code': student.student_code,
                'name': student_name,
                'email': user.email,
                'phone': phone,
                'enrollment_date': enrollment.enrollment_date.strftime('%Y-%m-%d') if enrollment.enrollment_date else '',
                'average': average,
                'attendance_rate': attendance_rate,
                'status': enrollment.status or 'enrolled'
            })

        return render_template('teacher_course_students.html', 
                             course=course, 
                             students=students_in_course)
        
    except Exception as e:
        flash(f'Error al cargar estudiantes del curso: {str(e)}', 'error')
        return redirect(url_for('teacher.courses'))

@teacher_bp.route('/students/<int:student_id>/detail')
@login_required('teacher')
def student_detail(student_id):
    """API para obtener detalles completos de un estudiante"""
    try:
        user_id = session.get('user_id')
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        
        if not teacher:
            return jsonify({'error': 'Profesor no encontrado'}), 404
        
        # Obtener información del estudiante
        student_data = db.session.query(Student, User, Profile).join(
            User, Student.user_id == User.id
        ).left_join(
            Profile, User.id == Profile.user_id
        ).filter(Student.id == student_id).first()
        
        if not student_data:
            return jsonify({'error': 'Estudiante no encontrado'}), 404
        
        student, user, profile = student_data
        
        # Verificar que el estudiante está en algún curso del profesor
        enrollment = db.session.query(Enrollment).join(
            Course, Enrollment.course_id == Course.id
        ).filter(
            Enrollment.student_id == student_id,
            Course.teacher_id == teacher.id
        ).first()
        
        if not enrollment:
            return jsonify({'error': 'No autorizado para ver este estudiante'}), 403
        
        # Preparar nombre del estudiante
        if profile:
            student_name = f'{profile.first_name} {profile.last_name}'
            phone = profile.phone or 'No especificado'
        else:
            student_name = user.username
            phone = 'No especificado'
        
        # Obtener calificaciones recientes
        recent_grades = db.session.query(Grade).join(
            Course, Grade.course_id == Course.id
        ).filter(
            Grade.student_id == student_id,
            Course.teacher_id == teacher.id
        ).order_by(desc(Grade.date)).limit(5).all()
        
        grades_data = []
        for grade in recent_grades:
            grades_data.append({
                'assignment_name': grade.assignment_name,
                'score': grade.score,
                'max_score': grade.max_score,
                'percentage': round((grade.score / grade.max_score * 100), 2) if grade.max_score > 0 else 0,
                'date': grade.date.strftime('%Y-%m-%d') if grade.date else '',
                'comments': grade.comments
            })
        
        # Obtener asistencia reciente
        recent_attendance = db.session.query(Attendance).join(
            Course, Attendance.course_id == Course.id
        ).filter(
            Attendance.student_id == student_id,
            Course.teacher_id == teacher.id
        ).order_by(desc(Attendance.date)).limit(10).all()
        
        attendance_data = []
        for att in recent_attendance:
            attendance_data.append({
                'date': att.date.strftime('%Y-%m-%d') if att.date else '',
                'status': att.status,
                'notes': att.notes
            })
        
        # Calcular estadísticas generales
        total_grades = db.session.query(Grade).join(
            Course, Grade.course_id == Course.id
        ).filter(
            Grade.student_id == student_id,
            Course.teacher_id == teacher.id
        ).all()
        
        avg_grade = sum(g.score for g in total_grades) / len(total_grades) if total_grades else 0
        
        total_classes = db.session.query(Attendance).join(
            Course, Attendance.course_id == Course.id
        ).filter(
            Course.teacher_id == teacher.id
        ).count()
        
        attended_classes = db.session.query(Attendance).join(
            Course, Attendance.course_id == Course.id
        ).filter(
            Attendance.student_id == student_id,
            Course.teacher_id == teacher.id,
            Attendance.status == 'present'
        ).count()
        
        attendance_rate = round((attended_classes / total_classes * 100), 1) if total_classes > 0 else 0
        
        return jsonify({
            'success': True,
            'student': {
                'id': student.id,
                'student_code': student.student_code,
                'name': student_name,
                'email': user.email,
                'phone': phone,
                'enrollment_date': enrollment.enrollment_date.strftime('%Y-%m-%d') if enrollment.enrollment_date else '',
                'average': round(avg_grade, 2),
                'attendance_rate': attendance_rate,
                'status': enrollment.status or 'enrolled',
                'recent_grades': grades_data,
                'recent_attendance': attendance_data
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error al obtener detalles del estudiante: {str(e)}'}), 500

@teacher_bp.route('/courses/<int:course_id>/students/api')
@login_required('teacher')
def get_course_students_api(course_id):
    """API para obtener estudiantes de un curso en formato JSON"""
    try:
        print(f"[DEBUG] API llamada para curso {course_id}")
        
        user_id = session.get('user_id')
        print(f"[DEBUG] User ID de sesión: {user_id}")
        
        # Verificar que el usuario existe y es profesor
        user = User.query.get(user_id)
        if not user or user.role != 'teacher':
            print(f"[DEBUG] Error: Usuario no válido o no es profesor. User: {user}, Role: {user.role if user else 'None'}")
            return jsonify({'error': 'Usuario no autorizado'}), 403
        
        # Buscar o crear registro Teacher si no existe
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        if not teacher:
            print(f"[DEBUG] Creando registro Teacher para user_id {user_id}")
            teacher = Teacher(
                user_id=user_id,
                employee_id=f"EMP{user_id:03d}",
                hire_date=user.created_at.date() if user.created_at else '2024-01-01',
                department="Facultad de Ingeniería"
            )
            db.session.add(teacher)
            db.session.commit()
            print(f"[DEBUG] Registro Teacher creado con ID {teacher.id}")
        
        print(f"[DEBUG] Profesor encontrado: {teacher.id}")
        
        if not teacher:
            print("[DEBUG] Error: Profesor no encontrado después de creación")
            return jsonify({'error': 'Profesor no encontrado'}), 404
        
        course = Course.query.get_or_404(course_id)
        print(f"[DEBUG] Curso encontrado: {course.name}, Teacher ID: {course.teacher_id}")
        
        # Verificar que el curso pertenece al profesor
        if course.teacher_id != teacher.id:
            print(f"[DEBUG] Error: No autorizado. Curso teacher_id: {course.teacher_id}, Usuario teacher_id: {teacher.id}")
            return jsonify({'error': 'No autorizado para este curso'}), 403
          # Obtener estudiantes inscritos
        enrollments = db.session.query(Enrollment, Student, User, Profile).join(
            Student, Enrollment.student_id == Student.id
        ).join(
            User, Student.user_id == User.id
        ).outerjoin(
            Profile, User.id == Profile.user_id
        ).filter(
            Enrollment.course_id == course_id
        ).all()
        
        print(f"[DEBUG] Inscripciones encontradas: {len(enrollments)}")
        
        students_data = []
        for enrollment, student, user, profile in enrollments:
            # Calcular promedio del estudiante en este curso
            try:
                grades = Grade.query.filter_by(
                    course_id=course_id,
                    student_id=student.id
                ).all()
                
                if grades:
                    total_score = sum(g.score for g in grades)
                    total_max = sum(g.max_score for g in grades)
                    final_grade = round((total_score / total_max * 100), 2) if total_max > 0 else 0
                else:
                    final_grade = 0
            except:
                final_grade = 0
            
            # Preparar nombre del estudiante
            if profile:
                full_name = f'{profile.first_name} {profile.last_name}'
            else:
                full_name = user.username
            
            student_data = {
                'id': student.id,
                'student_code': student.student_code,
                'full_name': full_name,
                'email': user.email,
                'status': enrollment.status or 'enrolled',
                'final_grade': final_grade,
                'enrollment_date': enrollment.enrollment_date.strftime('%Y-%m-%d') if enrollment.enrollment_date else ''
            }
            students_data.append(student_data)
            print(f"[DEBUG] Procesado estudiante: {student.student_code} - {full_name}")
        
        print(f"[DEBUG] Devolviendo {len(students_data)} estudiantes")
        return jsonify(students_data)
        
    except Exception as e:
        print(f"[DEBUG] Error en API: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error al obtener estudiantes: {str(e)}'}), 500
