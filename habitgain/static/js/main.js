// ============================================
// HabitGain — Global utilities (namespace-safe)
// ============================================
(() => {
    /** Debounce helper */
    function debounce(fn, wait = 300) {
        let t;
        return (...args) => {
            clearTimeout(t);
            t = setTimeout(() => fn(...args), wait);
        };
    }

    /**
     * Toast factory (Bootstrap 5)
     * Crea y muestra un toast "glass" con autohide.
     */
    function showToast(message, type = "info", delay = 3800) {
        // Contenedor fijo arriba-derecha (si no existe, lo crea)
        let container = document.querySelector(".toast-container");
        if (!container) {
            container = document.createElement("div");
            container.className = "toast-container position-fixed top-0 end-0 p-3";
            document.body.appendChild(container);
        }

        const iconByType = {
            success: "bi-check-circle text-success",
            danger: "bi-x-circle text-danger",
            error: "bi-x-circle text-danger",
            warning: "bi-exclamation-triangle text-warning",
            info: "bi-info-circle text-primary",
        };
        const iconClass = iconByType[type] || iconByType.info;

        // Toast element
        const toastEl = document.createElement("div");
        toastEl.className = "toast glass shadow-sm mb-2 border-0";
        toastEl.setAttribute("role", "alert");
        toastEl.setAttribute("aria-live", "assertive");
        toastEl.setAttribute("aria-atomic", "true");
        toastEl.dataset.bsAutohide = "true";
        toastEl.dataset.bsDelay = String(delay);

        toastEl.innerHTML = `
      <div class="toast-body d-flex gap-2 align-items-center">
        <i class="bi ${iconClass}"></i>
        <span>${message}</span>
        <button type="button" class="btn-close ms-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

        container.appendChild(toastEl);

        // Inicializa y muestra (si Bootstrap no está, cae elegante)
        try {
            // eslint-disable-next-line no-undef
            const t = new bootstrap.Toast(toastEl);
            t.show();
        } catch {
            // Plan B: log a consola si Bootstrap no está cargado
            console.log(`[TOAST:${type}]`, message);
        }
        return toastEl;
    }

    /**
     * Simple notifier
     * - Sigue loggeando a consola
     * - Además muestra toast visual si el DOM está listo
     */
    function notify(message, type = "info") {
        const tag = `[${type.toUpperCase()}]`;
        if (type === "error") console.error(tag, message);
        else if (type === "warn" || type === "warning") console.warn(tag, message);
        else console.log(tag, message);

        if (document.readyState === "complete" || document.readyState === "interactive") {
            showToast(message, type === "warn" ? "warning" : type);
        } else {
            // Diferir hasta que el DOM esté listo
            document.addEventListener("DOMContentLoaded", () =>
                showToast(message, type === "warn" ? "warning" : type)
            );
        }
    }

    /** Backward-compatible name used by some modules */
    const showFeedback = notify;

    /** Smooth scroll to element */
    function smoothScrollTo(element) {
        if (element) element.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    /** Format date (configurable locale) */
    function formatDate(dateString, locale = "en-GB", options) {
        const d = new Date(dateString);
        const opts = options || { year: "numeric", month: "long", day: "numeric" };
        return d.toLocaleDateString(locale, opts);
    }

    /** Empty/whitespace check */
    function isEmpty(str) {
        return !str || str.trim().length === 0;
    }

    // Expose in a single namespace
    window.appUtils = {
        debounce,
        notify,
        showFeedback,   // alias kept for existing code
        smoothScrollTo,
        formatDate,
        isEmpty,
        showToast,      // por si lo quieres usar directo
    };

    // ==================================================
    // Auto-init UI bits (toasts ya presentes en la página)
    // ==================================================
    document.addEventListener("DOMContentLoaded", () => {
        // Inicializa cualquier .toast del DOM (con autohide si tienen data attrs)
        document.querySelectorAll(".toast").forEach(el => {
            try {
                // eslint-disable-next-line no-undef
                const t = new bootstrap.Toast(el);
                t.show();
            } catch {
                /* sin Bootstrap, no hacemos nada */
            }
        });

        // Marcar carga de utilidades
        console.log("HabitGain — utilities loaded");
    });
})();
