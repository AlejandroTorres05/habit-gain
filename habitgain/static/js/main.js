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

    /** Simple notifier (console for now; swap for Bootstrap toasts later) */
    function notify(message, type = "info") {
        const tag = `[${type.toUpperCase()}]`;
        if (type === "error") console.error(tag, message);
        else if (type === "warn" || type === "warning") console.warn(tag, message);
        else console.log(tag, message);
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
        isEmpty
    };

    document.addEventListener("DOMContentLoaded", () => {
        console.log("HabitGain — utilities loaded");
    });
})();
