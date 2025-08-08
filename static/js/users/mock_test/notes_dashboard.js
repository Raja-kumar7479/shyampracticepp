document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('search-input');
    const topicsContainer = document.getElementById('topics-container');
    const noResultsMessage = document.getElementById('no-results');

    if (!searchInput || !topicsContainer || !noResultsMessage) {
        return;
    }

    const allListItems = Array.from(topicsContainer.querySelectorAll('.topic-list li'));
    const allTopicWrappers = Array.from(topicsContainer.querySelectorAll('.topic-list-wrapper'));
    const allTopicRows = Array.from(topicsContainer.querySelectorAll('.topic-row'));
    const originalHTML = new Map();

    allListItems.forEach(item => originalHTML.set(item, item.innerHTML));

    const debounce = (func, delay) => {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    };

    const performSearch = (searchTerm) => {
        const searchRegex = new RegExp(searchTerm.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&'), 'gi');
        let anyTopicFound = false;

        allTopicWrappers.forEach(wrapper => {
            const heading = wrapper.querySelector('.topic-heading');
            const listItems = wrapper.querySelectorAll('.topic-list > li');
            let wrapperHasVisibleItem = false;

            listItems.forEach(li => {
                const originalContent = originalHTML.get(li);
                const isMatch = li.textContent.toLowerCase().includes(searchTerm);
                
                if (isMatch) {
                    wrapperHasVisibleItem = true;
                    li.innerHTML = originalContent.replace(searchRegex, match => `<mark class="search-highlight">${match}</mark>`);
                    li.classList.remove('hidden');

                    let parentUl = li.parentElement;
                    while (parentUl && parentUl.tagName === 'UL') {
                        let parentLi = parentUl.previousElementSibling;
                        if (parentLi && parentLi.tagName === 'LI') {
                            parentLi.classList.remove('hidden');
                        }
                        parentUl = parentLi ? parentLi.parentElement : null;
                    }

                } else {
                    li.innerHTML = originalContent;
                    li.classList.add('hidden');
                }
            });
            
            if (heading.textContent.toLowerCase().includes(searchTerm)) {
                 wrapperHasVisibleItem = true;
            }

            wrapper.classList.toggle('hidden', !wrapperHasVisibleItem);
            if (wrapperHasVisibleItem) {
                anyTopicFound = true;
            }
        });

        allTopicRows.forEach(row => {
            const visibleWrappersInRow = row.querySelectorAll('.topic-list-wrapper:not(.hidden)');
            row.classList.toggle('hidden', visibleWrappersInRow.length === 0);
        });

        noResultsMessage.classList.toggle('hidden', anyTopicFound);
    };

    const restoreOriginalState = () => {
        allListItems.forEach(li => {
            li.innerHTML = originalHTML.get(li);
            li.classList.remove('hidden');
        });
        allTopicWrappers.forEach(w => w.classList.remove('hidden'));
        allTopicRows.forEach(r => r.classList.remove('hidden'));
        noResultsMessage.classList.add('hidden');
    };

    const debouncedSearch = debounce(performSearch, 250);

    searchInput.addEventListener('input', function (e) {
        const searchTerm = e.target.value.trim().toLowerCase();
        if (searchTerm.length > 1) {
            debouncedSearch(searchTerm);
        } else {
            restoreOriginalState();
        }
    });
});