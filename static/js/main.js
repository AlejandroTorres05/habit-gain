// ============================================
// UTILIDADES GENERALES
// ============================================

/**
 * Debounce function para optimizar búsquedas
 * @param {Function} func - Función a ejecutar
 * @param {number} wait - Tiempo de espera en ms
 * @returns {Function}
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Muestra mensaje de feedback temporal
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo: 'success', 'error', 'info'
 */
function showFeedback(message, type = 'success') {
    // Implementación futura para notificaciones toast
    console.log(`[${type.toUpperCase()}]: ${message}`);
    
    // Por ahora, usar alert simple (mejorar en futuras HU)
    if (type === 'error') {
        console.error(message);
    }
}

/**
 * Animación suave al hacer scroll
 * @param {HTMLElement} element - Elemento al que hacer scroll
 */
function smoothScrollTo(element) {
    if (element) {
        element.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }
}

/**
 * Formatea fecha a formato legible
 * @param {string} dateString - Fecha en formato ISO
 * @returns {string}
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    return date.toLocaleDateString('es-ES', options);
}

/**
 * Valida si un string está vacío o solo tiene espacios
 * @param {string} str - String a validar
 * @returns {boolean}
 */
function isEmpty(str) {
    return !str || str.trim().length === 0;
}

// ============================================
// EXPORTS (para uso en otros archivos)
// ============================================
window.appUtils = {
    debounce,
    showFeedback,
    smoothScrollTo,
    formatDate,
    isEmpty
};

// ============================================
// INICIALIZACIÓN GLOBAL
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Habit Gain MVP - Inicializado');
});