document.addEventListener('DOMContentLoaded', function () {
    const flashContainer = document.getElementById('flash-container');
    const addForm = document.getElementById('add-course-form');
    const coursesTable = document.getElementById('courses-table');
    const toggleBtn = document.getElementById('toggle-courses-btn');
    const coursesWrapper = document.getElementById('existing-courses-wrapper');
    const ownerRole = typeof ADMIN_ROLE !== 'undefined' && ADMIN_ROLE === "owner";

    const showFlashMessage = (message, category) => {
        flashContainer.innerHTML = '';
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${category}`;
        alertDiv.textContent = message;
        flashContainer.appendChild(alertDiv);
        setTimeout(() => {
            alertDiv.style.opacity = '0';
            setTimeout(() => alertDiv.remove(), 600);
        }, 5000);
    };

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const isHidden = coursesWrapper.style.display === 'none';
            coursesWrapper.style.display = isHidden ? 'block' : 'none';
            toggleBtn.textContent = isHidden ? 'Hide Existing Courses' : 'View Existing Courses';
        });
    }

    if (addForm) {
        addForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(addForm);
            const data = Object.fromEntries(formData.entries());
            const addUrl = addForm.dataset.addUrl;

            try {
                const response = await fetch(addUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                });

                const result = await response.json();
                if (response.ok) {
                    showFlashMessage(result.message, 'success');
                    addCourseToTable(result.course);
                    addForm.reset();
                } else {
                    showFlashMessage(result.message || 'An error occurred.', 'error');
                }
            } catch (error) {
                showFlashMessage('Network error. Please try again.', 'error');
            }
        });
    }

    const addCourseToTable = (course) => {
        const newRow = coursesTable.querySelector('tbody').insertRow(0);
        newRow.dataset.code = course.code;
        
        let actionButtons = '';
        if (ownerRole) {
            actionButtons = `
                <td class="action-buttons">
                    <button class="btn btn-update">Update</button>
                    <button class="btn btn-delete">Delete</button>
                </td>`;
        }

        newRow.innerHTML = `
            <td data-field="code">${course.code}</td>
            <td data-field="name">${course.name}</td>
            <td data-field="description">${course.description}</td>
            ${actionButtons}
        `;
    };

    if (coursesTable) {
        coursesTable.addEventListener('click', async (e) => {
            const target = e.target;
            const row = target.closest('tr');
            if (!row || !ownerRole) return;

            const code = row.dataset.code;

            if (target.classList.contains('btn-delete')) {
                if (confirm(`Are you sure you want to delete course '${code}'?`)) {
                    const deleteUrlTemplate = coursesTable.dataset.deleteUrlTemplate;
                    const deleteUrl = deleteUrlTemplate.replace('CODE_PLACEHOLDER', code);
                    try {
                        const response = await fetch(deleteUrl, {
                            method: 'POST'
                        });
                        const result = await response.json();
                        if (response.ok) {
                            showFlashMessage(result.message, 'success');
                            row.remove();
                        } else {
                            showFlashMessage(result.message || 'Failed to delete.', 'error');
                        }
                    } catch (error) {
                        showFlashMessage('Network error. Please try again.', 'error');
                    }
                }
            } else if (target.classList.contains('btn-update')) {
                toggleEditMode(row, true);
            } else if (target.classList.contains('btn-save')) {
                await saveCourseUpdate(row);
            } else if (target.classList.contains('btn-cancel')) {
                toggleEditMode(row, false);
            }
        });
    }
    
    const toggleEditMode = (row, isEditing) => {
        const nameCell = row.querySelector('td[data-field="name"]');
        const descCell = row.querySelector('td[data-field="description"]');
        const actionsCell = row.querySelector('.action-buttons');

        if (isEditing) {
            row.dataset.originalName = nameCell.textContent;
            row.dataset.originalDescription = descCell.textContent;

            nameCell.innerHTML = `<input type="text" class="edit-input" value="${nameCell.textContent}">`;
            descCell.innerHTML = `<textarea class="edit-textarea">${descCell.textContent}</textarea>`;
            actionsCell.innerHTML = `
                <button class="btn btn-save">Save</button>
                <button class="btn btn-cancel">Cancel</button>
            `;
        } else {
            nameCell.textContent = row.dataset.originalName;
            descCell.textContent = row.dataset.originalDescription;
            actionsCell.innerHTML = `
                <button class="btn btn-update">Update</button>
                <button class="btn btn-delete">Delete</button>
            `;
        }
    };

    const saveCourseUpdate = async (row) => {
        const code = row.dataset.code;
        const nameInput = row.querySelector('td[data-field="name"] input');
        const descInput = row.querySelector('td[data-field="description"] textarea');
        const data = {
            name: nameInput.value.trim(),
            description: descInput.value.trim()
        };

        const updateUrlTemplate = coursesTable.dataset.updateUrlTemplate;
        const updateUrl = updateUrlTemplate.replace('CODE_PLACEHOLDER', code);

        try {
            const response = await fetch(updateUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            
            if (response.ok) {
                if (result.status === 'success') {
                    showFlashMessage(result.message, 'success');
                    row.dataset.originalName = data.name;
                    row.dataset.originalDescription = data.description;
                } else {
                    showFlashMessage(result.message, 'info');
                }
            } else {
                showFlashMessage(result.message, 'error');
            }
        } catch (error) {
            showFlashMessage('Network error. Please try again.', 'error');
        } finally {
            toggleEditMode(row, false);
        }
    };
});
