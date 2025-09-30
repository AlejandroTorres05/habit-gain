// ============================================
// Explore module (clean, English, API-first)
// Routes expected:
//   GET /explore/api/by-category/:id
//   GET /explore/api/search?q=term
//   GET /explore/habit/:id
// ============================================

let selectedCategoryId = null;

// Boot
document.addEventListener('DOMContentLoaded', () => {
    console.log('📚 Explore module — ready');
    initListeners();
});

// Attach global listeners (no DOM cloning nonsense)
function initListeners() {
    // Category cards
    document.querySelectorAll('.category-card').forEach(card => {
        card.addEventListener('click', onCategoryClick);
    });

    // Search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', window.appUtils.debounce(onSearch, 300));
    }

    // Habit cards (as rendered server-side on first load)
    bindHabitCardClicks();
}

function bindHabitCardClicks() {
    document.querySelectorAll('#habitsList .habit-card').forEach(card => {
        card.addEventListener('click', onHabitClick);
    });
}

// ---------------------------
// Category filter
// ---------------------------
async function onCategoryClick(e) {
    const card = e.currentTarget;
    const id = String(card.dataset.categoryId);

    // Toggle UI
    const wasActive = card.classList.contains('active');
    document.querySelectorAll('.category-card').forEach(c => c.classList.remove('active'));

    if (wasActive) {
        selectedCategoryId = null;
        // Show all again via search with empty query (server returns all)
        return refreshFromSearch('');
    }

    selectedCategoryId = id;
    card.classList.add('active');

    try {
        const res = await fetch(`/explore/api/by-category/${id}`);
        if (!res.ok) throw new Error('Bad response');
        const habits = await res.json();
        renderHabits(habits);
        clearSearchBox();
    } catch (err) {
        window.appUtils.showFeedback('Error loading category', 'error');
        console.error(err);
    }
}

function clearSearchBox() {
    const input = document.getElementById('searchInput');
    if (input) input.value = '';
}

// ---------------------------
// Search
// ---------------------------
async function onSearch(e) {
    const q = e.target.value.trim();
    // When searching, cancel any active category selection
    if (q) {
        document.querySelectorAll('.category-card').forEach(c => c.classList.remove('active'));
        selectedCategoryId = null;
    }
    await refreshFromSearch(q);
}

async function refreshFromSearch(q) {
    try {
        const url = `/explore/api/search?q=${encodeURIComponent(q || '')}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Bad response');
        const habits = await res.json();
        renderHabits(habits);
    } catch (err) {
        window.appUtils.showFeedback('Search error', 'error');
        console.error(err);
    }
}

// ---------------------------
// Render
// ---------------------------
function renderHabits(items) {
    const list = document.getElementById('habitsList');
    const empty = document.getElementById('noResults');
    if (!list || !empty) return;

    if (!items || items.length === 0) {
        list.style.display = 'none';
        empty.style.display = 'block';
        return;
    }

    list.style.display = 'flex';
    empty.style.display = 'none';
    list.innerHTML = '';

    items.forEach(h => {
        const card = document.createElement('div');
        card.className = 'habit-card';
        card.dataset.habitId = h.id;
        card.innerHTML = `
      <div class="habit-icon">${h.icon}</div>
      <div class="habit-info">
        <div class="habit-name">${h.name}</div>
        <div class="habit-frequency">${h.frequency}</div>
      </div>
    `;
        card.addEventListener('click', onHabitClick);
        list.appendChild(card);
    });
}

// ---------------------------
/** Navigate to habit detail */
function onHabitClick(e) {
    const id = e.currentTarget.dataset.habitId;
    if (!id) return;
    window.location.href = `/explore/habit/${id}`;
}
