/**
 * HU-18: Sistema de Onboarding Interactivo
 *
 * Tour guiado paso a paso para nuevos usuarios con:
 * - 5 pasos con spotlight y tooltips
 * - Opción de saltar en cualquier momento
 * - Wizard para crear primer hábito
 * - Tracking de progreso
 */

class OnboardingTour {
    constructor() {
        this.currentStep = 0;
        this.totalSteps = 5;
        this.csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
        this.currentHighlightedElement = null;

        // Definición de los pasos del tour
        this.steps = [
            {
                target: '.section-kicker',
                icon: '👋',
                title: '¡Bienvenido a HabitGain!',
                content: 'Te guiaremos en un rápido recorrido para que aproveches al máximo la aplicación. Puedes saltar este tutorial en cualquier momento.',
                position: 'bottom'
            },
            {
                target: '[data-onboarding="habits-list"]',
                icon: '📋',
                title: 'Tus Hábitos',
                content: 'Aquí verás todos tus hábitos activos. Cada uno tiene un medidor de fortaleza que crece con tu constancia.',
                position: 'right'
            },
            {
                target: '[data-onboarding="complete-button"]',
                icon: '✅',
                title: 'Completar Hábitos',
                content: 'Haz clic aquí cada día para marcar un hábito como completado. ¡Verás animaciones motivadoras y tu racha aumentará!',
                position: 'left'
            },
            {
                target: '[data-onboarding="progress-stats"]',
                icon: '📊',
                title: 'Tu Progreso',
                content: 'Monitorea tu consistencia semanal y mantén tus rachas activas. La ciencia dice que 21 días forman un hábito.',
                position: 'top'
            },
            {
                target: '[data-onboarding="create-habit"]',
                icon: '🎯',
                title: 'Crear Hábitos',
                content: '¿Listo para empezar? Vamos a crear tu primer hábito juntos.',
                position: 'bottom',
                action: 'showWizard'
            }
        ];

        this.overlay = null;
        this.spotlight = null;
        this.tooltip = null;
        this.wizard = null;
    }

    /**
     * Inicia el tour de onboarding
     */
    async start() {
        this.createElements();
        this.showStep(0);
    }

    /**
     * Crea los elementos HTML necesarios para el tour
     */
    createElements() {
        // Overlay oscuro
        this.overlay = document.createElement('div');
        this.overlay.className = 'onboarding-overlay';
        document.body.appendChild(this.overlay);

        // Spotlight (resaltado)
        this.spotlight = document.createElement('div');
        this.spotlight.className = 'onboarding-spotlight';
        document.body.appendChild(this.spotlight);

        // Tooltip (tarjeta informativa)
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'onboarding-tooltip';
        document.body.appendChild(this.tooltip);

        // Activar overlay
        setTimeout(() => this.overlay.classList.add('active'), 50);
    }

