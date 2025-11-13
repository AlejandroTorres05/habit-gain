# HU-18: Implementación de Onboarding Interactivo

## Resumen
Historia de Usuario completa que implementa un sistema de onboarding interactivo para nuevos usuarios con tour guiado paso a paso, wizard para crear el primer hábito, y analytics de completitud.

## Estado: ✅ COMPLETADA

---

## Criterios de Aceptación Implementados

### CDA 1: Tour guiado de 4-5 pasos con opción de saltar ✅

**Implementación:**
- **Tour de 5 pasos** que guía al usuario a través de las funciones principales:
  1. **Bienvenida**: Introducción al sistema
  2. **Tus Hábitos**: Explicación de la lista de hábitos y medidor de fortaleza
  3. **Completar Hábitos**: Cómo marcar hábitos como completados
  4. **Tu Progreso**: Visualización de estadísticas y rachas
  5. **Crear Hábitos**: Invitación a crear el primer hábito

- **Sistema de spotlight** que resalta elementos específicos del UI
- **Tooltips informativos** con iconos, títulos y descripciones
- **Botón de "Saltar tutorial"** disponible en cualquier momento
- **Indicador de progreso** con puntos que muestran el paso actual
- **Navegación**: Botones de "Anterior" y "Siguiente"

**Archivos implementados:**
- `habitgain/static/js/onboarding.js`: Clase `OnboardingTour` con lógica completa (líneas 1-591)
- `habitgain/static/css/styles.css`: Estilos para overlay, spotlight y tooltips (líneas 552-894)
- `habitgain/progress/templates/progress/panel.html`: Data attributes para elementos del tour

---

### CDA 2: Wizard para crear primer hábito ✅

**Implementación:**
- **Wizard modal** que aparece al finalizar el tour
- **Formulario simplificado** con 3 campos:
  - Nombre del hábito
  - Razón/motivación personal
  - Categoría (selección de 5 opciones predefinidas)
- **Creación automática** del hábito al enviar el formulario
- **Animación de confeti** al completar exitosamente
- **Opción de "Crear después"** para usuarios que prefieren explorar primero

**Código relevante:**
```javascript
// habitgain/static/js/onboarding.js (líneas 258-338)
async showWizard() {
    // Crear wizard con formulario
    this.wizard = document.createElement('div');
    this.wizard.className = 'onboarding-wizard';
    // ... renderizado del formulario
}

async createHabit() {
    // Envío del formulario vía fetch
    const response = await fetch('/habits/new', {
        method: 'POST',
        // ... datos del hábito
    });
    if (response.ok) {
        this.showConfetti();
        this.completeOnboarding();
    }
}
```

---

### CDA 3: Personalización inicial (nombre, preferencias) ✅

**Implementación:**
- **Tracking de estado** por usuario en base de datos
- **Registro del nombre** durante el signup (ya existente)
- **Campos de personalización** en el wizard del primer hábito:
  - Motivación personal (campo "¿Por qué es importante para ti?")
  - Selección de categoría de interés

**Tabla de base de datos:**
```sql
CREATE TABLE onboarding_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL UNIQUE,
    completed INTEGER NOT NULL DEFAULT 0,
    current_step INTEGER NOT NULL DEFAULT 0,
    skipped INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    steps_completed TEXT DEFAULT '',
    FOREIGN KEY (user_email) REFERENCES users(email)
);
```

---

### CDA 4: Analytics de completitud ✅

**Implementación:**
- **Endpoint `/onboarding/analytics`** que retorna estadísticas completas
- **Métricas calculadas**:
  - Total de usuarios registrados
  - Total de usuarios con estado de onboarding
  - Usuarios que completaron el onboarding
  - Usuarios que saltaron el onboarding
  - Usuarios con onboarding en progreso
  - Tasa de completitud (%)
  - Tasa de skip (%)
  - Promedio de pasos completados

**Ejemplo de respuesta:**
```json
{
  "total_users": 150,
  "total_onboarding": 145,
  "completed": 98,
  "skipped": 22,
  "in_progress": 25,
  "completion_rate": 67.59,
  "skip_rate": 15.17,
  "avg_steps_completed": 3.8
}
```

---

## Arquitectura de la Solución

### 1. Backend (Python/Flask)

#### Modelo OnboardingStatus (`habitgain/models.py`, líneas 1075-1307)
```python
class OnboardingStatus:
    # Métodos principales:
    - get_status(user_email) → Dict | None
    - needs_onboarding(user_email) → bool
    - create_status(user_email) → None
    - mark_step_complete(user_email, step_number) → None
    - mark_skipped(user_email) → None
    - reset_status(user_email) → None
    - get_analytics() → Dict
```

