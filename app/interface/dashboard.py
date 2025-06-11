from flask import Blueprint, render_template, redirect, url_for, session
from app.interface.auth import login_required

# Este blueprint sirve como dashboard general y redirige según el rol

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required()
def dashboard_home():
    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('dashboard.admin_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('dashboard.teacher_dashboard'))
    elif role == 'student':
        return redirect(url_for('dashboard.student_dashboard'))
    return 'Rol no reconocido', 403

@dashboard_bp.route('/admin')
@login_required('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html', 
                         user_role=session.get('role', 'admin'),
                         user_name=session.get('username', 'Admin'))

@dashboard_bp.route('/teacher')
@login_required('teacher')
def teacher_dashboard():
    return render_template('teacher_dashboard.html',
                         user_role=session.get('role', 'teacher'),
                         user_name=session.get('username', 'Docente'))

@dashboard_bp.route('/student')
@login_required('student')
def student_dashboard():
    return render_template('student_dashboard.html',
                         user_role=session.get('role', 'student'),
                         user_name=session.get('username', 'Estudiante'))

@dashboard_bp.route('/login')
def login():
    return render_template('login.html')
