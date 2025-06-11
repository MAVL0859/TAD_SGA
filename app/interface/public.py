from flask import Blueprint, render_template

public_bp = Blueprint('public', __name__)

@public_bp.route('/', methods=['GET'])
def home():
    return render_template('inicio.html')

# Ruta catch-all para mostrar inicio en cualquier ruta no encontrada
@public_bp.app_errorhandler(404)
def not_found(e):
    return render_template('inicio.html'), 200
