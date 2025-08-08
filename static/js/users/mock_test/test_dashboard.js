
    document.addEventListener('DOMContentLoaded', function() {
        const allTestsBtn = document.getElementById('allTestsBtn');
        const unperformedTestsBtn = document.getElementById('unperformedTestsBtn');
        const resultBtn = document.getElementById('resultBtn');
        const testCardsContainer = document.getElementById('testCardsContainer');
        const reportsSection = document.getElementById('reportsSection');

        function showSection(sectionToShow) {
            testCardsContainer.style.display = 'none';
            reportsSection.style.display = 'none';
            sectionToShow.style.display = 'block';
        }

        function filterTests(filterType) {
            const testCards = testCardsContainer.querySelectorAll('.test-card');
            showSection(testCardsContainer);
            testCards.forEach(card => {
                const status = card.dataset.status;
                if (filterType === 'all') {
                    card.style.display = 'block'; 
                } else if (filterType === 'unperformed') {
                    card.style.display = (status === 'unperformed') ? 'block' : 'none';
                }
            });
        }

        allTestsBtn.addEventListener('click', () => filterTests('all'));
        unperformedTestsBtn.addEventListener('click', () => filterTests('unperformed'));
        resultBtn.addEventListener('click', () => showSection(reportsSection));

        const urlParams = new URLSearchParams(window.location.search);
        const action = urlParams.get('action');
        const highlightTestKey = urlParams.get('highlight');

        if (action === 'show_result' && resultBtn) {
            resultBtn.click();
            if (highlightTestKey) {
                setTimeout(() => {
                    const cardToHighlight = document.querySelector(`.report-card[data-test-key="${highlightTestKey}"]`);
                    if (cardToHighlight) {
                        cardToHighlight.classList.add('highlight');
                        cardToHighlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }, 100);
            }
        } else {
            filterTests('all');
        }
    });

    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');
        if (sidebar.classList.contains('active')) {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        } else {
            sidebar.classList.add('active');
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }