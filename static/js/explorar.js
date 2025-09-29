// ============================================
// VARIABLES GLOBALES
// ============================================
let categoriaSeleccionada = null;
let todosLosHabitos = [];

// ============================================
// INICIALIZACIÓN
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    console.log('📚 Módulo de Exploración - Inicializado');
    
    // Guardar todos los hábitos al cargar la página
    cargarHabitosIniciales();
    
    // Event listeners
    inicializarEventListeners();
});

/**
 * Carga los hábitos iniciales en memoria
 */
function cargarHabitosIniciales() {
    const habitCards = document.querySelectorAll('.habit-card');
    todosLosHabitos = Array.from(habitCards);
    console.log(`✅ Cargados ${todosLosHabitos.length} hábitos`);
}

/**
 * Inicializa todos los event listeners
 */
function inicializarEventListeners() {
    // Categorías
    const categoryCards = document.querySelectorAll('.category-card');
    categoryCards.forEach(card => {
        card.addEventListener('click', handleCategoriaClick);
    });
    
    // Tarjetas de hábitos
    const habitCards = document.querySelectorAll('.habit-card');
    habitCards.forEach(card => {
        card.addEventListener('click', handleHabitoClick);
    });
    
    // Búsqueda
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', window.appUtils.debounce(handleBusqueda, 300));
    }
    
    console.log('✅ Event listeners inicializados');
}

// ============================================
// MANEJO DE CATEGORÍAS
// ============================================

/**
 * Maneja el click en una categoría
 * @param {Event} event
 */
function handleCategoriaClick(event) {
    const card = event.currentTarget;
    const categoriaId = card.dataset.categoriaId;
    
    // Toggle de selección
    const wasActive = card.classList.contains('active');
    
    // Remover active de todas las categorías
    document.querySelectorAll('.category-card').forEach(c => {
        c.classList.remove('active');
    });
    
    if (wasActive) {
        // Si ya estaba activa, mostrar todos los hábitos
        categoriaSeleccionada = null;
        mostrarTodosLosHabitos();
        console.log('📋 Mostrando todos los hábitos');
    } else {
        // Activar la categoría seleccionada
        card.classList.add('active');
        categoriaSeleccionada = categoriaId;
        filtrarHabitosPorCategoria(categoriaId);
        console.log(`🔍 Filtrando por categoría: ${categoriaId}`);
    }
    
    // Limpiar búsqueda
    document.getElementById('searchInput').value = '';
}

/**
 * Filtra hábitos por categoría usando la API
 * @param {string} categoriaId - ID de la categoría
 */
async function filtrarHabitosPorCategoria(categoriaId) {
    try {
        const response = await fetch(`/api/habitos/categoria/${categoriaId}`);
        
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        
        const habitos = await response.json();
        console.log(`✅ Encontrados ${habitos.length} hábitos en la categoría`);
        
        renderizarHabitos(habitos);
    } catch (error) {
        console.error('❌ Error al filtrar hábitos:', error);
        window.appUtils.showFeedback('Error al cargar hábitos', 'error');
    }
}

/**
 * Muestra todos los hábitos
 */
function mostrarTodosLosHabitos() {
    const habitsList = document.getElementById('habitsList');
    const noResults = document.getElementById('noResults');
    
    habitsList.innerHTML = '';
    
    todosLosHabitos.forEach(habit => {
        habitsList.appendChild(habit.cloneNode(true));
    });
    
    // Re-agregar event listeners a los clones
    const habitCards = habitsList.querySelectorAll('.habit-card');
    habitCards.forEach(card => {
        card.addEventListener('click', handleHabitoClick);
    });
    
    habitsList.style.display = 'flex';
    noResults.style.display = 'none';
}

// ============================================
// BÚSQUEDA
// ============================================

/**
 * Maneja la búsqueda de hábitos
 * @param {Event} event
 */
async function handleBusqueda(event) {
    const query = event.target.value.trim();
    
    console.log(`🔎 Buscando: "${query}"`);
    
    // Si hay búsqueda, desactivar filtro de categoría
    if (query) {
        document.querySelectorAll('.category-card').forEach(c => {
            c.classList.remove('active');
        });
        categoriaSeleccionada = null;
    }
    
    try {
        const response = await fetch(`/api/habitos/buscar?q=${encodeURIComponent(query)}`);
        
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        
        const habitos = await response.json();
        console.log(`✅ Encontrados ${habitos.length} hábitos`);
        
        renderizarHabitos(habitos);
    } catch (error) {
        console.error('❌ Error en búsqueda:', error);
        window.appUtils.showFeedback('Error al buscar hábitos', 'error');
    }
}

// ============================================
// RENDERIZADO
// ============================================

/**
 * Renderiza la lista de hábitos
 * @param {Array} habitos - Array de objetos de hábitos
 */
function renderizarHabitos(habitos) {
    const habitsList = document.getElementById('habitsList');
    const noResults = document.getElementById('noResults');
    
    if (habitos.length === 0) {
        habitsList.style.display = 'none';
        noResults.style.display = 'block';
        console.log('⚠️ No se encontraron hábitos');
    } else {
        habitsList.style.display = 'flex';
        noResults.style.display = 'none';
        
        habitsList.innerHTML = '';
        
        habitos.forEach(habito => {
            const card = crearTarjetaHabito(habito);
            habitsList.appendChild(card);
        });
        
        console.log(`✅ Renderizados ${habitos.length} hábitos`);
    }
}

/**
 * Crea una tarjeta de hábito
 * @param {Object} habito - Objeto con datos del hábito
 * @returns {HTMLElement}
 */
function crearTarjetaHabito(habito) {
    const card = document.createElement('div');
    card.className = 'habit-card';
    card.dataset.habitoId = habito.id;
    
    card.innerHTML = `
        <div class="habit-icon">${habito.icono}</div>
        <div class="habit-info">
            <div class="habit-name">${habito.nombre}</div>
            <div class="habit-frequency">${habito.frecuencia}</div>
        </div>
    `;
    
    card.addEventListener('click', handleHabitoClick);
    
    return card;
}

// ============================================
// NAVEGACIÓN
// ============================================

/**
 * Maneja el click en una tarjeta de hábito
 * @param {Event} event
 */
function handleHabitoClick(event) {
    const card = event.currentTarget;
    const habitoId = card.dataset.habitoId;
    
    console.log(`➡️ Navegando a hábito: ${habitoId}`);
    
    // Navegar a la página de detalle
    window.location.href = `/habito/${habitoId}`;
}