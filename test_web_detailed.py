#!/usr/bin/env python3
"""Script detallado para debuggear creación de hábitos"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from habitgain import create_app

def test_habit_creation_detailed():
    print("=== Test Detallado Creación de Hábitos ===\n")

    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        with client.session_transaction() as sess:
            # Establecer sesión manualmente
            sess['user'] = {
                'email': 'demo@habitgain.local',
                'name': 'Usuario Demo'
            }

        print("1. Sesión establecida manualmente")
        print(f"   User: demo@habitgain.local\n")

        # Test GET primero
        print("2. Probando GET /habits/new...")
        response = client.get('/habits/new')
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   ❌ GET falló")
            return
        print(f"   ✓ GET funciona\n")

        # Test POST con datos completos
        print("3. Probando POST /habits/new con datos completos...")
        post_data = {
            'nombre': 'Test Web Habit',
            'descripcion': 'Descripción completa del hábito',
            'categoria': 'Health',
            'frecuencia': 'diaria',
            'icon': '💪',
            'habit_base_id': ''  # Sin habit stacking
        }

        print(f"   Datos enviados: {post_data}")

        response = client.post('/habits/new', data=post_data, follow_redirects=False)

        print(f"\n   Status: {response.status_code}")

        if response.status_code == 302:
            print(f"   ✓ Redirige a: {response.location}")
        elif response.status_code == 200:
            print(f"   ⚠ No redirige (200)")

            # Buscar mensajes flash en el HTML
            html = response.data.decode()

            # Buscar alerts
            import re
            # Buscar mensajes con class="alert"
            alerts = re.findall(r'<div[^>]*class="[^"]*alert[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)

            if alerts:
                print("\n   Mensajes encontrados en el HTML:")
                for alert in alerts[:5]:
                    clean_alert = re.sub(r'<[^>]+>', '', alert).strip()
                    if clean_alert and len(clean_alert) > 5:
                        print(f"   - {clean_alert[:150]}")

            # Buscar flash messages específicamente
            flash_pattern = r'flash\([\'"]([^\'"]+)[\'"],\s*[\'"](\w+)[\'"]'
            if 'flash' in html:
                print("\n   Hay referencias a 'flash' en el HTML")

            # Verificar si el form se renderizó de nuevo
            if '<form' in html and 'habitForm' in html:
                print("\n   ⚠ El formulario se volvió a renderizar (no se creó el hábito)")
            else:
                print("\n   El formulario NO se renderizó")

        else:
            print(f"   ❌ Status inesperado: {response.status_code}")

        # Verificar en BD si se creó
        print("\n4. Verificando en base de datos...")
        from habitgain.models import Habit
        habits = Habit.list_active_by_owner('demo@habitgain.local')
        test_habit = [h for h in habits if h['name'] == 'Test Web Habit']

        if test_habit:
            print(f"   ✓ Hábito encontrado en BD: ID {test_habit[0]['id']}")
        else:
            print(f"   ❌ Hábito NO encontrado en BD")
            print(f"   Total de hábitos del usuario: {len(habits)}")

if __name__ == "__main__":
    test_habit_creation_detailed()
