document.addEventListener('DOMContentLoaded', function() {
    const addCourseCodeSelect = document.getElementById('addCourseCode');
    const courseNameInput = document.getElementById('name');
    const remainingFields = document.getElementById('remainingFields');
    const labelSelect = document.getElementById('label');
    const priceInput = document.getElementById('price');
    const validityField = document.getElementById('validityField');
    const validityInput = document.getElementById('validity_expires_at');
    
    const courseFilterSelect = document.getElementById('courseFilter');
    const contentTableBody = document.getElementById('contentTable').querySelector('tbody');
    const tableSpinner = document.getElementById('tableSpinner');

    const imageModal = document.getElementById('imageModal');
    const closeImageModal = document.getElementById('closeImageModal');
    const modalImage = document.getElementById('modalImage');
    const updateImageBtn = document.getElementById('updateImageBtn');
    const deleteImageBtn = document.getElementById('deleteImageBtn');
    const newImageFile = document.getElementById('newImageFile');
    let currentImageContentId = null;

    addCourseCodeSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        courseNameInput.value = selectedOption.getAttribute('data-name') || '';
        remainingFields.style.display = this.value ? 'block' : 'none';
    });

    labelSelect.addEventListener('change', function() {
        const isPaid = this.value === 'Paid';
        priceInput.disabled = !isPaid;
        validityField.style.display = isPaid ? 'block' : 'none';
        
        if (isPaid) {
            priceInput.setAttribute('required', 'required');
            validityInput.setAttribute('required', 'required');
        } else {
            priceInput.value = '0.00';
            priceInput.removeAttribute('required');
            validityInput.value = '';
            validityInput.removeAttribute('required');
        }
    });

    courseFilterSelect.addEventListener('change', async function() {
        const courseCode = this.value;
        if (!courseCode) {
            contentTableBody.innerHTML = '';
            return;
        }

        tableSpinner.style.display = 'block';
        contentTableBody.innerHTML = '';

        try {
            const response = await fetch(`/get_content_for_course/${courseCode}`);
            if (!response.ok) throw new Error(`Server responded with status: ${response.status}`);
            const contents = await response.json();
            
            if (contents.error) throw new Error(contents.error);

            if (contents.length === 0) {
                contentTableBody.innerHTML = '<tr><td colspan="16" class="text-center font-italic">No content found for this course.</td></tr>';
            } else {
                populateTable(contents);
            }
        } catch (error) {
            console.error('Fetch error:', error);
            contentTableBody.innerHTML = `<tr><td colspan="16" class="text-center text-danger"><strong>Error:</strong> ${error.message}</td></tr>`;
        } finally {
            tableSpinner.style.display = 'none';
        }
    });

    function populateTable(contents) {
        contents.forEach(content => {
            const row = contentTableBody.insertRow();
            row.dataset.id = content.id;
            const isOwner = ADMIN_ROLE === 'owner';

            const deleteButtonHtml = isOwner
                ? `<button type="button" class="btn btn-sm btn-danger delete-btn" data-id="${content.id}" data-title="${content.title}">Delete</button>`
                : '<button class="btn btn-sm btn-danger" disabled title="Only owners can delete">Delete</button>';

            const imageUrl = content.image_url ? `/static/${content.image_url}` : '';
            const imageViewHtml = imageUrl 
                ? `<a href="#" class="view-image-btn" data-image-url="${imageUrl}" data-content-id="${content.id}">View</a>`
                : 'No Image';

            const previewUrlHtml = content.preview_url 
                ? `<a href="${content.preview_url}" target="_blank">View Preview</a>`
                : 'N/A';
            
            const rawDate = content.validity_expires_at || '';
            const formattedDate = content.validity_expires_at ? new Date(content.validity_expires_at).toLocaleString() : 'N/A';
            const editableClass = isOwner ? 'editable owner-editable' : 'editable';

            row.innerHTML = `
                <td>${content.id}</td>
                <td data-field="code" title="Code cannot be changed">${content.code}</td>
                <td class="${editableClass}" data-field="name">${content.name}</td>
                <td class="${editableClass}" data-field="stream">${content.stream}</td>
                <td data-field="section" title="Section cannot be changed">${content.section}</td>
                <td data-field="section_id" title="Section ID is auto-generated">${content.section_id}</td>
                <td class="${editableClass}" data-field="title">${content.title}</td>
                <td class="${editableClass}" data-field="subtitle">${content.subtitle || ''}</td>
                <td class="${editableClass}" data-field="price">${(content.price || 0).toFixed(2)}</td>
                <td class="${editableClass}" data-field="details">${content.details || ''}</td>
                <td class="${editableClass}" data-field="label">${content.label}</td>
                <td class="${editableClass}" data-field="status">${content.status}</td>
                <td class="${editableClass}" data-field="validity_expires_at" data-raw-date="${rawDate}">${formattedDate}</td>
                <td>${imageViewHtml}</td>
                <td class="${editableClass}" data-field="preview_url">${previewUrlHtml}</td>
                <td>${deleteButtonHtml}</td>
            `;
        });
    }

    contentTableBody.addEventListener('click', function(e) {
        const target = e.target;
        if (target.classList.contains('delete-btn') && !target.disabled) {
            handleDelete(target);
        } else if (target.classList.contains('view-image-btn')) {
            e.preventDefault();
            handleViewImage(target);
        } else if (target.classList.contains('owner-editable')) {
            handleEdit(target);
        }
    });

    function handleDelete(button) {
        const contentId = button.dataset.id;
        const contentTitle = button.dataset.title;
        if (confirm(`Are you sure you want to permanently delete "${contentTitle}"?`)) {
            const password = prompt("To confirm deletion, please enter your admin password:");
            if (password === null) return; 

            fetch(`/delete_content/${contentId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: password })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                if (data.success) {
                    button.closest('tr').remove();
                }
            })
            .catch(err => {
                console.error('Deletion error:', err);
                alert('An unexpected error occurred during deletion.');
            });
        }
    }

    function handleEdit(cell) {
        if (cell.querySelector('input, select, textarea')) return;
        if (ADMIN_ROLE !== 'owner') return;

        const field = cell.dataset.field;
        const forbiddenFields = ['code', 'section', 'id', 'section_id'];
        if (forbiddenFields.includes(field)) {
            alert(`The '${field}' field cannot be changed.`);
            return;
        }

        const row = cell.closest('tr');
        const contentId = row.dataset.id;
        let originalValue = cell.textContent.trim();
        let inputElement;
        
        if (field === 'details') {
            inputElement = document.createElement('textarea');
            inputElement.className = 'form-control';
        } else if (field === 'price') {
            inputElement = document.createElement('input');
            inputElement.type = 'number';
            inputElement.step = '0.01';
            inputElement.className = 'form-control';
        } else if (['label', 'status'].includes(field)) {
            inputElement = document.createElement('select');
            inputElement.className = 'form-control';
            const options = {
                label: ['Free', 'Paid'],
                status: ['active', 'inactive'],
            };
            options[field].forEach(opt => {
                const option = document.createElement('option');
                option.value = opt;
                option.textContent = opt;
                if (originalValue.toLowerCase() === opt.toLowerCase()) option.selected = true;
                inputElement.appendChild(option);
            });
        } else if (field === 'validity_expires_at') {
            originalValue = cell.dataset.rawDate; // Use the raw date for the input value
            inputElement = document.createElement('input');
            inputElement.type = 'datetime-local';
            inputElement.className = 'form-control';
        }
        else if (field === 'preview_url') {
            const link = cell.querySelector('a');
            originalValue = link ? link.href : '';
            inputElement = document.createElement('input');
            inputElement.type = 'text';
            inputElement.className = 'form-control';
        }
        else {
             inputElement = document.createElement('input');
             inputElement.type = 'text';
             inputElement.className = 'form-control';
        }
        
        inputElement.value = originalValue;
        cell.innerHTML = '';
        cell.appendChild(inputElement);
        inputElement.focus();

        const saveChanges = () => {
            const newValue = inputElement.value.trim();
            if (newValue === originalValue) {
                cell.textContent = originalValue === cell.dataset.rawDate ? new Date(originalValue).toLocaleString() : originalValue;
                if(field === 'validity_expires_at' && !originalValue) cell.textContent = 'N/A';
                if(field === 'preview_url' && !originalValue) cell.innerHTML = 'N/A';
                return;
            }

            if (!confirm(`Do you want to update the '${field}'?`)) {
                cell.textContent = originalValue;
                if(field === 'preview_url') cell.innerHTML = originalValue ? `<a href="${originalValue}" target="_blank">View Preview</a>` : 'N/A';
                return;
            }
            
            const password = prompt("Please enter your admin password to confirm the update:");
            if (password === null) {
                cell.textContent = originalValue;
                if(field === 'preview_url') cell.innerHTML = originalValue ? `<a href="${originalValue}" target="_blank">View Preview</a>` : 'N/A';
                return;
            }

            fetch(`/update_content_field/${contentId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ field: field, value: newValue, password: password })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    let displayValue = data.updated_field_value;
                    if (field === 'validity_expires_at') {
                        if (data.updated_field_value) {
                            cell.dataset.rawDate = data.updated_field_value;
                            displayValue = new Date(data.updated_field_value).toLocaleString();
                        } else {
                            cell.dataset.rawDate = '';
                            displayValue = 'N/A';
                        }
                    } else if (field === 'preview_url') {
                        displayValue = data.updated_field_value ? `<a href="${data.updated_field_value}" target="_blank">View Preview</a>` : 'N/A';
                        cell.innerHTML = displayValue;
                        return;
                    }

                    cell.textContent = displayValue;

                    if (data.new_price !== undefined) {
                        row.querySelector('[data-field="price"]').textContent = data.new_price.toFixed(2);
                    }
                } else {
                    alert(`Error: ${data.message}`);
                    cell.textContent = originalValue;
                    if(field === 'preview_url') cell.innerHTML = originalValue ? `<a href="${originalValue}" target="_blank">View Preview</a>` : 'N/A';
                }
            })
            .catch(err => {
                console.error('Update error:', err);
                cell.textContent = originalValue;
                if(field === 'preview_url') cell.innerHTML = originalValue ? `<a href="${originalValue}" target="_blank">View Preview</a>` : 'N/A';
            });
        };

        inputElement.addEventListener('blur', saveChanges);
        inputElement.addEventListener('keypress', e => { if (e.key === 'Enter') inputElement.blur(); });
    }

    function handleViewImage(button) {
        currentImageContentId = button.dataset.contentId;
        modalImage.src = button.dataset.imageUrl;
        imageModal.style.display = 'flex';
    }

    const closeModal = () => {
        imageModal.style.display = 'none';
        currentImageContentId = null;
        if(newImageFile) newImageFile.value = '';
    };

    closeImageModal.addEventListener('click', closeModal);
    window.addEventListener('click', e => { if (e.target === imageModal) closeModal(); });

    if (updateImageBtn) {
        updateImageBtn.addEventListener('click', () => newImageFile.click());
    }

    if(newImageFile) {
        newImageFile.addEventListener('change', function() {
           if (!currentImageContentId || !this.files[0]) return;
            const formData = new FormData();
            formData.append('image_file', this.files[0]);

            fetch(`/update_content_image/${currentImageContentId}`, { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    alert(data.message);
                    if (data.success) {
                        modalImage.src = data.new_image_url;
                        const viewBtn = contentTableBody.querySelector(`.view-image-btn[data-content-id="${currentImageContentId}"]`);
                        if (viewBtn) viewBtn.dataset.imageUrl = data.new_image_url;
                    }
                })
                .catch(err => console.error('Image update error:', err));
        });
    }

    if (deleteImageBtn) {
        deleteImageBtn.addEventListener('click', function() {
            if (!currentImageContentId) return;
            if (confirm('Are you sure you want to delete this image?')) {
                fetch(`/delete_content_image/${currentImageContentId}`, { method: 'POST' })
                    .then(res => res.json())
                    .then(data => {
                        alert(data.message);
                        if (data.success) {
                            closeModal();
                            const row = contentTableBody.querySelector(`tr[data-id="${currentImageContentId}"]`);
                            if (row) row.querySelector('td:nth-child(14)').innerHTML = 'No Image'; // Adjust column index
                        }
                    })
                    .catch(err => console.error('Image delete error:', err));
            }
        });
    }
});