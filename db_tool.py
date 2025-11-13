#!/usr/bin/env python3
"""
Herramienta CLI para manipular la base de datos
Uso: python3 db_tool.py [comando]

Comandos:
  list-users              - Lista todos los usuarios
  create-user             - Crea un nuevo usuario (interactivo)
  test-login [email]      - Prueba login con un email
  raw-query [sql]         - Ejecuta una consulta SQL directa
  reset-password [email]  - Resetear contraseña de un usuario
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from habitgain.models import Database, User

def list_users():
    """Lista todos los usuarios"""
    print("=== Usuarios en el Sistema ===\n")
    users = User.list_all()
    if not users:
        print("No hay usuarios en el sistema")
        return

    for u in users:
        role = u.get('role') or 'user'
        marker = " [ADMIN]" if role == 'admin' else ""
        print(f"ID: {u['id']}")
        print(f"Email: {u['email']}")
        print(f"Nombre: {u['name']}")
        print(f"Rol: {role}{marker}")
        print("-" * 40)

def create_user_interactive():
    """Crea un usuario de forma interactiva"""
    print("=== Crear Nuevo Usuario ===\n")
    email = input("Email: ").strip().lower()
    name = input("Nombre: ").strip()
    password = input("Contraseña: ").strip()
    role = input("Rol (user/admin) [user]: ").strip() or "user"

    if role not in ['user', 'admin']:
        print("❌ Rol inválido. Usa 'user' o 'admin'")
        return

    try:
        user_id = User.create_user(email, name, password, role)
        print(f"\n✓ Usuario creado exitosamente con ID: {user_id}")
        print(f"  Email: {email}")
        print(f"  Nombre: {name}")
        print(f"  Rol: {role}")
    except Exception as e:
        print(f"\n❌ Error al crear usuario: {e}")

def test_login(email=None):
    """Prueba credenciales de login"""
    if not email:
        email = input("Email: ").strip().lower()

    password = input("Contraseña: ").strip()

    user = User.verify_password(email, password)
    if user:
        print(f"\n✓ Login exitoso!")
        print(f"  Email: {user['email']}")
        print(f"  Nombre: {user['name']}")
        print(f"  Rol: {user.get('role')}")
    else:
        print(f"\n❌ Login fallido - credenciales incorrectas")

def reset_password(email=None):
    """Resetea la contraseña de un usuario"""
    if not email:
        email = input("Email del usuario: ").strip().lower()

    user = User.get_by_email(email)
    if not user:
        print(f"❌ No existe usuario con email: {email}")
        return

    new_password = input("Nueva contraseña: ").strip()

    try:
        User.update_password(email, new_password)
        print(f"✓ Contraseña actualizada para {email}")
    except Exception as e:
        print(f"❌ Error al actualizar contraseña: {e}")

def raw_query(sql=None):
    """Ejecuta una consulta SQL directa"""
    if not sql:
        print("Ingresa tu consulta SQL (termina con ; y presiona Enter):")
        lines = []
        while True:
            line = input()
            lines.append(line)
            if line.strip().endswith(';'):
                break
        sql = ' '.join(lines)

    db = Database()
    conn = db.get_connection()
    cur = conn.cursor()

    try:
        cur.execute(sql)

        # Si es SELECT, mostrar resultados
        if sql.strip().upper().startswith('SELECT'):
            rows = cur.fetchall()
            if rows:
                # Mostrar nombres de columnas
                cols = [description[0] for description in cur.description]
                print("\n" + " | ".join(cols))
                print("-" * 80)

                # Mostrar filas
                for row in rows:
                    print(" | ".join(str(v) for v in row))
            else:
                print("No hay resultados")
        else:
            # Para INSERT, UPDATE, DELETE
            conn.commit()
            print(f"✓ Consulta ejecutada. Filas afectadas: {cur.rowcount}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def show_help():
    """Muestra ayuda"""
    print(__doc__)

def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1]

    if command == "list-users":
        list_users()
    elif command == "create-user":
        create_user_interactive()
    elif command == "test-login":
        email = sys.argv[2] if len(sys.argv) > 2 else None
        test_login(email)
    elif command == "reset-password":
        email = sys.argv[2] if len(sys.argv) > 2 else None
        reset_password(email)
    elif command == "raw-query":
        sql = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        raw_query(sql)
    elif command in ["help", "-h", "--help"]:
        show_help()
    else:
        print(f"❌ Comando desconocido: {command}")
        print("\nUsa 'python3 db_tool.py help' para ver comandos disponibles")

if __name__ == "__main__":
    main()
