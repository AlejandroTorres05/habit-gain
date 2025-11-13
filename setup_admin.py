#!/usr/bin/env python3
"""
Script para configurar el primer usuario administrador.
Uso: python3 setup_admin.py
"""

import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from habitgain.models import Database, User

def setup_admin():
    print("=== Configuración de Administrador ===\n")

    # Inicializar BD y ejecutar migraciones
    print("1. Ejecutando migraciones de base de datos...")
    db = Database()
    db.init_db()
    print("   ✓ Migraciones completadas\n")

    # Listar usuarios actuales
    print("2. Usuarios actuales en el sistema:")
    users = User.list_all()
    if not users:
        print("   No hay usuarios en el sistema\n")
    else:
        for u in users:
            role = u.get('role') or 'user'
            print(f"   - {u['email']} ({u['name']}) - Rol: {role}")
        print()

    # Actualizar o crear admin
    print("3. Configurando usuario administrador...")

    # Opción 1: Actualizar demo@habitgain.local si existe
    demo_user = User.get_by_email('demo@habitgain.local')
    if demo_user:
        print(f"   Actualizando demo@habitgain.local a rol 'admin'...")
        User.update_user(demo_user['id'], demo_user['email'], demo_user['name'], 'admin')
        print("   ✓ Usuario demo@habitgain.local actualizado a admin")
        print("\n   Credenciales de acceso:")
        print("   Email: demo@habitgain.local")
        print("   Password: demo123")
    else:
        # Opción 2: Crear nuevo admin
        print("   Creando nuevo usuario administrador...")
        try:
            User.create_user('admin@habitgain.com', 'Administrador', 'admin123', 'admin')
            print("   ✓ Usuario administrador creado exitosamente")
            print("\n   Credenciales de acceso:")
            print("   Email: admin@habitgain.com")
            print("   Password: admin123")
        except Exception as e:
            print(f"   ✗ Error al crear admin: {e}")
            return False

    print("\n4. Usuarios finales en el sistema:")
    users = User.list_all()
    for u in users:
        role = u.get('role') or 'user'
        admin_marker = " [ADMIN]" if role == 'admin' else ""
        print(f"   - {u['email']} ({u['name']}) - Rol: {role}{admin_marker}")

    print("\n=== Configuración completada ===")
    print("\nAccede al panel de administración en:")
    print("http://localhost:5000/admin")
    print("\nPrimero inicia sesión con las credenciales de administrador mostradas arriba.")

    return True

if __name__ == "__main__":
    try:
        success = setup_admin()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
