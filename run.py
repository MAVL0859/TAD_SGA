#!/usr/bin/env python3
"""
Archivo principal para ejecutar la aplicación Flask del SGA UTM
"""

from app.main import create_app

# Crear la aplicación Flask
app = create_app()

if __name__ == '__main__':
    print("🚀 Iniciando SGA UTM...")
    print("📊 Dashboard disponible en: http://localhost:5000")
    print("👤 Login: http://localhost:5000/login")
    print("🔧 Admin: http://localhost:5000/admin")
    
    # Ejecutar en modo debug
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )
