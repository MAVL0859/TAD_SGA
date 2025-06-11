from app.main import db, create_app
from app.infrastructure.models import User

app = create_app()
with app.app_context():
    username = 'admin@admin.com'  # Cambiado para coincidir con el usuario real
    password = '123'  # Puedes cambiar la contraseña aquí si lo deseas
    user = User.query.filter_by(username=username).first()
    if user:
        user.set_password(password)
        db.session.commit()
        print(f'Contraseña actualizada correctamente para el usuario {username}')
    else:
        print(f'El usuario {username} no existe')
