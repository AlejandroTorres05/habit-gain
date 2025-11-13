#!/usr/bin/env python3
"""
Test de creación concurrente de hábitos para verificar que no hay locks de BD
"""
import threading
import time
from habitgain.models import Database, User, Habit, Category

def create_habit_worker(thread_id, user_email, results):
    """Worker thread que crea un hábito"""
    try:
        habit_name = f"Hábito Concurrente #{thread_id}"
        habit_id = Habit.create(
            email=user_email,
            name=habit_name,
            short_desc=f"Descripción del hábito {thread_id}",
            category_id=1,
            frequency="daily"
        )
        results[thread_id] = {"success": True, "id": habit_id, "name": habit_name}
        print(f"  ✓ Thread {thread_id}: Hábito creado (ID: {habit_id})")
    except Exception as e:
        results[thread_id] = {"success": False, "error": str(e)}
        print(f"  ✗ Thread {thread_id}: ERROR - {str(e)}")

def main():
    print("=== Test de Creación Concurrente de Hábitos ===\n")

    # Configurar
    user_email = "demo@habitgain.local"
    num_threads = 10

    print(f"1. Usuario de prueba: {user_email}")
    print(f"2. Threads concurrentes: {num_threads}\n")

    # Crear threads
    threads = []
    results = {}

    print("3. Iniciando creación concurrente...")
    start_time = time.time()

    for i in range(num_threads):
        thread = threading.Thread(target=create_habit_worker, args=(i, user_email, results))
        threads.append(thread)
        thread.start()

    # Esperar a que terminen
    for thread in threads:
        thread.join()

    end_time = time.time()
    elapsed = end_time - start_time

    # Analizar resultados
    print(f"\n4. Resultados:")
    successful = sum(1 for r in results.values() if r.get("success"))
    failed = len(results) - successful

    print(f"   Exitosos: {successful}/{num_threads}")
    print(f"   Fallidos: {failed}/{num_threads}")
    print(f"   Tiempo total: {elapsed:.2f} segundos")
    print(f"   Promedio: {elapsed/num_threads:.2f} seg/hábito")

    if failed > 0:
        print("\n5. Errores detectados:")
        for tid, result in results.items():
            if not result.get("success"):
                print(f"   Thread {tid}: {result.get('error')}")
        return 1
    else:
        print("\n✓ TODAS LAS OPERACIONES EXITOSAS - No hay locks de BD!")
        return 0

if __name__ == "__main__":
    exit(main())