#### Blueprint Onboarding (`habitgain/onboarding/__init__.py`)
**Endpoints:**
- `POST /onboarding/step` - Marca un paso como completado
- `POST /onboarding/skip` - Marca el onboarding como saltado
- `POST /onboarding/reset` - Reinicia el onboarding (para re-ver tutorial)
- `GET /onboarding/status` - Obtiene estado actual del usuario
- `GET /onboarding/analytics` - Obtiene estadísticas globales

#### Integración con Auth (`habitgain/auth/__init__.py`, línea 89)
```python
# Al registrar nuevo usuario:
User.create_user(email, name, password, role="user")
OnboardingStatus.create_status(email)  # ← Auto-create
```

#### Integración con Progress (`habitgain/progress/__init__.py`, líneas 106-127)
```python
# En el panel de progreso:
needs_onboarding = OnboardingStatus.needs_onboarding(user)
return render_template('progress/panel.html',
                      needs_onboarding=needs_onboarding,
                      # ... otros parámetros
)
```

---

### 2. Frontend (JavaScript)

#### Clase OnboardingTour (`habitgain/static/js/onboarding.js`)

**Estructura:**
```javascript
class OnboardingTour {
    constructor() {
        this.currentStep = 0;
        this.totalSteps = 5;
        this.steps = [...]; // Definición de pasos
    }

    // Métodos principales:
    start()                    // Inicia el tour
    showStep(stepIndex)        // Muestra paso específico
    nextStep()                 // Avanza al siguiente
    previousStep()             // Retrocede
    showWizard()               // Muestra wizard de primer hábito
    createHabit()              // Crea hábito desde wizard
    skip()                     // Salta el tour
    markStepComplete(stepNumber) // API call para tracking
    cleanup()                  // Limpia elementos del DOM
}
```

**Auto-inicialización:**
```javascript
function initOnboarding() {
    const needsOnboarding = document.body.dataset.needsOnboarding === 'true';
    if (needsOnboarding) {
        onboardingTour = new OnboardingTour();
        setTimeout(() => onboardingTour.start(), 500);
    }
}
initOnboarding();
```

---

### 3. Estilos CSS (`habitgain/static/css/styles.css`, líneas 552-894)

**Componentes estilizados:**

1. **Overlay oscuro** (`.onboarding-overlay`)
   - Fondo semitransparente que oscurece la página
   - z-index: 9998

2. **Spotlight** (`.onboarding-spotlight`)
   - Borde que resalta el elemento objetivo
   - Box-shadow con "recorte" visual usando 9999px
   - Animación de pulso suave
   - z-index: 9999

3. **Tooltip** (`.onboarding-tooltip`)
   - Tarjeta glassmorphism con información
   - Posicionamiento inteligente (top/bottom/left/right)
   - Indicador de paso actual
   - Puntos de progreso
   - Botones de navegación
   - z-index: 10000

4. **Wizard** (`.onboarding-wizard`)
   - Modal centrado en pantalla
   - Formulario con campos personalizados
   - z-index: 10001

5. **Animaciones:**
   - `spotlight-pulse`: Pulsación del borde
   - `tooltip-enter`: Entrada suave del tooltip
   - `welcome-bounce`: Rebote del badge de bienvenida
   - `onboarding-confetti-burst`: Explosión de confeti

---

## Archivos Modificados/Creados

### Nuevos archivos:
1. **`habitgain/onboarding/__init__.py`** - 133 líneas
   - Blueprint con 5 endpoints
   - Manejo de estados de onboarding

2. **`habitgain/static/js/onboarding.js`** - 591 líneas
   - Clase OnboardingTour completa
   - Gestión del tour paso a paso
   - Wizard de primer hábito
   - Integración con API

3. **`test_onboarding.py`** - 335 líneas
   - 4 suites de tests
   - Verificación de modelo
   - Tests de integración
   - Tests de analytics
   - Verificación de estructura de BD

4. **`HU18_IMPLEMENTACION.md`** - Este documento

### Archivos modificados:

1. **`habitgain/models.py`**
   - +234 líneas (clase OnboardingStatus completa)
   - +16 líneas (creación de tabla en init_db)

2. **`habitgain/static/css/styles.css`**
   - +342 líneas de estilos para onboarding

3. **`habitgain/__init__.py`**
   - +2 líneas (import y registro del blueprint)