    /**
     * Muestra un paso específico del tour
     */
    showStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= this.totalSteps) {
            return;
        }

        this.currentStep = stepIndex;
        const step = this.steps[stepIndex];

        // Remover highlight del elemento anterior
        if (this.currentHighlightedElement) {
            this.currentHighlightedElement.classList.remove('onboarding-highlight');
            this.currentHighlightedElement.style.position = '';
            this.currentHighlightedElement.style.zIndex = '';
        }

        // Buscar elemento objetivo
        const targetElement = document.querySelector(step.target);

        if (!targetElement) {
            console.warn(`Elemento no encontrado: ${step.target}`);
            // Si el elemento no existe, pasar al siguiente paso
            if (stepIndex < this.totalSteps - 1) {
                this.showStep(stepIndex + 1);
            } else {
                this.finish();
            }
            return;
        }

        // Resaltar el elemento actual
        this.currentHighlightedElement = targetElement;
        const originalPosition = window.getComputedStyle(targetElement).position;
        if (originalPosition === 'static') {
            targetElement.style.position = 'relative';
        }
        targetElement.style.zIndex = '10000';
        targetElement.classList.add('onboarding-highlight');

        // Posicionar spotlight
        this.positionSpotlight(targetElement);

        // Renderizar tooltip
        this.renderTooltip(step, targetElement);

        // Marcar paso como completado en el backend
        this.markStepComplete(stepIndex);
    }

    /**
     * Posiciona el spotlight sobre el elemento objetivo
     */
    positionSpotlight(element) {
        const rect = element.getBoundingClientRect();
        const padding = 8;

        this.spotlight.style.top = `${rect.top - padding + window.scrollY}px`;
        this.spotlight.style.left = `${rect.left - padding}px`;
        this.spotlight.style.width = `${rect.width + padding * 2}px`;
        this.spotlight.style.height = `${rect.height + padding * 2}px`;
    }

    /**
     * Renderiza el tooltip con la información del paso
     */
    renderTooltip(step, targetElement) {
        const isLastStep = this.currentStep === this.totalSteps - 1;

        this.tooltip.innerHTML = `
            <div class="onboarding-tooltip-header">
                <span class="onboarding-step-indicator">Paso ${this.currentStep + 1} de ${this.totalSteps}</span>
                <button class="onboarding-tooltip-close" onclick="onboardingTour.skip()">×</button>
            </div>

            <div class="onboarding-tooltip-icon">${step.icon}</div>
            <h3 class="onboarding-tooltip-title">${step.title}</h3>
            <p class="onboarding-tooltip-content">${step.content}</p>

            <div class="onboarding-tooltip-actions">
                <div class="onboarding-progress-dots">
                    ${this.renderProgressDots()}
                </div>
                <div class="onboarding-btn-group">
                    ${this.currentStep > 0 ? '<button class="onboarding-btn-prev" onclick="onboardingTour.previousStep()">← Anterior</button>' : '<button class="onboarding-btn-skip" onclick="onboardingTour.skip()">Saltar tutorial</button>'}
                    ${isLastStep ?
                        '<button class="onboarding-btn-finish" onclick="onboardingTour.showWizard()">¡Crear mi primer hábito! 🚀</button>' :
                        '<button class="onboarding-btn-next" onclick="onboardingTour.nextStep()">Siguiente →</button>'
                    }
                </div>
            </div>
        `;

        // Posicionar tooltip
        this.positionTooltip(step.position, targetElement);

        // Activar tooltip con animación
        this.tooltip.classList.remove('active');
        setTimeout(() => {
            this.tooltip.classList.add('active', 'entering');
            setTimeout(() => this.tooltip.classList.remove('entering'), 400);
        }, 50);
    }

    /**
     * Renderiza los puntos de progreso
     */
    renderProgressDots() {
        let dots = '';
        for (let i = 0; i < this.totalSteps; i++) {
            dots += `<div class="onboarding-progress-dot ${i === this.currentStep ? 'active' : ''}"></div>`;
        }
        return dots;
    }

    /**
     * Posiciona el tooltip respecto al elemento objetivo
     */
    positionTooltip(position, targetElement) {
        const rect = targetElement.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();
        const offset = 20;

        let top, left;

        switch(position) {
            case 'bottom':
                top = rect.bottom + offset + window.scrollY;
                left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                break;
            case 'top':
                top = rect.top - tooltipRect.height - offset + window.scrollY;
                left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
                break;
            case 'right':
                top = rect.top + (rect.height / 2) - (tooltipRect.height / 2) + window.scrollY;
                left = rect.right + offset;
                break;
            case 'left':
                top = rect.top + (rect.height / 2) - (tooltipRect.height / 2) + window.scrollY;
                left = rect.left - tooltipRect.width - offset;
                break;
            default:
                top = rect.bottom + offset + window.scrollY;
                left = rect.left;
        }

        // Ajustar si se sale de la pantalla
        if (left < 10) left = 10;
        if (left + tooltipRect.width > window.innerWidth - 10) {
            left = window.innerWidth - tooltipRect.width - 10;
        }
        if (top < 10) top = rect.bottom + offset + window.scrollY;

        this.tooltip.style.top = `${top}px`;
        this.tooltip.style.left = `${left}px`;
    }

    /**
     * Avanza al siguiente paso
     */
    nextStep() {
        if (this.currentStep < this.totalSteps - 1) {
            this.showStep(this.currentStep + 1);
        } else {
            this.finish();
        }
    }

    /**
     * Retrocede al paso anterior
     */
    previousStep() {
        if (this.currentStep > 0) {
            this.showStep(this.currentStep - 1);
        }
    }

    /**
     * Muestra el wizard para crear el primer hábito
     */
    async showWizard() {
        // Ocultar tour
        this.hideElements();

        // Crear wizard
        this.wizard = document.createElement('div');
        this.wizard.className = 'onboarding-wizard';
        this.wizard.innerHTML = `
            <div class="onboarding-wizard-header">
                <div class="onboarding-wizard-icon">🎯</div>
                <h2 class="onboarding-wizard-title">Crea tu primer hábito</h2>
                <p class="onboarding-wizard-subtitle">Empieza con algo simple y alcanzable</p>
            </div>

            <form class="onboarding-wizard-form" id="onboardingWizardForm">
                <div>
                    <label for="wizard-habit-name" class="form-label">¿Qué hábito quieres formar?</label>
                    <input type="text" id="wizard-habit-name" class="form-control"
                           placeholder="Ej: Leer 10 páginas, Meditar 5 minutos..." required>
                </div>

                <div>
                    <label for="wizard-habit-desc" class="form-label">¿Por qué es importante para ti?</label>
                    <textarea id="wizard-habit-desc" class="form-control" rows="3"
                              placeholder="Ej: Quiero reducir el estrés y mejorar mi concentración..." required></textarea>
                </div>

                <div>
                    <label for="wizard-habit-category" class="form-label">Categoría</label>
                    <select id="wizard-habit-category" class="form-select" required>
                        <option value="1">💪 Salud y Fitness</option>
                        <option value="2">🧘 Mindfulness</option>
                        <option value="3">📚 Aprendizaje</option>
                        <option value="4">🎨 Creatividad</option>
                        <option value="5">💼 Productividad</option>
                    </select>
                </div>

                <div class="onboarding-wizard-actions">
                    <button type="button" class="onboarding-btn-skip" onclick="onboardingTour.skipWizard()">
                        Crear después
                    </button>
                    <button type="submit" class="onboarding-btn-finish">
                        ¡Comenzar mi hábito! 🚀
                    </button>
                </div>
            </form>
        `;

        document.body.appendChild(this.wizard);

        // Activar wizard
        setTimeout(() => this.wizard.classList.add('active'), 50);

        // Event listener para el formulario
        document.getElementById('onboardingWizardForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createHabit();
        });
    }

    /**
     * Crea el hábito del wizard
     */
    async createHabit() {
        const name = document.getElementById('wizard-habit-name').value;
        const desc = document.getElementById('wizard-habit-desc').value;
        const category = document.getElementById('wizard-habit-category').value;

        try {
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

            if (response.ok) {
                // Mostrar confeti de celebración
                this.showConfetti();

                // Cerrar wizard
                this.wizard.classList.remove('active');
                setTimeout(() => {
                    this.wizard.remove();
                    this.completeOnboarding();
                }, 300);
            } else {
                alert('Hubo un error al crear el hábito. Por favor, intenta nuevamente.');
            }
        } catch (error) {
            console.error('Error al crear hábito:', error);
            alert('Hubo un error al crear el hábito. Por favor, intenta nuevamente.');
        }
    }

    /**
     * Salta el wizard y completa el onboarding
     */
    skipWizard() {
        this.wizard.classList.remove('active');
        setTimeout(() => {
            this.wizard.remove();
            this.completeOnboarding();
        }, 300);
    }

    /**
     * Marca el paso como completado en el backend
     */
    async markStepComplete(stepNumber) {
        try {
            await fetch('/onboarding/step', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': this.csrfToken
                },
                body: JSON.stringify({ step: stepNumber })
            });
        } catch (error) {
            console.error('Error al marcar paso:', error);
        }
    }

    /**
     * Marca el onboarding como saltado
     */
    async skip() {
        if (confirm('¿Estás seguro de que quieres saltar el tutorial? Puedes volver a verlo desde tu perfil.')) {
            try {
                const response = await fetch('/onboarding/skip', {
                    method: 'POST',
                    headers: {
                        'X-CSRF-Token': this.csrfToken
                    }
                });

                if (response.ok) {
                    this.cleanup();
                    // Esperar a que la limpieza termine antes de recargar
                    setTimeout(() => {
                        location.reload();
                    }, 500);
                }
            } catch (error) {
                console.error('Error al saltar onboarding:', error);
                this.cleanup();
                setTimeout(() => {
                    location.reload();
                }, 500);
            }
        }
    }

    /**
     * Finaliza el tour sin completar el wizard
     */
    finish() {
        this.showWizard();
    }

    /**
     * Completa el onboarding completamente
     */
    async completeOnboarding() {
        try {
            // Marcar el onboarding como completado en el backend
            await fetch('/onboarding/complete', {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': this.csrfToken
                }
            });

            // Mostrar mensaje de éxito usando el sistema de toasts nativo
            if (window.appUtils && window.appUtils.showToast) {
                window.appUtils.showToast('🎉 ¡Onboarding completado! Bienvenido a HabitGain!', 'success', 2000);
            }

            // Limpiar elementos
            this.cleanup();

            // Recargar página después de 2 segundos
            setTimeout(() => {
                location.reload();
            }, 2000);
        } catch (error) {
            console.error('Error al completar onboarding:', error);
            // Intentar limpiar y recargar de todos modos
            this.cleanup();
            setTimeout(() => {
                location.reload();
            }, 2000);
        }
    }

    /**
     * Oculta los elementos del tour
     */
    hideElements() {
        if (this.overlay) this.overlay.classList.remove('active');
        if (this.tooltip) this.tooltip.classList.remove('active');
        if (this.spotlight) this.spotlight.style.opacity = '0';
    }

    /**
     * Limpia y elimina todos los elementos del DOM
     */
    cleanup() {
        // Remover highlight del elemento actual
        if (this.currentHighlightedElement) {
            this.currentHighlightedElement.classList.remove('onboarding-highlight');
            this.currentHighlightedElement.style.position = '';
            this.currentHighlightedElement.style.zIndex = '';
            this.currentHighlightedElement = null;
        }

        this.hideElements();

        setTimeout(() => {
            if (this.overlay) this.overlay.remove();
            if (this.spotlight) this.spotlight.remove();
            if (this.tooltip) this.tooltip.remove();
            if (this.wizard) this.wizard.remove();
        }, 400);
    }

    /**
     * Muestra confeti de celebración
     */
    showConfetti() {
        const colors = ['🎉', '🎊', '⭐', '✨', '🌟', '💫'];
        const count = 30;

        for (let i = 0; i < count; i++) {
            setTimeout(() => {
                const confetti = document.createElement('div');
                confetti.className = 'onboarding-confetti';
                confetti.textContent = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.left = `${Math.random() * 100}%`;
                confetti.style.top = `${Math.random() * 100}%`;
                confetti.style.animationDelay = `${Math.random() * 0.5}s`;

                document.body.appendChild(confetti);

                setTimeout(() => confetti.remove(), 2000);
            }, i * 50);
        }
    }
}

// Variable global para acceder al tour
let onboardingTour = null;

/**
 * Inicializa el onboarding si el usuario lo necesita
 */
function initOnboarding() {
    // Verificar si el usuario necesita onboarding
    const needsOnboarding = document.body.dataset.needsOnboarding === 'true';

    if (needsOnboarding) {
        onboardingTour = new OnboardingTour();

        // Esperar a que el DOM esté completamente cargado
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(() => onboardingTour.start(), 500);
            });
        } else {
            setTimeout(() => onboardingTour.start(), 500);
        }
    }
}

// Auto-inicializar
initOnboarding();
