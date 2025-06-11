
    document.addEventListener('DOMContentLoaded', function() {
        const codeInput = document.getElementById('code');
        const sectionSelect = document.getElementById('section');
        const remainingFields = document.getElementById('remainingFields');
        const labelSelect = document.getElementById('label');
        const priceInput = document.getElementById('price');
        const contentTable = document.getElementById('contentTable');
        const imageModal = document.getElementById('imageModal');
        const closeImageModal = document.getElementById('closeImageModal');
        const modalImage = document.getElementById('modalImage');
        const updateImageBtn = document.getElementById('updateImageBtn');
        const deleteImageBtn = document.getElementById('deleteImageBtn');

        let currentImageContentId = null;

        function toggleRemainingFieldsAndPrice() {
            if (codeInput.value.trim() !== '' && sectionSelect.value !== '') {
                remainingFields.style.display = 'block';
            } else {
                remainingFields.style.display = 'none';
            }
            
            if (labelSelect.value === 'Free') {
                priceInput.value = '0.00';
                priceInput.disabled = true;
                priceInput.removeAttribute('required');
            } else {
                priceInput.disabled = false;
                priceInput.setAttribute('required', 'required');
            }
        }

        codeInput.addEventListener('input', toggleRemainingFieldsAndPrice);
        sectionSelect.addEventListener('change', toggleRemainingFieldsAndPrice);
        labelSelect.addEventListener('change', toggleRemainingFieldsAndPrice);

        toggleRemainingFieldsAndPrice();

        contentTable.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', function() {
                const contentId = this.dataset.id;
                const contentTitle = this.dataset.title;
                if (confirm(`Are you sure you want to delete "${contentTitle}" (ID: ${contentId})? This action cannot be undone.`)) {
                    fetch(`/delete_content/${contentId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert(data.message);
                            this.closest('tr').remove();
                        } else {
                            alert(`Error: ${data.message}`);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred during deletion.');
                    });
                }
            });
        });

        contentTable.querySelectorAll('.editable').forEach(cell => {
            cell.addEventListener('click', function() {
                if (this.querySelector('input, select, textarea')) {
                    return;
                }

                const originalText = this.textContent.trim();
                const field = this.dataset.field;
                const contentId = this.closest('tr').dataset.id;
                const row = this.closest('tr');

                const currentLabelCell = row.querySelector('[data-field="label"]');
                const currentPriceCell = row.querySelector('[data-field="price"]');
                const currentLabel = currentLabelCell.textContent.trim();
                const currentPrice = parseFloat(currentPriceCell.textContent.trim());


                let inputElement;

                if (field === 'details' || field === 'image_url') {
                    inputElement = document.createElement('textarea');
                } else if (field === 'price') {
                    inputElement = document.createElement('input');
                    inputElement.type = 'number';
                    inputElement.step = '0.01';
                } else if (field === 'label') {
                    inputElement = document.createElement('select');
                    ['Free', 'Paid'].forEach(optionValue => {
                        const option = document.createElement('option');
                        option.value = optionValue;
                        option.textContent = optionValue;
                        if (originalText === optionValue) {
                            option.selected = true;
                        }
                        inputElement.appendChild(option);
                    });
                } else if (field === 'status') {
                    inputElement = document.createElement('select');
                    ['active', 'inactive'].forEach(optionValue => {
                        const option = document.createElement('option');
                        option.value = optionValue;
                        option.textContent = optionValue;
                        if (originalText === optionValue) {
                            option.selected = true;
                        }
                        inputElement.appendChild(option);
                    });
                } else if (field === 'section') {
                    inputElement = document.createElement('select');
                    const sections = ['NOTES', 'PRACTICE BOOK', 'PYQ', 'MOCK TEST'];
                    sections.forEach(optionValue => {
                        const option = document.createElement('option');
                        option.value = optionValue;
                        option.textContent = optionValue;
                        if (originalText === optionValue) {
                            option.selected = true;
                        }
                        inputElement.appendChild(option);
                    });
                }
                else {
                    inputElement = document.createElement('input');
                    inputElement.type = 'text';
                }

                inputElement.value = originalText;
                this.innerHTML = '';
                this.appendChild(inputElement);
                inputElement.focus();

                inputElement.addEventListener('blur', function() {
                    const newValue = this.value.trim();
                    const currentCell = this.parentNode;
                    let priceToSend = currentPrice;

                    currentCell.textContent = originalText;

                    if (newValue !== originalText) {
                        if (field === 'label') {
                            if (newValue === 'Paid') {
                                let enteredPrice = prompt("Enter the price for this Paid content:");
                                if (enteredPrice === null) {
                                    return;
                                }
                                enteredPrice = parseFloat(enteredPrice);
                                if (isNaN(enteredPrice) || enteredPrice <= 0) {
                                    alert("Invalid price. Price must be a number greater than 0 for Paid content.");
                                    return;
                                }
                                priceToSend = enteredPrice;
                            } else if (newValue === 'Free') {
                                priceToSend = 0.00;
                            }
                        } else if (field === 'price' && currentLabel === 'Paid' && parseFloat(newValue) <= 0) {
                            alert("Price must be greater than 0 for Paid content.");
                            return;
                        } else if (field === 'price') {
                             priceToSend = parseFloat(newValue);
                        }

                        if (confirm(`Confirm update for "${field}" from "${originalText}" to "${newValue}"?`)) {
                            const bodyData = {
                                field: field,
                                value: newValue
                            };
                            if (field === 'label') {
                                bodyData.price = priceToSend;
                            }

                            fetch(`/update_content_field/${contentId}`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify(bodyData)
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    alert(data.message);
                                    currentCell.textContent = data.updated_field_value;

                                    const priceCell = row.querySelector('[data-field="price"]');
                                    if (priceCell && data.new_price !== undefined) {
                                        priceCell.textContent = data.new_price.toFixed(2);
                                    }

                                    const sectionIdCell = row.querySelector('[data-field="section_id"]');
                                    if (sectionIdCell && data.new_section_id) {
                                        sectionIdCell.textContent = data.new_section_id;
                                    }

                                } else {
                                    alert(`Error: ${data.message}`);
                                    currentCell.textContent = originalText;
                                }
                            })
                            .catch(error => {
                                console.error('Error:', error);
                                alert('An error occurred during update.');
                                currentCell.textContent = originalText;
                            });
                        } else {
                            currentCell.textContent = originalText;
                        }
                    } else {
                        currentCell.textContent = originalText;
                    }
                });

                inputElement.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        this.blur();
                    }
                });
            });
        });

        contentTable.querySelectorAll('.view-image-btn').forEach(button => {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                const imageUrl = this.dataset.imageUrl;
                currentImageContentId = this.dataset.contentId;
                modalImage.src = imageUrl;
                imageModal.style.display = 'flex';
            });
        });

        closeImageModal.addEventListener('click', function() {
            imageModal.style.display = 'none';
            currentImageContentId = null;
        });

        window.addEventListener('click', function(event) {
            if (event.target === imageModal) {
                imageModal.style.display = 'none';
                currentImageContentId = null;
            }
        });

        updateImageBtn.addEventListener('click', function() {
            if (!currentImageContentId) return;

            const newImageUrl = prompt("Enter new image URL:");
            if (newImageUrl !== null) {
                if (confirm(`Confirm update image URL for ID ${currentImageContentId} to "${newImageUrl}"?`)) {
                    fetch(`/update_content_field/${currentImageContentId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ field: 'image_url', value: newImageUrl })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('Image URL updated successfully!');
                            modalImage.src = newImageUrl;
                            const row = contentTable.querySelector(`tr[data-id="${currentImageContentId}"]`);
                            if (row) {
                                const imageCell = row.children[10];
                                imageCell.innerHTML = `<a href="#" class="view-image-btn" data-image-url="${newImageUrl}" data-content-id="${currentImageContentId}">View Image</a>`;
                                imageCell.querySelector('.view-image-btn').addEventListener('click', function(event) {
                                    event.preventDefault();
                                    const imageUrl = this.dataset.imageUrl;
                                    currentImageContentId = this.dataset.contentId;
                                    modalImage.src = imageUrl;
                                    imageModal.style.display = 'flex';
                                });
                            }
                        } else {
                            alert(`Error updating image: ${data.message}`);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('An error occurred during update.');
                    });
                }
            }
        });

        deleteImageBtn.addEventListener('click', function() {
            if (!currentImageContentId) return;

            if (confirm(`Are you sure you want to delete the image for ID ${currentImageContentId}? This will remove the image URL.`)) {
                fetch(`/update_content_field/${currentImageContentId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ field: 'image_url', value: '' })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Image removed successfully!');
                        imageModal.style.display = 'none';
                        const row = contentTable.querySelector(`tr[data-id="${currentImageContentId}"]`);
                        if (row) {
                            const imageCell = row.children[10];
                            imageCell.innerHTML = 'No Image';
                        }
                        currentImageContentId = null;
                    } else {
                        alert(`Error removing image: ${data.message}`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while removing the image.');
                });
            }
        });
});