#!/usr/bin/env python3
"""Script para probar el flujo web completo"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from habitgain import create_app
from flask import session

def test_web_flow():
    print("=== Test Flujo Web ===\n")

    app = create_app()

    with app.test_client() as client:
        # 1. Test login
        print("1. Probando login...")
        response = client.post('/auth/login', data={
            'email': 'demo@habitgain.local',
            'password': 'demo123'
        }, follow_redirects=False)

        print(f"   Status: {response.status_code}")
        print(f"   Location: {response.location}")

        if response.status_code in [302, 303]:
            print("   ✓ Login redirige correctamente")
        else:
            print("   ❌ Login no redirige")
            print(f"   Response: {response.data.decode()[:200]}")
            return

        # 2. Test crear hábito
        print("\n2. Probando crear hábito...")
        response = client.post('/habits/new', data={
            'nombre': 'Test Web Habit',
            'descripcion': 'Descripción de prueba',
            'categoria': 'Health',
            'frecuencia': 'diaria',
            'icon': ''
        }, follow_redirects=False)

        print(f"   Status: {response.status_code}")
        print(f"   Location: {response.location if hasattr(response, 'location') else 'N/A'}")

        if response.status_code in [302, 303]:
            print("   ✓ Creación redirige correctamente")
        elif response.status_code == 200:
            print("   ⚠ Devuelve 200 (no redirige)")
            # Buscar mensajes de error en el HTML
            html = response.data.decode()
            if 'danger' in html or 'error' in html.lower():
                print("   Posibles errores en el HTML:")
                # Extraer mensajes flash si existen
                import re
                alerts = re.findall(r'<div[^>]*alert[^>]*>(.*?)</div>', html, re.DOTALL)
                for alert in alerts[:3]:
                    print(f"   - {alert[:100]}")
        else:
            print(f"   ❌ Status inesperado: {response.status_code}")
            print(f"   Response: {response.data.decode()[:500]}")

if __name__ == "__main__":
    test_web_flow()
