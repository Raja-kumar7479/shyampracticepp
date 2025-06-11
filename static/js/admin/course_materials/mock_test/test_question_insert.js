
    let selectedTestIdForDescriptionAdd = null;
    let currentViewedTestId = null;
    let selectedTestIdForQuestionAdd = null;
    let isSectionSet = false;

    let quillEditor = null;

    const studyForm = document.getElementById('studyForm');
    const testForm = document.getElementById('testForm');
    const questionForm = document.getElementById('questionForm');
    const questionFieldsGroup = document.getElementById('questionFieldsGroup');
    const sectionIdInput = questionForm.querySelector('[name="section_id"]');
    const sectionNameInput = questionForm.querySelector('[name="section_name"]');

    const setSectionBtn = document.getElementById('setSectionBtn');
    const addQuestionSubmitBtn = document.getElementById('addQuestionSubmitBtn');
    const resetSectionBtn = document.getElementById('resetSectionBtn');

    const questionTypeSelect = document.getElementById('question_type');
    const correctOptionInput = questionForm.querySelector('[name="correct_option"]');
    const questionTextQuillContainer = document.getElementById('question_text_editor_quill');
    const questionImageInput = document.getElementById('question_image_url');
    const optionInputs = document.querySelectorAll('.option-input');
    const insertImageBtn = document.getElementById('insertImageBtn');

    function initializeQuill() {
        if (!quillEditor && questionTextQuillContainer && !questionFieldsGroup.classList.contains('hidden')) {
            quillEditor = new Quill(questionTextQuillContainer, {
                theme: 'snow',
                placeholder: 'Write your question here...',
                modules: {
                    toolbar: [
                        [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        ['blockquote', 'code-block'],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        [{ 'script': 'sub'}, { 'script': 'super' }],
                        [{ 'indent': '-1'}, { 'indent': '+1' }],
                        [{ 'direction': 'rtl' }],
                        [{ 'size': ['small', false, 'large', 'huge'] }],
                        [{ 'color': [] }, { 'background': [] }],
                        [{ 'font': [] }],
                        [{ 'align': [] }],
                        ['link'],
                        ['clean']
                    ]
                }
            });
        }
    }

    function showAlert(message, type = 'success') {
        const alertPlaceholder = document.getElementById('alertPlaceholder');
        const wrapper = document.createElement('div');
        wrapper.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        alertPlaceholder.append(wrapper);
        setTimeout(() => {
            wrapper.remove();
        }, 5000);
    }

    async function fetchMaterials() {
        try {
            const res = await fetch('api/study-materials');
            const data = await res.json();
            const table = document.querySelector('#materialsTable tbody');
            table.innerHTML = '';
            data.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td contenteditable="true" data-original-value="${item.name}" onblur="handleInlineUpdate(${item.id}, 'name', this, 'study_material')">${item.name}</td>
                    <td contenteditable="true" data-original-value="${item.code}" onblur="handleInlineUpdate(${item.id}, 'code', this, 'study_material')">${item.code}</td>
                    <td contenteditable="true" data-original-value="${item.status}" onblur="handleInlineUpdate(${item.id}, 'status', this, 'study_material')">${item.status}</td>
                    <td contenteditable="true" data-original-value="${item.label}" onblur="handleInlineUpdate(${item.id}, 'label', this, 'study_material')">${item.label}</td>
                    <td contenteditable="true" data-original-value="${item.stream}" onblur="handleInlineUpdate(${item.id}, 'stream', this, 'study_material')">${item.stream}</td>
                    <td class="test-id-cell">${item.test_id}</td>
                    <td contenteditable="true" data-original-value="${item.test_key}" onblur="handleInlineUpdate(${item.id}, 'test_key', this, 'study_material')">${item.test_key}</td>
                    <td contenteditable="true" data-original-value="${item.test_code}" onblur="handleInlineUpdate(${item.id}, 'test_code', this, 'study_material')">${item.test_code}</td>
                    <td><button onclick="handleDelete(${item.id}, 'study_material')" class="btn btn-sm btn-danger">Delete</button></td>
                    <td><button onclick="initAddDescription('${item.test_id}')" class="btn btn-sm btn-info">Add Description</button></td>
                `;
                table.appendChild(row);
            });
        } catch (error) {
            console.error('Error fetching study materials:', error);
            showAlert('Failed to load study materials.', 'danger');
        }
    }

    async function fetchAllDescriptions() {
        currentViewedTestId = null;
        document.getElementById('selectedTestId').innerText = 'Viewing All';
        document.getElementById('currentTestIdForDescAdd').innerText = 'selected Study Material';
        document.getElementById('addTestDescriptionBtn').disabled = true;

        try {
            const res = await fetch(`api/test-descriptions`);
            const data = await res.json();
            const table = document.querySelector('#descriptionTable tbody');
            table.innerHTML = '';
            if (data.length === 0) {
                table.innerHTML = '<tr><td colspan="10" class="text-center">No test descriptions found.</td></tr>';
            } else {
                data.forEach(d => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${d.test_id}</td>
                        <td contenteditable="true" data-original-value="${d.test_number}" onblur="handleInlineUpdate(${d.id}, 'test_number', this, 'test_description')">${d.test_number}</td>
                        <td contenteditable="true" data-original-value="${d.subject_title}" onblur="handleInlineUpdate(${d.id}, 'subject_title', this, 'test_description')">${d.subject_title}</td>
                        <td contenteditable="true" data-original-value="${d.subject_subtitle || ''}" onblur="handleInlineUpdate(${d.id}, 'subject_subtitle', this, 'test_description')">${d.subject_subtitle || ''}</td>
                        <td contenteditable="true" data-original-value="${d.year || ''}" onblur="handleInlineUpdate(${d.id}, 'year', this, 'test_description')">${d.year || ''}</td>
                        <td contenteditable="true" data-original-value="${d.total_questions}" onblur="handleInlineUpdate(${d.id}, 'total_questions', this, 'test_description')">${d.total_questions}</td>
                        <td contenteditable="true" data-original-value="${d.total_marks}" onblur="handleInlineUpdate(${d.id}, 'total_marks', this, 'test_description')">${d.total_marks}</td>
                        <td contenteditable="true" data-original-value="${d.total_duration_minutes}" onblur="handleInlineUpdate(${d.id}, 'total_duration_minutes', this, 'test_description')">${d.total_duration_minutes}</td>
                        <td><button onclick="handleDelete(${d.id}, 'test_description')" class="btn btn-sm btn-danger">Delete</button></td>
                        <td><button onclick="viewQuestionsByTestId('${d.test_id}')" class="btn btn-sm btn-primary">View/Add Questions</button></td>
                    `;
                    table.appendChild(row);
                });
            }
        } catch (error) {
            console.error('Error fetching all test descriptions:', error);
            showAlert('Failed to load all test descriptions.', 'danger');
        }
    }

    async function viewDescriptionsByTestId(testId) {
        selectedTestIdForDescriptionAdd = testId;
        currentViewedTestId = testId;
        document.getElementById('selectedTestId').innerText = testId;
        document.getElementById('currentTestIdForDescAdd').innerText = testId;
        document.getElementById('addTestDescriptionBtn').disabled = false;

        selectedTestIdForQuestionAdd = null;
        document.getElementById('selectedTestIdForQuestion').innerText = 'Select a Test ID';
        document.getElementById('currentQuestionsCount').innerText = '0';
        document.getElementById('maxAllowedQuestions').innerText = '0';
        setQuestionFormPhase('initial');
        document.querySelector('#questionsTable tbody').innerHTML = '<tr><td colspan="19" class="text-center">Select a Test ID from Test Descriptions to view/add questions.</td></tr>';

        try {
            const res = await fetch(`/api/test-descriptions/${testId}`);
            const data = await res.json();
            const existingNumbers = data.map(d => d.test_number);
            let nextTestNumber = 1;
            if (existingNumbers.length > 0) {
                nextTestNumber = Math.max(...existingNumbers) + 1;
            }
            document.querySelector('#testForm input[name="test_number"]').value = nextTestNumber;
        } catch (error) {
            console.error('Error suggesting next test number:', error);
            document.querySelector('#testForm input[name="test_number"]').value = '';
        }

        try {
            const res = await fetch(`api/test-descriptions/${testId}`);
            const data = await res.json();
            const table = document.querySelector('#descriptionTable tbody');
            table.innerHTML = '';
            if (data.length === 0) {
                table.innerHTML = '<tr><td colspan="10" class="text-center">No test descriptions found for this Study Material.</td></tr>';
            } else {
                data.forEach(d => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${d.test_id}</td>
                        <td contenteditable="true" data-original-value="${d.test_number}" onblur="handleInlineUpdate(${d.id}, 'test_number', this, 'test_description')">${d.test_number}</td>
                        <td contenteditable="true" data-original-value="${d.subject_title}" onblur="handleInlineUpdate(${d.id}, 'subject_title', this, 'test_description')">${d.subject_title}</td>
                        <td contenteditable="true" data-original-value="${d.subject_subtitle || ''}" onblur="handleInlineUpdate(${d.id}, 'subject_subtitle', this, 'test_description')">${d.subject_subtitle || ''}</td>
                        <td contenteditable="true" data-original-value="${d.year || ''}" onblur="handleInlineUpdate(${d.id}, 'year', this, 'test_description')">${d.year || ''}</td>
                        <td contenteditable="true" data-original-value="${d.total_questions}" onblur="handleInlineUpdate(${d.id}, 'total_questions', this, 'test_description')">${d.total_questions}</td>
                        <td contenteditable="true" data-original-value="${d.total_marks}" onblur="handleInlineUpdate(${d.id}, 'total_marks', this, 'test_description')">${d.total_marks}</td>
                        <td contenteditable="true" data-original-value="${d.total_duration_minutes}" onblur="handleInlineUpdate(${d.id}, 'total_duration_minutes', this, 'test_description')">${d.total_duration_minutes}</td>
                        <td><button onclick="handleDelete(${d.id}, 'test_description')" class="btn btn-sm btn-danger">Delete</button></td>
                        <td><button onclick="viewQuestionsByTestId('${d.test_id}')" class="btn btn-sm btn-primary">View/Add Questions</button></td>
                    `;
                    table.appendChild(row);
                });
            }
        } catch (error) {
            console.error('Error fetching test descriptions:', error);
            showAlert('Failed to load test descriptions.', 'danger');
        }
    }

    async function fetchTestQuestions(testId) {
        document.getElementById('selectedTestIdForQuestion').innerText = testId;
        selectedTestIdForQuestionAdd = testId;
        try {
            const res = await fetch(`api/test-questions/${testId}`);
            const data = await res.json();
            const table = document.querySelector('#questionsTable tbody');
            table.innerHTML = '';
            document.getElementById('currentQuestionsCount').innerText = data.current_count;
            document.getElementById('maxAllowedQuestions').innerText = data.max_allowed;

            if (data.questions.length === 0) {
                table.innerHTML = '<tr><td colspan="19" class="text-center">No questions found for this Test ID.</td></tr>';
            } else {
                data.questions.forEach(q => {
                    let displayedQuestionHtml = q.question_text || "";
                    if (q.question_image) {
                        displayedQuestionHtml = displayedQuestionHtml.replace(/\[IMAGE: view\]/g, `<img src="${q.question_image}" class="question-img" alt="Question Image">`);
                    }

                    const row = document.createElement('tr');
                    const originalQuestionText = q.question_text || "";

                    row.innerHTML = `
                        <td>${q.test_id}</td>
                        <td contenteditable="true" data-original-value="${q.section_id}" onblur="handleInlineUpdate(${q.id}, 'section_id', this, 'test_question')">${q.section_id}</td>
                        <td contenteditable="true" data-original-value="${q.section_name}" onblur="handleInlineUpdate(${q.id}, 'section_name', this, 'test_question')">${q.section_name}</td>
                        <td>${q.question_number}</td>
                        <td contenteditable="true" data-original-value="${q.question_type}" onblur="handleInlineUpdate(${q.id}, 'question_type', this, 'test_question')">${q.question_type}</td>
                        <td contenteditable="true" data-original-value="${escapeHtmlAttribute(originalQuestionText)}" onblur="handleInlineUpdate(${q.id}, 'question_text', this, 'test_question')" data-field="question_text"></td>
                        <td><a href="${q.question_image}" target="_blank">${q.question_image ? 'View' : 'N/A'}</a></td>
                        <td contenteditable="true" data-original-value="${q.option_a || ''}" onblur="handleInlineUpdate(${q.id}, 'option_a', this, 'test_question')">${q.option_a || ''}</td>
                        <td contenteditable="true" data-original-value="${q.option_b || ''}" onblur="handleInlineUpdate(${q.id}, 'option_b', this, 'test_question')">${q.option_b || ''}</td>
                        <td contenteditable="true" data-original-value="${q.option_c || ''}" onblur="handleInlineUpdate(${q.id}, 'option_c', this, 'test_question')">${q.option_c || ''}</td>
                        <td contenteditable="true" data-original-value="${q.option_d || ''}" onblur="handleInlineUpdate(${q.id}, 'option_d', this, 'test_question')">${q.option_d || ''}</td>
                        <td contenteditable="true" data-original-value="${q.correct_option}" onblur="handleInlineUpdate(${q.id}, 'correct_option', this, 'test_question')">${q.correct_option}</td>
                        <td contenteditable="true" data-original-value="${q.correct_marks}" onblur="handleInlineUpdate(${q.id}, 'correct_marks', this, 'test_question')">${q.correct_marks}</td>
                        <td contenteditable="true" data-original-value="${q.negative_marks}" onblur="handleInlineUpdate(${q.id}, 'negative_marks', this, 'test_question')">${q.negative_marks}</td>
                        <td contenteditable="true" data-original-value="${q.question_level}" onblur="handleInlineUpdate(${q.id}, 'question_level', this, 'test_question')">${q.question_level}</td>
                        <td contenteditable="true" data-original-value="${q.answer_text || ''}" onblur="handleInlineUpdate(${q.id}, 'answer_text', this, 'test_question')">${q.answer_text || ''}</td>
                        <td><a href="${q.answer_link}" target="_blank">${q.answer_link ? 'View' : 'N/A'}</a></td>
                        <td><a href="${q.answer_image}" target="_blank">${q.answer_image ? 'View' : 'N/A'}</a></td>
                        <td><button onclick="handleDelete(${q.id}, 'test_question')" class="btn btn-sm btn-danger">Delete</button></td>
                    `;
                    row.cells[5].innerHTML = displayedQuestionHtml;
                    table.appendChild(row);
                });
            }
        } catch (error) {
            console.error('Error fetching test questions:', error);
            showAlert('Failed to load test questions.', 'danger');
        }
    }

    function escapeHtmlAttribute(text) {
        return text.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }


    function initAddDescription(testId) {
        selectedTestIdForDescriptionAdd = testId;
        document.getElementById('currentTestIdForDescAdd').innerText = testId;
        document.getElementById('addTestDescriptionBtn').disabled = false;
        viewDescriptionsByTestId(testId);
    }

    function viewQuestionsByTestId(testId) {
        selectedTestIdForQuestionAdd = testId;
        document.getElementById('selectedTestIdForQuestion').innerText = testId;
        setQuestionFormPhase('initial');
        fetchTestQuestions(testId);
    }

    function setQuestionFormPhase(phase) {
        if (phase === 'initial') {
            sectionIdInput.disabled = false;
            sectionNameInput.disabled = false;
            sectionIdInput.value = '';
            sectionNameInput.value = '';

            questionFieldsGroup.classList.add('hidden');

            if (quillEditor) {
                quillEditor.setText('');
            }

            questionFieldsGroup.querySelectorAll('input:not(#question_image_url), select, textarea').forEach(field => {
                field.disabled = true;
            });
            insertImageBtn.disabled = true;

            setSectionBtn.classList.remove('hidden');
            addQuestionSubmitBtn.classList.add('hidden');
            resetSectionBtn.classList.add('hidden');

            isSectionSet = false;
            questionForm.reset();
            questionTypeSelect.dispatchEvent(new Event('change'));

        } else if (phase === 'section_set') {
            sectionIdInput.disabled = true;
            sectionNameInput.disabled = true;

            questionFieldsGroup.classList.remove('hidden');

            setTimeout(() => {
                initializeQuill();
            }, 100);

            questionFieldsGroup.querySelectorAll('input:not(#question_image_url), select, textarea').forEach(field => {
                field.disabled = false;
            });
            insertImageBtn.disabled = false;

            setSectionBtn.classList.add('hidden');
            addQuestionSubmitBtn.classList.remove('hidden');
            resetSectionBtn.classList.remove('hidden');

            isSectionSet = true;
            resetQuestionSpecificFields();
            questionTypeSelect.dispatchEvent(new Event('change'));
        }
    }

    function resetQuestionSpecificFields() {
        const currentSectionId = sectionIdInput.value;
        const currentSectionName = sectionNameInput.value;

        if (quillEditor) {
            quillEditor.setText('');
            quillEditor.focus();
        }

        questionImageInput.value = '';
        optionInputs.forEach(input => input.value = '');
        correctOptionInput.value = '';
        questionForm.querySelector('[name="correct_marks"]').value = '';
        questionForm.querySelector('[name="negative_marks"]').value = '';
        questionForm.querySelector('[name="question_level"]').value = 'Medium';
        questionForm.querySelector('[name="answer_text"]').value = '';
        questionForm.querySelector('[name="answer_link"]').value = '';
        questionForm.querySelector('[name="answer_image"]').value = '';

        questionTypeSelect.value = '';
        questionTypeSelect.dispatchEvent(new Event('change'));

        sectionIdInput.value = currentSectionId;
        sectionNameInput.value = currentSectionName;
        sectionIdInput.disabled = true;
        sectionNameInput.disabled = true;
    }


    async function handleInlineUpdate(id, field, element, type) {
        const oldValue = element.dataset.originalValue;
        let newValue;

        if (type === 'test_question' && field === 'question_text') {
            newValue = element.innerHTML.trim();
            if (questionImageInput.value) {
                newValue = newValue.replace(/<img src="[^"]+" class="question-img" alt="Question Image">/g, '[IMAGE: view]');
            }
        } else {
            newValue = element.innerText.trim();
        }

        let isChanged = true;
        if (type === 'test_question' && field === 'question_text') {
            const normalizedOld = new DOMParser().parseFromString(oldValue, 'text/html').body.innerHTML.replace(/\s+/g, ' ').trim();
            const normalizedNew = new DOMParser().parseFromString(newValue, 'text/html').body.innerHTML.replace(/\s+/g, ' ').trim();
            if (normalizedNew === normalizedOld) {
                isChanged = false;
            }
        } else if (newValue === oldValue) {
            isChanged = false;
        }

        if (!isChanged) {
            return;
        }

        if (['test_number', 'total_questions', 'total_marks', 'total_duration_minutes', 'year', 'correct_marks', 'negative_marks'].includes(field)) {
            if (newValue !== '' && isNaN(parseFloat(newValue))) {
                showAlert(`Invalid input for ${field}. Please enter a number.`, 'danger');
                if (type === 'test_question' && field === 'question_text') {
                    element.innerHTML = oldValue;
                } else {
                    element.innerText = oldValue;
                }
                return;
            }
        }

        if (!confirm(`Are you sure you want to update '${field}' to '${newValue.substring(0,100)}${newValue.length > 100 ? '...' : ''}'?`)) {
            if (type === 'test_question' && field === 'question_text') {
                element.innerHTML = oldValue;
            } else {
                element.innerText = oldValue;
            }
            return;
        }

        const url = type === 'study_material' ? `api/study-materials/update/${id}` :
                     type === 'test_description' ? `api/test-descriptions/update/${id}` :
                     `api/test-questions/update/${id}`;
        try {
            const res = await fetch(url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [field]: newValue })
            });
            const data = await res.json();
            if (res.ok) {
                showAlert(data.message);
                element.dataset.originalValue = escapeHtmlAttribute(newValue);

                if (type === 'study_material') fetchMaterials();
                else if (type === 'test_description') {
                    if (currentViewedTestId) viewDescriptionsByTestId(currentViewedTestId);
                    else fetchAllDescriptions();
                } else if (type === 'test_question' && selectedTestIdForQuestionAdd) {
                    fetchTestQuestions(selectedTestIdForQuestionAdd);
                }
            } else {
                showAlert(data.message, 'danger');
                if (type === 'test_question' && field === 'question_text') {
                    element.innerHTML = oldValue;
                } else {
                    element.innerText = oldValue;
                }
            }
        } catch (error) {
            console.error(`Error updating ${type}:`, error);
            showAlert(`Failed to update ${type}.`, 'danger');
            if (type === 'test_question' && field === 'question_text') {
                element.innerHTML = oldValue;
            } else {
                element.innerText = oldValue;
            }
        }
    }

    async function handleDelete(id, type) {
        if (!confirm(`Are you sure you want to delete this ${type}? This action cannot be undone.`)) {
            return;
        }

        const url = type === 'study_material' ? `api/study-materials/delete/${id}` :
                     type === 'test_description' ? `api/test-descriptions/delete/${id}` :
                     `api/test-questions/delete/${id}`;
        try {
            const res = await fetch(url, { method: 'DELETE' });
            const data = await res.json();
            if (res.ok) {
                showAlert(data.message);
                if (type === 'study_material') fetchMaterials();
                else if (type === 'test_description') {
                    if (currentViewedTestId) viewDescriptionsByTestId(currentViewedTestId);
                    else fetchAllDescriptions();
                } else if (type === 'test_question' && selectedTestIdForQuestionAdd) {
                    fetchTestQuestions(selectedTestIdForQuestionAdd);
                }
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error(`Error deleting ${type}:`, error);
            showAlert(`Failed to delete ${type}.`, 'danger');
        }
    }

    studyForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const formData = Object.fromEntries(new FormData(this));

        if (!confirm('Are you sure you want to add this Study Material?')) {
            return;
        }

        try {
            const res = await fetch('api/study-materials/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const data = await res.json();
            if (res.ok) {
                showAlert(data.message);
                this.reset();
                fetchMaterials();
                selectedTestIdForDescriptionAdd = formData.test_id;
                document.getElementById('currentTestIdForDescAdd').innerText = formData.test_id;
                document.getElementById('addTestDescriptionBtn').disabled = false;
                viewDescriptionsByTestId(formData.test_id);
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error adding study material:', error);
            showAlert('Failed to add study material.', 'danger');
        }
    });

    testForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (!selectedTestIdForDescriptionAdd) {
            showAlert('Please select a Study Material (Test ID) first to add a Test Description, or add a new Study Material.', 'warning');
            return;
        }

        const formData = Object.fromEntries(new FormData(this));
        formData.test_id = selectedTestIdForDescriptionAdd;

        if (!confirm(`Are you sure you want to add this Test Description for Test ID: ${selectedTestIdForDescriptionAdd}?`)) {
            return;
        }

        try {
            const res = await fetch('api/test-descriptions/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const data = await res.json();
            if (res.ok) {
                showAlert(data.message);
                this.reset();
                viewDescriptionsByTestId(selectedTestIdForDescriptionAdd);
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error adding test description:', error);
            showAlert('Failed to add test description.', 'danger');
        }
    });

    questionTypeSelect.addEventListener('change', function() {
        const type = this.value;

        optionInputs.forEach(inputWrapper => {
            inputWrapper.classList.remove('hidden');
            inputWrapper.required = false;
            inputWrapper.placeholder = "Option (Optional)";
        });

        const optA = questionForm.querySelector('[name="option_a"]');
        const optB = questionForm.querySelector('[name="option_b"]');
        const optC = questionForm.querySelector('[name="option_c"]');
        const optD = questionForm.querySelector('[name="option_d"]');

        if (type === 'MCQ' || type === 'MSQ') {
            if(optA) { optA.placeholder = "Option A"; optA.required = true; optA.classList.remove('hidden'); }
            if(optB) { optB.placeholder = "Option B"; optB.required = true; optB.classList.remove('hidden'); }
            if(optC) { optC.placeholder = "Option C"; optC.required = true; optC.classList.remove('hidden'); }
            if(optD) { optD.placeholder = "Option D"; optD.required = true; optD.classList.remove('hidden'); }
        } else if (type === 'NAT') {
            optionInputs.forEach(input => {
                input.classList.add('hidden');
                input.required = false;
                input.value = '';
            });
        }

        if (type === 'MCQ') {
            correctOptionInput.placeholder = 'A, B, C, or D (single letter)';
            correctOptionInput.required = true;
        } else if (type === 'MSQ') {
            correctOptionInput.placeholder = 'e.g., AB, ACD (multiple letters, no spaces)';
            correctOptionInput.required = true;
        } else if (type === 'NAT') {
            correctOptionInput.placeholder = 'Numeric value (e.g., 20 or 20.987)';
            correctOptionInput.required = true;
        } else {
            correctOptionInput.placeholder = 'Correct Option(s)';
            correctOptionInput.required = false;
        }
        correctOptionInput.value = '';
    });

    setSectionBtn.addEventListener('click', function() {
        if (!selectedTestIdForQuestionAdd) {
            showAlert('Please select a Test ID from the Test Descriptions table to add questions.', 'warning');
            return;
        }

        const sectionId = sectionIdInput.value.trim();
        const sectionName = sectionNameInput.value.trim();

        if (!sectionId || !sectionName) {
            showAlert('Please enter both Section ID and Section Name before proceeding.', 'danger');
            return;
        }
        setQuestionFormPhase('section_set');
        showAlert('Section details set. You can now add questions to this section.', 'info');
    });

    questionForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        if (!isSectionSet) {
             showAlert('Please set the Section ID and Name first.', 'warning');
             return;
        }
        if (!selectedTestIdForQuestionAdd) {
            showAlert('No Test ID selected for adding questions.', 'warning');
            return;
        }

        const formData = Object.fromEntries(new FormData(this));
        formData.test_id = selectedTestIdForQuestionAdd;
        formData.section_id = sectionIdInput.value;
        formData.section_name = sectionNameInput.value;

        if (quillEditor) {
            formData.question_text = quillEditor.root.innerHTML;
            if (!formData.question_text.trim() || formData.question_text.trim() === '<p><br></p>') {
                showAlert('Question text is empty. Please enter content.', 'danger');
                return;
            }
        } else {
            showAlert('Quill editor not initialized. Cannot get question text.', 'danger');
            return;
        }

        const requiredFields = [
            'question_text', 'question_type', 'correct_option',
            'correct_marks', 'question_level'
        ];

        const missingFields = requiredFields.filter(field => {
            if (field === 'question_text') {
                return !formData[field].trim() || formData[field].trim() === '<p><br></p>';
            }
            return !formData[field];
        });

        if (missingFields.length > 0) {
            showAlert(`Missing required fields: ${missingFields.join(', ')}. Please fill all necessary fields.`, 'danger');
            return;
        }

        const questionType = formData.question_type;
        const correctOption = formData.correct_option.trim().toUpperCase();

        if (questionType === 'MCQ') {
            if (correctOption.length !== 1 || !['A', 'B', 'C', 'D'].includes(correctOption)) {
                showAlert('For MCQ, Correct Option must be a single letter (A, B, C, or D).', 'danger');
                return;
            }
        } else if (questionType === 'MSQ') {
            if (!/^[A-D]+$/.test(correctOption) || !correctOption.split('').every(char => ['A','B','C','D'].includes(char))) {
                showAlert('For MSQ, Correct Option must be one or more unique letters from A, B, C, D (e.g., AB, ACD). No spaces or repeats.', 'danger');
                return;
            }
            const uniqueChars = [...new Set(correctOption.split(''))];
            if (uniqueChars.length !== correctOption.length) {
                showAlert('For MSQ, Correct Option letters must be unique (e.g., A, B, AB, ACD. Not AA or ABA).', 'danger');
                return;
            }
        } else if (questionType === 'NAT') {
            if (isNaN(parseFloat(formData.correct_option.trim()))) {
                showAlert('For NAT, Correct Option must be a numeric value (e.g., 20 or 20.987).', 'danger');
                return;
            }
            formData.correct_option = formData.correct_option.trim();
        }

        if (!confirm('Are you sure you want to add this question?')) {
            return;
        }

        try {
            const res = await fetch('api/test-questions/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const data = await res.json();
            if (res.ok) {
                showAlert(data.message);
                resetQuestionSpecificFields();
                fetchTestQuestions(selectedTestIdForQuestionAdd);
            } else {
                showAlert(data.message, 'danger');
            }
        } catch (error) {
            console.error('Error adding test question:', error);
            showAlert('Failed to add test question. Check server console for errors.', 'danger');
        }
    });

    resetSectionBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to reset the section? This will clear current question fields and allow you to enter a new section ID and Name.')) {
            setQuestionFormPhase('initial');
        }
    });

    insertImageBtn.addEventListener('click', function() {
        const imageUrl = questionImageInput.value.trim();
        if (!imageUrl) {
            showAlert('Please enter an Image URL in the field before inserting.', 'warning');
            return;
        }
        if (quillEditor) {
            const range = quillEditor.getSelection(true);
            if (range) {
                quillEditor.insertText(range.index, '[IMAGE: view]', { 'class': 'image-placeholder' });
                quillEditor.setSelection(range.index + '[IMAGE: view]'.length);
            } else {
                quillEditor.insertText(0, '[IMAGE: view]', { 'class': 'image-placeholder' });
                quillEditor.setSelection('[IMAGE: view]'.length);
            }
            showAlert('Image placeholder inserted into the question text.', 'info');
        } else {
            showAlert('Quill editor is not initialized.', 'danger');
        }
    });

    document.addEventListener('DOMContentLoaded', () => {
        fetchMaterials();
        fetchAllDescriptions();
        document.querySelector('#questionsTable tbody').innerHTML = '<tr><td colspan="19" class="text-center">Select a Test ID from Test Descriptions to view/add questions.</td></tr>';
        setQuestionFormPhase('initial');
    });