4. **`habitgain/auth/__init__.py`**
   - +3 líneas (import y auto-create de onboarding status)

5. **`habitgain/progress/__init__.py`**
   - +3 líneas (import y verificación de needs_onboarding)

6. **`habitgain/progress/templates/progress/panel.html`**
   - +8 líneas modificadas (data attributes y script include)

7. **`habitgain/templates/base.html`**
   - +3 líneas (meta tag CSRF para JavaScript)

---

## Pruebas Realizadas

### Tests Automatizados ✅

**Ejecutar:**
```bash
python test_onboarding.py
```

**Resultados:**
```
✓ Test 1: Modelo OnboardingStatus (7 sub-tests)
  ✓ Usuario nuevo necesita onboarding
  ✓ Estado creado correctamente
  ✓ Pasos completados correctamente
  ✓ Onboarding completado al finalizar 5 pasos
  ✓ Usuario completado no necesita onboarding
  ✓ Función de saltar funciona
  ✓ Reset funciona correctamente

✓ Test 2: Integración con la aplicación
  ✓ Data attribute presente en panel
  ✓ Elementos del tour presentes
  ✓ Todos los endpoints funcionan

✓ Test 3: Analytics
  ✓ Estadísticas generadas correctamente

✓ Test 4: Verificación de BD
  ✓ Tabla onboarding_status existe con 7 columnas
  ✓ Índices creados correctamente
```

### Tests Manuales Recomendados 🖱️

1. **Flujo completo de nuevo usuario:**
   ```bash
   flask run
   # Abrir http://localhost:5000
   # Ir a /auth/register
   # Registrar usuario nuevo: test@example.com / Test User / password123
   ```
   - ✓ Verificar que aparece el tour automáticamente
   - ✓ Navegar por los 5 pasos
   - ✓ Verificar que el spotlight resalta los elementos correctos
   - ✓ Probar botón "Anterior"
   - ✓ Completar wizard de primer hábito
   - ✓ Verificar confeti al finalizar

2. **Funcionalidad de Skip:**
   - En cualquier paso, hacer clic en "Saltar tutorial"
   - Confirmar en el diálogo
   - Verificar que el tour se cierra
   - Recargar página y verificar que NO aparece de nuevo

3. **Reset del onboarding:**
   ```bash
   # Desde Flask shell o endpoint:
   curl -X POST http://localhost:5000/onboarding/reset
   ```
   - Recargar página
   - Verificar que el tour aparece de nuevo

4. **Analytics dashboard:**
   ```bash
   curl http://localhost:5000/onboarding/analytics
   ```
   - Verificar que las métricas son correctas

---

## Flujo de Usuario (User Journey)

### Nuevo Usuario:
```
1. Registro en /auth/register
   ↓
2. Auto-redirect a /progress/panel
   ↓
3. OnboardingStatus.create_status(email) ejecutado
   ↓
4. needs_onboarding = True en contexto del template
   ↓
5. data-needs-onboarding="true" en <body>
   ↓
6. onboarding.js detecta el atributo
   ↓
7. OnboardingTour.start() después de 500ms
   ↓
8. Usuario navega por 5 pasos
   ↓
9. Al llegar al paso 5, se muestra wizard
   ↓
10. Usuario crea primer hábito (opcional)
   ↓
11. Confeti de celebración
   ↓
12. OnboardingStatus marcado como completed
   ↓
13. needs_onboarding = False en próximas visitas
```

### Usuario que Salta:
```
1. En cualquier paso, clic en "Saltar tutorial"
   ↓
2. Confirmación del usuario
   ↓
3. POST /onboarding/skip
   ↓
4. OnboardingStatus.mark_skipped(email)
   ↓
5. Tour se cierra
   ↓
6. needs_onboarding = False en próximas visitas
```

---

## Detalles Técnicos de Implementación

### 1. Sistema de Posicionamiento del Tooltip

El tooltip se posiciona inteligentemente respecto al elemento objetivo:

```javascript
positionTooltip(position, targetElement) {
    const rect = targetElement.getBoundingClientRect();
    const offset = 20;

    // 4 posiciones: top, bottom, left, right
    // Ajuste automático si se sale de pantalla
    if (left < 10) left = 10;
    if (left + width > window.innerWidth - 10) {
        left = window.innerWidth - width - 10;
    }
}
```

### 2. Spotlight con Box-Shadow Trick

El spotlight crea la ilusión de un recorte usando una sombra gigante:

