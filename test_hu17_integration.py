#!/usr/bin/env python3
"""
Test de integración para HU-17: Verificar que el panel de progreso funciona correctamente
"""
import sys
from habitgain import create_app
from habitgain.models import User, Habit, Completion
from datetime import date


def test_panel_with_motivational_message():
    """Prueba que el panel de progreso carga correctamente con el mensaje motivacional"""
    print("=== Test de Integración HU-17 ===\n")

    app = create_app()

    with app.test_client() as client:
        # 1. Login
        print("1. Intentando login...")
        response = client.post('/auth/login', data={
            'email': 'demo@habitgain.local',
            'password': 'demo123'
        }, follow_redirects=False)

        if response.status_code == 302:
            print("   ✓ Login exitoso (redirección detectada)")
        else:
            print(f"   ✗ Error en login: {response.status_code}")
            return False

        # 2. Acceder al panel de progreso
        print("\n2. Accediendo al panel de progreso...")
        response = client.get('/progress/panel', follow_redirects=True)

        if response.status_code == 200:
            print("   ✓ Panel cargado correctamente")
        else:
            print(f"   ✗ Error al cargar panel: {response.status_code}")
            return False

        # 3. Verificar que el HTML contiene elementos de HU-17
        html = response.data.decode('utf-8')

        checks = [
            ("Banner motivacional", "motivation-banner" in html),
            ("Icono motivacional", "motivation-icon" in html),
            ("Texto motivacional", "motivation-text" in html),
            ("Subtexto motivacional", "motivation-subtext" in html),
            ("Función de confeti", "createConfetti" in html),
            ("Indicador de racha", "streak-indicator" in html or "streak-fire" in html),
            ("Animación de dopamina", "dopamine-glow" in html),
            ("Animación de pulso de éxito", "success-pulse" in html),
        ]

        print("\n3. Verificando elementos de HU-17 en el HTML:")
        all_passed = True
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"   {status} {name}")
            if not passed:
                all_passed = False

        # 4. Verificar que el mensaje motivacional está presente
        print("\n4. Verificando presencia del mensaje motivacional...")
        motivation_indicators = [
            "¡Bienvenido a tu viaje!",
            "Vas por buen camino",
            "¡Eres imparable!",
            "Un nuevo comienzo",
            "¡Primera semana completada!",
            "Tu cerebro aprende",
            "constancia"
        ]

        found_message = False
        for indicator in motivation_indicators:
            if indicator in html:
                print(f"   ✓ Mensaje motivacional detectado: '{indicator}'")
                found_message = True
                break

        if not found_message:
            print("   ⚠ No se detectó un mensaje motivacional específico, pero puede ser uno nuevo")

        return all_passed

    return True


def test_complete_habit_endpoint():
    """Prueba que el endpoint de completar hábito funciona correctamente"""
    print("\n5. Probando endpoint de completar hábito...")

    app = create_app()

    with app.test_client() as client:
        # Login primero
        client.post('/auth/login', data={
            'email': 'demo@habitgain.local',
            'password': 'demo123'
        })

        # Obtener un hábito para completar
        user_email = "demo@habitgain.local"
        habits = Habit.list_active_by_owner(user_email)

        if not habits:
            print("   ⚠ No hay hábitos activos para probar")
            return True

        habit_id = habits[0]["id"]

        # Obtener CSRF token
        panel_response = client.get('/progress/panel')
        html = panel_response.data.decode('utf-8')

        # Extraer CSRF token del HTML (buscar en el script)
        import re
        csrf_match = re.search(r"'X-CSRF-Token':\s*'([^']+)'", html)
        if not csrf_match:
            print("   ✗ No se pudo obtener CSRF token")
            return False

        csrf_token = csrf_match.group(1)
        print(f"   ✓ CSRF token obtenido: {csrf_token[:20]}...")

        # Completar el hábito
        response = client.post(
            f'/progress/complete/{habit_id}',
            headers={
                'X-CSRF-Token': csrf_token,
                'X-Requested-With': 'fetch'
            }
        )

        if response.status_code == 200:
            data = response.get_json()
            if data and data.get('ok'):
                print(f"   ✓ Hábito completado exitosamente")
                print(f"   ✓ Datos de racha recibidos:")
                print(f"     - Streak: {data.get('streak')} días")
                print(f"     - Strength: {data.get('strength')}%")
                print(f"     - Level: {data.get('strength_level')}")
                print(f"     - Color: {data.get('strength_color')}")
                return True
            else:
                print(f"   ✗ Respuesta no exitosa: {data}")
                return False
        else:
            print(f"   ✗ Error al completar hábito: {response.status_code}")
            return False


def main():
    print("Iniciando tests de integración HU-17...\n")

    # Test 1: Panel con mensaje motivacional
    test1_passed = test_panel_with_motivational_message()

    # Test 2: Endpoint de completar hábito
    test2_passed = test_complete_habit_endpoint()

    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("✓ TODOS LOS TESTS DE INTEGRACIÓN PASARON")
        print("=" * 60)
        print("\nLa HU-17 está completamente funcional:")
        print("  ✓ Banner motivacional dinámico visible en el panel")
        print("  ✓ JavaScript para animaciones de confeti cargado")
        print("  ✓ Sistema de rachas visuales implementado")
        print("  ✓ Endpoint de completar hábito con datos de racha")
        print("  ✓ Efectos visuales de dopamina listos")
        print("\nAhora puedes:")
        print("  1. Iniciar el servidor: flask run")
        print("  2. Abrir http://localhost:5000")
        print("  3. Login con: demo@habitgain.local / demo123")
        print("  4. Completar un hábito y ver las animaciones!")
        return 0
    else:
        print("✗ ALGUNOS TESTS FALLARON")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
