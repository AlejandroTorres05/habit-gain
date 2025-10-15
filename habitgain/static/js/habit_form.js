// Manejo de opciones personalizadas
document.addEventListener('DOMContentLoaded', function() {
    // Frecuencia personalizada
    const customFreqRadio = document.getElementById('freq_custom');
    const customFreqInput = document.getElementById('custom_frequency_input');
    const frequencyRadios = document.querySelectorAll('input[name="frequency"]');
    
    frequencyRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.id === 'freq_custom') {
                customFreqInput.style.display = 'block';
                customFreqInput.querySelector('input').focus();
            } else {
                customFreqInput.style.display = 'none';
            }
        });
    });
    
    // Duración personalizada
    const durationSelect = document.getElementById('duration');
    const customDurationInput = document.getElementById('custom_duration_input');
    
    if (durationSelect) {
        durationSelect.addEventListener('change', function() {
            if (this.value === 'Custom') {
                customDurationInput.style.display = 'block';
                customDurationInput.querySelector('input').focus();
            } else {
                customDurationInput.style.display = 'none';
            }
        });
    }
    
    // Selector de días de la semana
    const weekdayCheckboxes = document.querySelectorAll('.weekday-checkbox');
    const selectedDaysInput = document.getElementById('selected_days');
    
    weekdayCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const selectedDays = Array.from(weekdayCheckboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            selectedDaysInput.value = selectedDays.join(',');
        });
    });
});
