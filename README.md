# HabitGain - MVP Flask con Bootstrap

Aplicación web MVP para el seguimiento de hábitos desarrollada con Flask, Jinja2 y Bootstrap siguiendo metodología de desarrollo incremental con historias de usuario.

## Requisitos Previos

### Todos los Sistemas Operativos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Verificar instalación de Python

```bash
python3 --version  # Linux/macOS
python --version   # Windows
```

### Verificar instalación de pip

```bash
pip3 --version     # Linux/macOS
pip --version      # Windows
```

## Configuración del Proyecto

### Linux (Ubuntu/Debian)

```bash
# 1. Clonar el repositorio
git clone https://github.com/AlejandroTorres05/habit-gain.git
cd habit-gain

# 2. Crear un entorno virtual
python3 -m venv venv

# 3. Activar el entorno virtual
source venv/bin/activate

# 4. Actualizar pip
pip install --upgrade pip

# 5. Instalar dependencias
pip install -r requirements.txt
```

### macOS

```bash
# 1. Clonar el repositorio
git clone https://github.com/AlejandroTorres05/habit-gain.git
cd habit-gain

# 2. Crear un entorno virtual
python3 -m venv venv

# 3. Activar el entorno virtual
source venv/bin/activate

# 4. Actualizar pip
pip3 install --upgrade pip

# 5. Instalar dependencias
pip3 install -r requirements.txt
```

### Windows (PowerShell)

```powershell
# 1. Clonar el repositorio
git clone https://github.com/AlejandroTorres05/habit-gain.git
cd habit-gain

# 2. Crear un entorno virtual
python -m venv venv

# 3. Activar el entorno virtual
.\venv\Scripts\Activate.ps1

o 

.\venv\bin\Activate.ps1

# 4. Si hay error de permisos, ejecutar primero:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 5. Actualizar pip
python -m pip install --upgrade pip

# 6. Instalar dependencias
pip install -r requirements.txt
```

### Windows (CMD)

```cmd
# 1. Clonar el repositorio
git clone https://github.com/AlejandroTorres05/habit-gain.git
cd habit-gain

# 2. Crear un entorno virtual
python -m venv venv

# 3. Activar el entorno virtual
venv\Scripts\activate.bat

# 4. Actualizar pip
python -m pip install --upgrade pip

# 5. Instalar dependencias
pip install -r requirements.txt
```

## Estructura del Proyecto

```
habit-gain/
├── venv/                  # Entorno virtual (no se sube a git)
├── run.py                 # Archivo principal de la aplicación
├── requirements.txt       # Dependencias del proyecto
├── habitgain.db          # Base de datos SQLite
├── .gitignore            # Archivos ignorados por git
└── habitgain/            # Paquete principal de la aplicación
    ├── __init__.py       # Factory de la aplicación Flask
    ├── models.py         # Modelos de base de datos
    ├── static/           # Archivos estáticos
    │   ├── css/         # Hojas de estilo
    │   └── js/          # Scripts JavaScript
    ├── templates/        # Plantillas HTML compartidas
    └── [blueprints]/     # Módulos: auth, core, explore, habits, etc.
```

## Inicializar la Base de Datos

```bash
# Activar entorno virtual (si no está activado)
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\Activate.ps1  # Windows

# Inicializar la base de datos y datos semilla
python -c "from habitgain.models import Database; db = Database(); db.init_db(); db.seed_data()"
```

## Ejecutar la Aplicación

### Linux/macOS

```bash
# Activar entorno virtual (si no está activado)
source venv/bin/activate

# Ejecutar la aplicación
python run.py
```

### Windows

```powershell
# Activar entorno virtual (si no está activado)
.\venv\Scripts\Activate.ps1

# Ejecutar la aplicación
python run.py
```

La aplicación estará disponible en: `http://localhost:9001`

### Posibles Problemas

**Si necesitas cambiar el puerto:**
```bash
# El proyecto está configurado para usar el puerto 9001
# Si necesitas usar otro puerto, puedes ejecutar:
python -c "from habitgain import create_app; app = create_app(); app.run(debug=True, port=5000)"
# Luego acceder a: http://localhost:5000
```

## Credenciales de Prueba

### Usuario Demo (Pre-creado)
- **Email:** `demo@habit.com`
- **Contraseña:** `123456`

### Crear Nueva Cuenta
1. Ve a `http://localhost:9001/auth/register`
2. Completa el formulario de registro
3. Usa las credenciales creadas para iniciar sesión

## Funcionalidades Disponibles

- ✅ **Autenticación de usuarios** (login/logout)
- ✅ **Registro de usuarios** con validación
- ✅ **Exploración de hábitos** por categorías
- ✅ **Creación de hábitos** personalizados
- ✅ **Panel de progreso** personal
- ✅ **Sistema de categorías** (Health, Productivity, Learning)
- ✅ **Base de datos SQLite** con migraciones automáticas
- ✅ **Interfaz responsive** con diseño glassmorphism

## Desactivar el Entorno Virtual

### Linux/macOS/Windows

```bash
deactivate
```

## Dependencias Actuales

- Flask: Framework web minimalista
- Jinja2: Motor de plantillas (incluido con Flask)
- Bootstrap: Framework CSS responsive (CDN)

## Metodología de Desarrollo

### Marco de Trabajo: SCRUM

Este proyecto sigue el marco de trabajo ágil **SCRUM**, organizando el desarrollo en sprints iterativos e incrementales mediante historias de usuario.

### Estrategia de Branching: Git Flow

El proyecto utiliza **Git Flow** como estrategia de ramificación:

#### Ramas Principales

- **main**: Código en producción, siempre estable
- **develop**: Rama de integración para el desarrollo

#### Ramas de Soporte

- **feature/**: Nuevas funcionalidades
  - Nomenclatura: `feature/nombre-funcionalidad`
  - Se crean desde: `develop`
  - Se fusionan en: `develop`
- **hotfix/**: Correcciones urgentes en producción
  - Nomenclatura: `hotfix/descripcion`
  - Se crean desde: `main`
  - Se fusionan en: `main` y `develop`

#### Convenciones de Commits

Se recomienda usar commits descriptivos siguiendo este formato:

```
tipo(alcance): descripción breve

[cuerpo opcional]

```

**Tipos de commit:**

- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Cambios de formato (no afectan el código)
- `refactor`: Refactorización de código
- `test`: Agregar o modificar tests
- `chore`: Tareas de mantenimiento

**Ejemplo:**

```bash
git commit -m "feat: add the login screen"
```

## Notas de Desarrollo

Este proyecto se desarrolla de manera incremental siguiendo historias de usuario en sprints SCRUM. El README se actualizará conforme se agreguen nuevas funcionalidades.
