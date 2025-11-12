# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Setup & Environment
```bash
# Setup virtual environment (first time)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# .\\venv\\Scripts\\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Initialize/reset database
python -c "from habitgain.models import Database; db = Database(); db.init_db(); db.seed_data()"
```

### Running the Application
```bash
# Development server with debug mode
python run.py

# Alternative method
python -m flask --app run run --debug

# The application will be available at http://localhost:5000
```

### Database Operations
```bash
# Check database contents (SQLite)
sqlite3 habitgain.db ".tables"
sqlite3 habitgain.db "SELECT * FROM users;"
sqlite3 habitgain.db "SELECT * FROM categories;"
sqlite3 habitgain.db "SELECT * FROM habits;"

# Reset database completely
rm habitgain.db
python -c "from habitgain.models import Database; db = Database(); db.init_db(); db.seed_data()"
```

### Testing Access
```bash
# Demo credentials for testing
# Email: demo@habit.com
# Password: 123456 (hardcoded in habitgain/auth/__init__.py)
```

## Architecture Overview

### Application Structure
This is a Flask web application following a modular blueprint architecture for an MVP habit tracking system. The app uses the factory pattern with `create_app()` and is organized around user stories for SCRUM development.

### Key Components

**Core Application (`habitgain/__init__.py`)**
- Flask application factory with blueprint registration
- Database initialization and seeding on startup
- Template context processors for navigation URLs
- Development secret key (needs changing for production)

**Database Layer (`habitgain/models.py`)**
- SQLite database with automatic schema migrations
- PBKDF2 password hashing with salt for security
- Three main models: User, Category, Habit
- Safe schema evolution system that handles missing columns
- Environment-configurable database name via `HABITGAIN_DB`

**Blueprint Architecture**
- `core/`: Homepage, error handlers (404), base layouts
- `auth/`: Login/logout, user registration (stub)
- `explore/`: Browse habits by category, search functionality
- `habits/`: Create new habits, mark as complete
- `progress/`: User dashboard/panel showing progress
- `profile/`: User profile editing (stub for future development)
- `manage/`: Habit deletion/archiving (stub for future development)

### Database Schema
```sql
-- Core tables with migration-safe design
users: id, email (unique), name, password_hash, password_salt
categories: id, name (unique), icon
habits: id, owner_email, name, active, short_desc, category_id
```

### Authentication System
- Session-based authentication using Flask sessions
- PBKDF2 with 200,000 iterations for password hashing
- User migration system handles legacy password formats
- Demo user hardcoded for MVP testing

### Frontend Technology Stack
- Bootstrap 5.3.3 with dark theme
- Custom glassmorphism CSS design system
- Jinja2 templating with shared base template
- Responsive design with mobile-first approach

## Development Methodology

### SCRUM & Git Flow
The project follows SCRUM methodology with Git Flow branching:
- `main`: Production-ready code
- `develop`: Integration branch for development
- `feature/*`: New functionality branches
- `hotfix/*`: Emergency production fixes

### Commit Conventions
- `feat`: New functionality
- `fix`: Bug corrections
- `docs`: Documentation changes
- `style`: Formatting changes
- `refactor`: Code refactoring
- `test`: Test additions/modifications
- `chore`: Maintenance tasks

## Common Development Patterns

### Adding New Features
1. Create feature branch from `develop`
2. Add new blueprint in `habitgain/new_feature/`
3. Register blueprint in `habitgain/__init__.py`
4. Add URL prefix in blueprint registration
5. Create templates in `new_feature/templates/`

### Database Migrations
The app uses a custom migration system in `models.py`:
- Use `_ensure_column()` to add new columns safely
- Use `_maybe_create_index()` for performance indexes
- Migration functions run automatically on app startup

### Adding New Routes
```python
# In blueprint __init__.py
@blueprint_name.route("/new-route")
def new_function():
    if not _require_login():  # For protected routes
        return redirect(url_for("auth.login"))
    # Route logic here
```

### Template Inheritance
- Extend `base.html` for consistent layout
- Use `{% block content %}` for main content
- Flash messages are handled automatically in base template

## Environment Configuration

### Environment Variables
- `HABITGAIN_DB`: Database filename (defaults to "habitgain.db")
- `FLASK_ENV`: Set to "development" for debug mode

### Production Considerations
- Change `SECRET_KEY` from "dev-secret"
- Remove hardcoded demo user credentials
- Implement proper user registration
- Add proper error handling and logging
- Consider database connection pooling for SQLite

## File Structure Understanding

```
habitgain/
├── __init__.py           # App factory and blueprint registration
├── models.py            # Database models and migration system
├── static/              # CSS, JS, images
│   ├── css/styles.css   # Custom glassmorphism theme
│   └── js/              # Frontend JavaScript
├── templates/           # Shared templates (base.html)
└── [blueprint]/         # Each feature as separate blueprint
    ├── __init__.py      # Blueprint routes and logic
    └── templates/       # Blueprint-specific templates
```

The application is designed for incremental development following user stories, with stubs in place for future features (profile editing, habit management).