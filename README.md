# 🎓 SGA UTM - Sistema de Gestión Académica

Sistema web de gestión académica desarrollado con Flask y PostgreSQL, implementando Clean Architecture para la Universidad Técnica de Manabí.

## 🚀 Características

- **Dashboard diferenciado** por roles (Admin, Profesor, Estudiante)
- **Gestión de cursos** y asignaciones académicas
- **Sistema de inscripciones** automatizado
- **Modal de estudiantes** con información detallada
- **Autenticación segura** con sesiones
- **Arquitectura limpia** y escalable
- **UI moderna** y responsive

## 🛠️ Tecnologías

- **Backend:** Python Flask
- **Base de datos:** PostgreSQL
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap
- **Autenticación:** Flask-JWT-Extended
- **ORM:** SQLAlchemy

## 📦 Instalación

### Requisitos Previos
- Python 3.8+
- PostgreSQL 12+
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/MAVL0859/TAD_SGA
cd TAD_SGA
```

2. **Crear entorno virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
Crear archivo `.env` con:
```bash
DATABASE_URL=postgresql://usuario:password@host:puerto/nombre_db
SECRET_KEY=tu_clave_secreta_aqui
```

5. **Inicializar base de datos**
```bash
python -c "from app.main import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

## 🏃‍♂️ Uso

### Iniciar el servidor
```bash
python run.py
```

La aplicación estará disponible en: `http://localhost:5000`

### Credenciales por defecto
Consultar el archivo `credenciales.txt` para las credenciales de acceso inicial.

## 📁 Estructura del Proyecto

```
TAD_SGA/
├── app/
│   ├── infrastructure/     # Configuración, modelos y acceso a datos
│   ├── interface/         # Controladores, rutas y vistas
│   ├── static/           # Archivos estáticos (CSS, JS, imágenes)
│   └── templates/        # Plantillas HTML
├── db/                   # Scripts de base de datos
├── img/                  # Imágenes del proyecto
├── .env                  # Variables de entorno
├── run.py               # Punto de entrada principal
├── requirements.txt     # Dependencias del proyecto
└── README.md           # Documentación
```

## 👥 Roles del Sistema

### 🔧 Administrador
- Gestión completa de usuarios y roles
- Administración de cursos y asignaciones
- Supervisión general del sistema
- Acceso a reportes y estadísticas

### 👨‍🏫 Profesor
- Gestión de cursos asignados
- Visualización de estudiantes inscritos
- Registro de calificaciones y asistencia
- Dashboard con métricas académicas

### 👨‍🎓 Estudiante
- Visualización de cursos inscritos
- Consulta de calificaciones y progreso
- Gestión de perfil personal
- Dashboard académico personalizado

## 🔒 Seguridad

- Autenticación basada en sesiones seguras
- Autorización estricta por roles
- Validación robusta de datos de entrada
- Protección contra inyección SQL
- Separación de responsabilidades

## 🌐 Características Técnicas

- **Clean Architecture**: Separación clara de capas
- **Responsive Design**: Compatible con dispositivos móviles
- **API RESTful**: Endpoints bien documentados
- **Modular**: Fácil mantenimiento y escalabilidad
- **Logging**: Sistema de registro de eventos

## 🚀 Despliegue

El sistema está preparado para despliegue en:
- Servidores locales
- Servicios cloud (Railway, Heroku, AWS)
- Contenedores Docker

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Crear un Pull Request

## 📋 Lista de Verificación Pre-Despliegue

- [ ] Configurar variables de entorno de producción
- [ ] Verificar conexión a base de datos
- [ ] Ejecutar tests de funcionalidad
- [ ] Configurar logs de producción
- [ ] Verificar seguridad de endpoints

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

**Desarrollado por Marlon Vera y Jean Pierre Chavez**