```css
.onboarding-spotlight {
    box-shadow:
        0 0 0 9999px rgba(0, 0, 0, 0.75),  /* "Recorte" visual */
        0 0 20px rgba(123, 113, 255, 0.6),  /* Brillo exterior */
        inset 0 0 15px rgba(123, 113, 255, 0.3); /* Brillo interior */
}
```

### 3. Tracking de Pasos

Cada paso se trackea automáticamente en el backend:

```javascript
async markStepComplete(stepNumber) {
    await fetch('/onboarding/step', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': this.csrfToken
        },
        body: JSON.stringify({ step: stepNumber })
    });
}
```

### 4. Creación del Primer Hábito desde Wizard

El wizard hace submit directamente al endpoint existente `/habits/new`:

```javascript
const response = await fetch('/habits/new', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRF-Token': this.csrfToken
    },
    body: new URLSearchParams({
        name: name,
        short_desc: desc,
        category_id: category,
        frequency: 'daily'
    })
});
```

---

## Métricas de Éxito (KPIs)

Para medir el impacto del onboarding, se recomienda trackear:

1. **Tasa de Completitud**: % de usuarios que completan el tour
   - Fórmula: `(completed / total_onboarding) * 100`
   - Objetivo: > 60%

2. **Tasa de Skip**: % de usuarios que saltan el tour
   - Fórmula: `(skipped / total_onboarding) * 100`
   - Objetivo: < 30%

3. **Tiempo promedio por paso**: Cuánto tiempo pasan los usuarios en cada paso
   - Requiere tracking adicional (no implementado)

4. **Conversión a primer hábito**: % de usuarios que crean su primer hábito desde el wizard
   - Requiere tracking adicional (no implementado)

5. **Retención D1/D7**: % de usuarios que regresan después de completar onboarding
   - Comparar vs usuarios que saltaron
   - Requiere tracking adicional (no implementado)

**Analytics actuales disponibles:**
```python
OnboardingStatus.get_analytics()
# Returns:
{
    "total_users": int,
    "total_onboarding": int,
    "completed": int,
    "skipped": int,
    "in_progress": int,
    "completion_rate": float,  # %
    "skip_rate": float,         # %
    "avg_steps_completed": float
}
```

---

## Mejoras Futuras (Opcional)

### Corto plazo:
- [ ] Tracking de tiempo por paso
- [ ] A/B testing de mensajes del tour
- [ ] Personalización de pasos según tipo de usuario
- [ ] Onboarding contextual (mostrar tips en momentos relevantes)

### Mediano plazo:
- [ ] Video tutoriales embebidos
- [ ] Gamificación: badges por completar onboarding
- [ ] Encuesta de satisfacción post-onboarding
- [ ] Dashboard de admin para ver analytics

### Largo plazo:
- [ ] Onboarding adaptativo con ML
- [ ] Tours específicos por feature
- [ ] Sistema de "hints" progresivos
- [ ] Integración con sistema de ayuda contextual

---

## Principios de UX Aplicados

### 1. Progresividad
- El tour se divide en pasos pequeños y manejables
- Cada paso se enfoca en UNA función específica
- El usuario puede ir a su propio ritmo

### 2. Control del usuario
- Botón de "Saltar" siempre visible
- Navegación bidireccional (Anterior/Siguiente)
- Opción de "Crear después" en el wizard
- Posibilidad de re-ver el tour (reset)

### 3. Feedback visual
- Spotlight que resalta elementos
- Indicador de progreso (puntos)
- Animaciones suaves de transición
- Confeti de celebración al finalizar

### 4. Diseño consistente
- Uso del sistema de diseño existente (glassmorphism)
- Colores del tema (--primary, --accent)
- Tipografía coherente
- Iconos emoji para mayor claridad

### 5. Accesibilidad
- z-index apropiados para modal stacking
- Contraste adecuado en textos
- Botones con estados hover claros
- Animaciones no invasivas (pueden pausarse)

---

## Conclusión

La HU-18 está **completamente implementada y probada**. Todos los criterios de aceptación están cumplidos:

✅ **CDA 1**: Tour guiado de 5 pasos con opción de saltar
✅ **CDA 2**: Wizard para crear primer hábito
✅ **CDA 3**: Personalización inicial (nombre, categoría, motivación)
✅ **CDA 4**: Analytics de completitud del onboarding

La implementación sigue mejores prácticas de UX, es completamente funcional, y está lista para producción.

---

**Implementado por:** Claude Code
**Fecha:** 2025-11-13
**Versión:** 1.0
**Estado:** Producción Ready ✅
