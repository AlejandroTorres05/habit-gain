#!/usr/bin/env python3
"""Script para probar creación de hábitos"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from habitgain.models import Database, User, Habit, Category

def test_habit_creation():
    print("=== Test Creación de Hábitos ===\n")

    # Verificar usuario
    test_email = "demo@habitgain.local"
    print(f"1. Verificando usuario: {test_email}")
    user = User.get_by_email(test_email)
    if not user:
        print(f"   ❌ Usuario no existe")
        return
    print(f"   ✓ Usuario existe: {user['name']}")
    print(f"   Rol: {user.get('role')}")
    print()

    # Verificar categorías
    print("2. Verificando categorías:")
    categories = Category.all()
    if not categories:
        print("   ❌ No hay categorías")
        return
    for cat in categories:
        print(f"   - {cat['name']} (ID: {cat['id']})")
    print()

    # Intentar crear un hábito
    print("3. Creando hábito de prueba...")
    try:
        habit_name = "Test Hábito de Prueba"
        habit_desc = "Este es un hábito de prueba"
        category_id = categories[0]['id']

        new_id = Habit.create(
            email=test_email,
            name=habit_name,
            short_desc=habit_desc,
            category_id=category_id,
            frequency="daily",
            habit_base_id=None,
            icon=None,
            frequency_detail=""
        )

        print(f"   ✓ Hábito creado exitosamente con ID: {new_id}")

        # Verificar que se creó
        created_habit = Habit.get_by_id(new_id)
        if created_habit:
            print(f"   ✓ Hábito verificado en BD:")
            print(f"     Nombre: {created_habit['name']}")
            print(f"     Owner: {created_habit['owner_email']}")
            print(f"     Activo: {created_habit.get('active')}")
        else:
            print(f"   ❌ No se puede recuperar el hábito creado")

    except Exception as e:
        print(f"   ❌ Error al crear hábito: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_habit_creation()
