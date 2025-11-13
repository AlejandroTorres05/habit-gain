#!/usr/bin/env python3
"""Script para verificar y manipular la base de datos"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from habitgain.models import Database, User

def main():
    print("=== Verificación de Base de Datos ===\n")

    # Ver todos los usuarios
    print("1. Usuarios en el sistema:")
    users = User.list_all()
    for u in users:
        role = u.get('role') or 'user'
        print(f"   ID: {u['id']}")
        print(f"   Email: {u['email']}")
        print(f"   Nombre: {u['name']}")
        print(f"   Rol: {role}")
        print()

    # Probar login con cada usuario
    print("2. Probando credenciales:")

    # Test demo@habitgain.local
    test_users = [
        ('demo@habitgain.local', 'demo123'),
        ('demo@habit.com', '123456'),
    ]

    for email, password in test_users:
        user = User.verify_password(email, password)
        if user:
            print(f"   ✓ {email} con password '{password}' - OK")
            print(f"     Rol: {user.get('role')}")
        else:
            print(f"   ✗ {email} con password '{password}' - FALLO")
        print()

if __name__ == "__main__":
    main()
