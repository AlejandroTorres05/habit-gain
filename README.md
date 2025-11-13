# MVP Flask con Bootstrap

Aplicación web MVP desarrollada con Flask, Jinja2 y Bootstrap siguiendo metodología de desarrollo incremental con historias de usuario.

### Test unitarios
``` pytest -v ```


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
cd mi-mvp-flask

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
cd mi-mvp-flask

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
cd mi-mvp-flask

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
cd mi-mvp-flask

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
mi-mvp-flask/
├── venv/                  # Entorno virtual (no se sube a git)
├── app.py                 # Archivo principal de la aplicación
├── requirements.txt       # Dependencias del proyecto
├── .gitignore            # Archivos ignorados por git
├── templates/            # Plantillas HTML (Jinja2)
├── static/               # Archivos estáticos
│   ├── css/             # Hojas de estilo
│   ├── js/              # Scripts JavaScript
│   └── img/             # Imágenes
```

## Ejecutar la Aplicación

### Linux/macOS

```bash
# Activar entorno virtual (si no está activado)
source venv/bin/activate

# Ejecutar la aplicación
python3 app.py
```

### Windows

```powershell
# Activar entorno virtual (si no está activado)
.\venv\Scripts\Activate.ps1

# Ejecutar la aplicación
python app.py
```

La aplicación estará disponible en: `http://localhost:5000`

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

---

## Panel de Administración

### Configurar Usuario Administrador

Después de instalar el proyecto, ejecuta el script de configuración:

```bash
# Activar entorno virtual (si no está activado)
source venv/bin/activate  # Linux/macOS
# o
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Ejecutar script de configuración
python3 setup_admin.py
```

Este script:
1. Ejecuta las migraciones necesarias
2. Actualiza el usuario demo a administrador O crea un nuevo admin
3. Muestra las credenciales de acceso

### Credenciales por Defecto

**Si tienes el usuario demo:**
- Email: `demo@habitgain.local`
- Password: `demo123`

**Si se crea nuevo admin:**
- Email: `admin@habitgain.com`
- Password: `admin123`

### Acceder al Panel

1. Inicia sesión con las credenciales de administrador
2. Accede a: `http://localhost:5000/admin`

### Funcionalidades del Panel Admin

- **Dashboard**: Estadísticas del sistema (usuarios, hábitos, etc.)
- **Gestión de Usuarios**: Crear, editar, eliminar usuarios y asignar roles
- **Gestión de Hábitos**: Ver, editar y eliminar hábitos de cualquier usuario
- Todas las acciones requieren confirmación antes de eliminar
- Validaciones completas en todos los formularios

