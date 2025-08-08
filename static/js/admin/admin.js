
document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.querySelector('.toggle-sidebar');
    const closeBtn = document.querySelector('.close-sidebar');
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    const submenuTriggers = document.querySelectorAll('.has-submenu > a');

    toggleBtn.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('show');
        } else {
            sidebar.classList.toggle('collapsed');
            content.classList.toggle('collapsed');
        }
    });

    closeBtn.addEventListener('click', () => {
        sidebar.classList.remove('show');
    });

    submenuTriggers.forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const parentLi = trigger.parentElement;
            if (sidebar.classList.contains('collapsed')) return;
            const wasOpen = parentLi.classList.contains('open');
            document.querySelectorAll('.has-submenu.open').forEach(openLi => openLi.classList.remove('open'));
            if (!wasOpen) parentLi.classList.add('open');
        });
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) sidebar.classList.remove('show');
    });

    const timerEl = document.getElementById('live-timer');
    const dateEl = document.getElementById('date-display');
    const quoteEl = document.getElementById('motivational-quote');
    const lastUpdatedEl = document.getElementById('last-updated');

    const quotes = [
        "The only way to do great work is to love what you do.",
        "Believe you can and you're halfway there.",
        "The secret of getting ahead is getting started.",
        "Your limitation is only your imagination.",
        "Push yourself, because no one else is going to do it for you."
    ];

    function updateTime() {
        const now = new Date();
        timerEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        dateEl.textContent = now.toLocaleDateString([], { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    }
    
    function updateLastUpdated() {
        const now = new Date();
        lastUpdatedEl.textContent = `Last updated: ${now.toLocaleTimeString()}`;
    }

    function updateQuote() {
        quoteEl.textContent = `"${quotes[Math.floor(Math.random() * quotes.length)]}"`;
    }

    updateTime();
    updateQuote();
    updateLastUpdated();

    setInterval(updateTime, 1000);
    setInterval(updateQuote, 30000);
    setInterval(updateLastUpdated, 30000);
});