from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, send_from_directory, abort
from app.infrastructure.models import User, AccessLog
from app.main import db
from datetime import timedelta, datetime
import os
import logging

auth_bp = Blueprint('auth', __name__)

# Configurar el registro para depuración
logging.basicConfig(level=logging.WARNING)

def log_access(user_id=None, action='UNKNOWN', endpoint=None, status='SUCCESS', details=None):
    """Función para registrar accesos al sistema"""
    try:
        access_log = AccessLog(
            user_id=user_id,
            action=action,
            endpoint=endpoint or request.endpoint,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:255],  # Limitar longitud
            timestamp=datetime.utcnow(),
            status=status,
            details=details
        )
        db.session.add(access_log)
        db.session.commit()
    except Exception as e:
        logging.error(f"Error logging access: {str(e)}")
        # No fallar el proceso principal por errores de logging
        pass

def login_required(role=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            if role and session.get('role') != role:
                return 'Acceso denegado', 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logging.warning(f"Estado de la sesión: {session}")  # Registrar el estado de la sesión
        return login_required(role='admin')(f)(*args, **kwargs)
    return decorated_function

def redirect_by_role():
    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('dashboard.admin_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('dashboard.teacher_dashboard'))
    elif role == 'student':
        return redirect(url_for('dashboard.student_dashboard'))
    else:
        return 'Rol no reconocido', 403

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    data = request.form
    user = User.query.filter((User.username==data.get('username')) | (User.email==data.get('username'))).first()
    if user and user.check_password(data.get('password')):
        session['user_id'] = user.id
        session['role'] = user.role
        session['user_role'] = user.role  # Para compatibilidad con templates
        # Guardar el nombre del usuario en la sesión para mensajes de bienvenida
        profile = getattr(user, 'profile', None)
        if profile:
            session['user_name'] = f"{profile.first_name} {profile.last_name}"
        else:
            session['user_name'] = user.username # Fallback al nombre de usuario
        log_access(user_id=user.id, action='login', status='SUCCESS')
        return redirect_by_role()
    return render_template('login.html', error='Credenciales inválidas')

@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    username = session.get('user_name')
    session.clear()
    log_access(user_id=user_id, action='logout', status='SUCCESS')
    return redirect(url_for('auth.login'))

@auth_bp.route('/avatars/<filename>')
def protected_avatar(filename):
    # Verificar si el usuario está autenticado
    if 'user_id' not in session:
        abort(403)  # Prohibido

    # Obtener el ID del usuario autenticado
    user_id = session['user_id']

    # Validar que el archivo pertenece al usuario autenticado
    # Aquí asumimos que los nombres de archivo están relacionados con el ID del usuario
    if not filename.startswith(f"avatar_{user_id}"):
        abort(403)  # Prohibido

    # Ruta segura para servir el archivo
    avatar_path = os.path.join(auth_bp.root_path, 'static', 'avatars')
    return send_from_directory(avatar_path, filename)
