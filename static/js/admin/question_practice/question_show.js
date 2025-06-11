document.addEventListener('DOMContentLoaded', function () {
    function showBootstrapAlert(message, type = 'success') {
        const alertPlaceholder = document.getElementById('alertPlaceholder');
        if (!alertPlaceholder) {
            alert(message);
            return;
        }
        const wrapper = document.createElement('div');
        wrapper.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        alertPlaceholder.prepend(wrapper);
        setTimeout(() => {
            wrapper.remove();
        }, 5000);
    }

    window.deleteQuestion = function (questionId, btn) {
        if (!confirm(`Are you sure you want to delete question ID ${questionId}?`)) return;
        fetch(`/admin/delete_question/${questionId}`, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })

        .then(res => res.json())
        .then(data => {
            if (data.success) {
                btn.closest('.question-box').remove();
                showBootstrapAlert(`Question ID ${questionId} deleted successfully.`, 'success');
            } else {
                showBootstrapAlert('Delete failed: ' + data.error, 'danger');
            }
        })
        .catch(() => {
            showBootstrapAlert('An error occurred during deletion.', 'danger');
        });
    };

    window.saveChanges = function (button, originalId) {
        const box = button.closest('.question-box');
        const editableFields = box.querySelectorAll('.editable-text, .editable-html');
        let updatedData = {};
        let currentQuestionIdInDom = originalId;

        editableFields.forEach(el => {
            const field = el.dataset.field;
            let val;

            if (el.classList.contains('editable-html')) {
                const parser = new DOMParser();
                const doc = parser.parseFromString(el.innerHTML, 'text/html');
                doc.querySelectorAll('.image-placeholder-link').forEach(placeholder => {
                    const imgUrl = placeholder.dataset.imageUrl;
                    if (imgUrl) {
                        const imgTag = doc.createElement('img');
                        imgTag.src = imgUrl;
                        imgTag.style.maxWidth = '100%';
                        imgTag.style.height = 'auto';
                        imgTag.style.display = 'block';
                        imgTag.style.margin = '10px 0';
                        placeholder.replaceWith(imgTag);
                    } else {
                        placeholder.replaceWith(doc.createTextNode(placeholder.textContent));
                    }
                });
                const imagePathSpan = box.querySelector('[data-field="image_path"]');
                if (imagePathSpan) {
                    updatedData['image_path'] = imagePathSpan.innerText.trim();
                }
                val = doc.body.innerHTML;
            } else {
                val = el.innerText.trim();
            }

            if (field === 'question_id') {
                currentQuestionIdInDom = val;
            }
            updatedData[field] = val;
        });

        fetch('/admin/update_single_question', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                original_id: originalId,
                new_id: currentQuestionIdInDom,
                updates: updatedData
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showBootstrapAlert(`Question ID ${originalId} updated successfully.`, 'success');
                if (data.new_question_id && originalId !== data.new_question_id) {
                    location.reload();
                } else {
                    const questionTextWrapper = box.querySelector('.question-content-wrapper');
                    if (questionTextWrapper) {
                        processQuestionTextForDisplay(questionTextWrapper);
                    }
                }
            } else {
                showBootstrapAlert("Update failed: " + data.error, 'danger');
                location.reload();
            }
        })
        .catch(() => {
            showBootstrapAlert('An error occurred during save changes.', 'danger');
            location.reload();
        });
    };

    const imagePreviewModal = new bootstrap.Modal(document.getElementById('imagePreviewModal'));
    const modalImage = document.getElementById('modalImage');

    window.previewImage = function (imageUrl) {
        modalImage.src = imageUrl;
        imagePreviewModal.show();
    };


    function processQuestionTextForDisplay(targetElement = null) {
        const wrappers = targetElement ? [targetElement] : document.querySelectorAll('.question-content-wrapper');
        wrappers.forEach(wrapper => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(wrapper.innerHTML, 'text/html');
            const images = doc.querySelectorAll('img');
            images.forEach(img => {
                const imageUrl = img.src;
                const imgWrapper = doc.createElement('span');
                imgWrapper.className = 'image-placeholder-link';
                imgWrapper.dataset.imageUrl = imageUrl;
                imgWrapper.textContent = '[Image: Click to View]';
                img.replaceWith(imgWrapper);
            });
            wrapper.innerHTML = doc.body.innerHTML;
        });
    }

    document.addEventListener('click', function (event) {
        if (event.target.classList.contains('image-placeholder-link')) {
            const imageUrl = event.target.dataset.imageUrl;
            if (imageUrl) {
                previewImage(imageUrl);
            } else {
                showBootstrapAlert('Image URL not found for this placeholder.', 'warning');
            }
        }
    });
    
    processQuestionTextForDisplay();
});
