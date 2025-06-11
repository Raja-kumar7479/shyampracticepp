document.addEventListener('DOMContentLoaded', () => {
    let quillEditor = null;
    let isSectionSet = false;
    let currentPaperCode = '';
    let currentSubject = '';
    let currentTopic = '';
    
    const form = document.getElementById('questionInsertForm');
    const questionIdInput = document.getElementById('question_id_input');
    const paperCodeInput = document.getElementById('paper_code');
    const subjectInput = document.getElementById('subject');
    const topicInput = document.getElementById('topic');
    const questionFieldsGroup = document.getElementById('question_fields_group');

    const setSectionBtn = document.getElementById('setSectionBtn');
    const resetTopicBtn = document.getElementById('resetTopicBtn');
    const resetAllBtn = document.getElementById('resetAllBtn');

    const questionTextEditorContainer = document.getElementById('question_text_editor');
    const questionTextHiddenInput = document.getElementById('question_text_hidden_input');
    const imagePathInput = document.getElementById('image_path_input');

    const questionTypeSelect = document.getElementById('question_type');
    const correctOptionMcqMsqField = document.getElementById('correct_option_mcq_msq_field');
    const correctOptionNatField = document.getElementById('correct_option_nat_field');
    const mcqMsqLabel = document.getElementById('mcq_msq_label');
    const correctOptionInput = document.querySelector('[name="correct_option"]');
    const correctOptionNatInput = document.querySelector('[name="correct_option_nat_placeholder"]');

    const optionContainers = ['option_a_container', 'option_b_container', 'option_c_container', 'option_d_container'].map(id => document.getElementById(id));
    const optionInputs = ['option_a', 'option_b', 'option_c', 'option_d'].map(id => document.getElementById(id));

    function showAlert(message, type = 'success') {
        const alertPlaceholder = document.getElementById('alertPlaceholder');
        const wrapper = document.createElement('div');
        wrapper.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        alertPlaceholder.prepend(wrapper);
        setTimeout(() => wrapper.remove(), 5000);
    }

    function imageHandler() {
        const range = quillEditor.getSelection(true);
        const imageUrl = prompt("Please enter the image URL:");
        if (imageUrl) {
            const existingImage = quillEditor.root.querySelector('img');
            if (existingImage) {
                showAlert('Only one main image is supported per question when storing it separately. Please remove the existing image first.', 'warning');
                return;
            }
            quillEditor.insertEmbed(range.index, 'image', imageUrl, Quill.sources.USER);
            quillEditor.setSelection(range.index + 1, Quill.sources.SILENT);
            showAlert('Image inserted into the question text. Its URL will be stored separately.', 'info');
            quillEditor.root.dispatchEvent(new Event('input', { bubbles: true }));
        } else {
            showAlert('Image URL not provided.', 'warning');
        }
    }

    function initializeQuill() {
        if (!quillEditor) {
            quillEditor = new Quill(questionTextEditorContainer, {
                theme: 'snow',
                placeholder: 'Write your question text here...',
                modules: {
                    toolbar: {
                        container: [
                            [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
                            ['bold', 'italic', 'underline', 'strike'],
                            ['blockquote', 'code-block'],
                            [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                            [{ 'script': 'sub' }, { 'script': 'super' }],
                            [{ 'indent': '-1' }, { 'indent': '+1' }],
                            [{ 'direction': 'rtl' }],
                            [{ 'size': ['small', false, 'large', 'huge'] }],
                            [{ 'color': [] }, { 'background': [] }],
                            [{ 'font': [] }],
                            [{ 'align': [] }],
                            ['link', 'image'],
                            ['clean']
                        ],
                        handlers: { 'image': imageHandler }
                    }
                }
            });

            quillEditor.on('text-change', () => {
                let editorContent = quillEditor.root.innerHTML;
                let imageUrl = '';
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = editorContent;
                const imgElement = tempDiv.querySelector('img');
                if (imgElement && imgElement.src) {
                    imageUrl = imgElement.src;
                    imgElement.outerHTML = '<span>[IMAGE_PLACEHOLDER]</span>';
                }
                imagePathInput.value = imageUrl;
                questionTextHiddenInput.value = tempDiv.innerHTML;
            });
        }
    }

    function setFormPhase(phase) {
        if (phase === 'initial') {
            paperCodeInput.disabled = false;
            subjectInput.disabled = false;
            topicInput.disabled = false;
            setSectionBtn.classList.remove('hidden-field');
            resetTopicBtn.classList.add('hidden-field');
            resetAllBtn.classList.add('hidden-field');
            questionFieldsGroup.classList.add('hidden-field');
            isSectionSet = false;
            if (quillEditor) {
                quillEditor.setText('');
                questionTextHiddenInput.value = '';
            }
            imagePathInput.value = '';
            form.querySelector('button[type="submit"]').disabled = true;
            currentPaperCode = '';
            currentSubject = '';
            currentTopic = '';
        } else if (phase === 'section_set') {
            paperCodeInput.disabled = true;
            subjectInput.disabled = true;
            topicInput.disabled = true;
            setSectionBtn.classList.add('hidden-field');
            resetTopicBtn.classList.remove('hidden-field');
            resetAllBtn.classList.remove('hidden-field');
            questionFieldsGroup.classList.remove('hidden-field');
            isSectionSet = true;
            initializeQuill();
            form.querySelector('button[type="submit"]').disabled = false;
            handleQuestionTypeChange();
            currentPaperCode = paperCodeInput.value;
            currentSubject = subjectInput.value;
            currentTopic = topicInput.value;
        }
    }

    function resetQuestionSpecificFields() {
        if (quillEditor) {
            quillEditor.setText('');
            questionTextHiddenInput.value = '';
        }
        imagePathInput.value = '';
        questionTypeSelect.value = 'MCQ';
        questionTypeSelect.dispatchEvent(new Event('change'));
        questionIdInput.value = '';
        document.getElementById('answer_text').value = '';
        document.getElementById('explanation_link').value = '';
        document.getElementById('paper_set').value = '';
        document.querySelector('[name="year"]').value = new Date().getFullYear();
        fetchNextQuestionId();
    }

    function handleQuestionTypeChange() {
        const type = questionTypeSelect.value;
        optionContainers.forEach(container => container.classList.remove('hidden-field'));
        optionInputs.forEach(input => input.setAttribute('required', 'required'));
        correctOptionInput.removeAttribute('required');
        correctOptionNatInput.removeAttribute('required');
        if (type === 'NAT') {
            optionContainers.forEach(container => container.classList.add('hidden-field'));
            optionInputs.forEach(input => input.removeAttribute('required'));
            correctOptionMcqMsqField.style.display = 'none';
            correctOptionNatField.style.display = 'block';
            correctOptionNatInput.setAttribute('required', 'required');
        } else {
            correctOptionMcqMsqField.style.display = 'block';
            correctOptionNatField.style.display = 'none';
            correctOptionInput.setAttribute('required', 'required');
            mcqMsqLabel.innerText = type === 'MSQ' ? "Correct Option(s) (e.g., A,B,C)" : "Correct Option (e.g., A)";
        }
        correctOptionInput.value = '';
        correctOptionNatInput.value = '';
    }

    setSectionBtn.addEventListener('click', () => {
        if (!paperCodeInput.value.trim() || !subjectInput.value.trim() || !topicInput.value.trim()) {
            showAlert('Please fill in Paper Code, Subject, and Topic.', 'danger');
            return;
        }
        setFormPhase('section_set');
        resetQuestionSpecificFields();
        showAlert('Paper Code, Subject, and Topic set. You can now add questions.', 'success');
        sessionStorage.setItem('currentPaperCode', paperCodeInput.value);
        sessionStorage.setItem('currentSubject', subjectInput.value);
        sessionStorage.setItem('currentTopic', topicInput.value);
    });

    resetTopicBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to reset the Topic and add questions for a new topic under the same Paper Code and Subject?')) {
            topicInput.value = '';
            topicInput.disabled = false;
            setSectionBtn.classList.remove('hidden-field');
            resetTopicBtn.classList.add('hidden-field');
            resetAllBtn.classList.remove('hidden-field');
            questionFieldsGroup.classList.add('hidden-field');
            isSectionSet = false;
            form.querySelector('button[type="submit"]').disabled = true;
            currentTopic = '';
            sessionStorage.removeItem('currentTopic');
            resetQuestionSpecificFields();
            showAlert('Topic reset. Please set the new topic.', 'info');
        }
    });

    resetAllBtn.addEventListener('click', () => {
        if (confirm('Are you sure you want to reset all fields (Paper Code, Subject, Topic)?')) {
            paperCodeInput.value = '';
            subjectInput.value = '';
            topicInput.value = '';
            setFormPhase('initial');
            form.reset();
            sessionStorage.removeItem('currentPaperCode');
            sessionStorage.removeItem('currentSubject');
            sessionStorage.removeItem('currentTopic');
            showAlert('All fields reset. Please set Paper Code, Subject, and Topic to begin.', 'info');
        }
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (!isSectionSet) {
            showAlert('Please set Paper Code, Subject, and Topic first.', 'warning');
            return;
        }
        if (!questionTextHiddenInput.value.trim() || questionTextHiddenInput.value.trim() === '<p><br></p>') {
            showAlert('Question text cannot be empty. Please enter content.', 'danger');
            return;
        }
        const formData = new FormData(form);
        const data = {};
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        data['paper_code'] = currentPaperCode;
        data['subject'] = currentSubject;
        data['topic'] = currentTopic;
        if (data.question_type === 'NAT') {
            data['correct_option'] = correctOptionNatInput.value.trim();
            delete data['correct_option_nat_placeholder'];
        } else {
            data['correct_option'] = correctOptionInput.value.trim();
        }
        try {
            const response = await fetch('/admin/insert_question_ajax', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                const errorResult = await response.json();
                showAlert(errorResult.error || 'An error occurred on the server.', 'danger');
            } else {
                const result = await response.json();
                if (result.success) {
                    resetQuestionSpecificFields();
                    showAlert(result.message || 'Question inserted successfully.', 'success');
                } else {
                    showAlert(result.error || 'An unknown error occurred during insertion.', 'danger');
                }
            }
        } catch (error) {
            console.error('Network or unexpected error submitting form:', error);
            showAlert('Failed to connect to server or unexpected error. Check console.', 'danger');
        }
    });

    async function fetchNextQuestionId() {
        try {
            const response = await fetch('/admin/get_next_question_id');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            document.getElementById('next_question_id_display').innerText = data.next_id;
        } catch (error) {
            console.error('Error fetching next question ID:', error);
            document.getElementById('next_question_id_display').innerText = 'Error';
            showAlert('Failed to fetch next question ID. Please check server logs.', 'danger');
        }
    }

    setFormPhase('initial');
    handleQuestionTypeChange();
    fetchNextQuestionId();
    questionTypeSelect.addEventListener('change', handleQuestionTypeChange);

    const storedPaperCode = sessionStorage.getItem('currentPaperCode');
    const storedSubject = sessionStorage.getItem('currentSubject');
    const storedTopic = sessionStorage.getItem('currentTopic');
    if (storedPaperCode && storedSubject && storedTopic) {
        paperCodeInput.value = storedPaperCode;
        subjectInput.value = storedSubject;
        topicInput.value = storedTopic;
        setFormPhase('section_set');
    }

});