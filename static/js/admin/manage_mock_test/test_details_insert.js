$(document).ready(function() {
    let testDescriptionsTable;
    let currentQuestions = [];
    let currentQuestionIndex = 0;
    let quillEditors = {};
    let activeTestId = null;
    let activeTestDescriptionId = null;
    let activeTestKey = null;
    let activeSectionId = null;
    let activeSectionName = null;
    function selectLocalImage(editor) {
        const input = document.createElement('input');
        input.setAttribute('type', 'file');
        input.setAttribute('accept', 'image/*');
        input.click();
        input.onchange = () => {
            const file = input.files[0];
            if (file) {
                const formData = new FormData();
                formData.append('image', file);
                fetch('/api/upload-quill-image', { method: 'POST', body: formData })
                .then(response => {
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    return response.json();
                })
                .then(result => {
                    if (result.url) {
                        const range = editor.getSelection(true);
                        editor.insertEmbed(range.index, 'image', result.url);
                    } else {
                        alert('Image upload failed: ' + (result.message || 'Unknown error'));
                    }
                })
                .catch(error => {
                    console.error('Error uploading image:', error);
                    alert('Image upload failed. See console for details.');
                });
            }
        };
    }
    const initQuill = (selector) => {
        if (quillEditors[selector]) {
            quillEditors[selector].setContents([]);
            return;
        }
        const toolbarOptions = [
            [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
            ['bold', 'italic', 'underline', 'strike'],
            [{ 'script': 'sub'}, { 'script': 'super' }],
            ['blockquote', 'code-block'],
            [{ 'list': 'ordered'}, { 'list': 'bullet' }],
            ['link', 'image', 'formula'],
            [{ 'color': [] }, { 'background': [] }], ['clean']
        ];
        const editor = new Quill(`#${selector}`, {
            theme: 'snow',
            modules: {
                toolbar: {
                    container: toolbarOptions,
                    handlers: { 'image': function() { selectLocalImage(this.quill); } }
                },
                formula: true
            }
        });
        quillEditors[selector] = editor;
    };
    ['addQuestionTextEditor', 'addOptionAEditor', 'addOptionBEditor', 'addOptionCEditor', 'addOptionDEditor', 'addAnswerTextEditor', 'editQuestionTextEditor', 'editOptionAEditor', 'editOptionBEditor', 'editOptionCEditor', 'editOptionDEditor', 'editAnswerTextEditor'].forEach(initQuill);
    function showMessage(selector, type, message, isMain = false) {
        const alertDiv = $(selector);
        alertDiv.removeClass('alert-success alert-danger').addClass(`alert-${type}`).html(message).show();
        if(isMain) return;
        setTimeout(() => alertDiv.fadeOut(), 5000);
    }
    $.get('/api/content-for-tests', function(data) {
        const select = $('#testIdSelect');
        data.forEach(item => select.append(`<option value="${item.test_id}">${item.test_id} (${item.title})</option>`));
    });
    testDescriptionsTable = $('#testDescriptionsTable').DataTable({
        ajax: { url: '/api/test-descriptions/0', dataSrc: '' },
        columns: [
            { data: 'id' }, { data: 'test_key' },
            { data: 'subject_title', render: (d,t,r) => `${d} <br><small class="text-muted">${r.subject_subtitle}</small>` },
            { data: 'total_questions' }, { data: 'total_marks' }, { data: 'total_duration_minutes' },
            { data: null, searchable: false, orderable: false, render: (d,t,r) => `<button class="btn btn-warning btn-sm edit-desc-btn" data-id="${r.id}" title="Edit"><i class="fas fa-edit"></i></button> <button class="btn btn-danger btn-sm delete-desc-btn" data-id="${r.id}" title="Delete"><i class="fas fa-trash"></i></button> <button class="btn btn-info btn-sm load-questions-btn" data-id="${r.id}" data-test-id="${r.test_id}" data-test-key="${r.test_key}" title="Load Questions"><i class="fas fa-tasks"></i></button>` }
        ],
        searching: false, paging: false, info: false
    });
    $('#testIdSelect').on('change', function() {
        activeTestId = $(this).val();
        $('#questionManagementContainer').hide();
        if (activeTestId) {
            $('#addTestDescriptionTestId').val(activeTestId);
            $('#managementArea').show();
            testDescriptionsTable.ajax.url(`/api/test-descriptions/${activeTestId}`).load();
        } else {
            $('#managementArea').hide();
            testDescriptionsTable.clear().draw();
        }
    });
    $('#generateTestKeyBtn').on('click', function() {
        const array = new Uint8Array(12);
        window.crypto.getRandomValues(array);
        const key = Array.from(array, byte => ('0' + byte.toString(16)).slice(-2)).join('');
        $('#addTestKey').val(key);
    });
    $('#testDescriptionsTable tbody').on('click', '.load-questions-btn', function() {
        const data = testDescriptionsTable.row($(this).closest('tr')).data();
        activeTestDescriptionId = data.id;
        activeTestId = data.test_id;
        activeTestKey = data.test_key;
        $('#questionManagementHeader').text(`Questions for Test: ${activeTestId} / Key: ${data.test_key}`);
        $('#questionManagementContainer').show();
        $('#questionControls').hide();
        $('#sectionEntryContainer').show().find('input').val('');
    });
    $('#changeSectionBtn').on('click', function() {
        $('#questionControls').hide();
        $('#sectionEntryContainer').show().find('input').val('');
    });
    $('#loadQuestionsForSectionBtn').on('click', function() {
        activeSectionId = $('#sectionIdInput').val();
        activeSectionName = $('#sectionNameInput').val();
        if (!activeSectionId || !activeSectionName) {
            alert('Please provide both Section ID and Section Name.');
            return;
        }
        $('#sectionEntryContainer').hide();
        $('#questionControls').show();
        fetchQuestionsForDisplay();
    });
    function fetchQuestionsForDisplay() {
        if (!activeTestDescriptionId || !activeSectionId) return;
        $.get(`/api/questions/${activeTestDescriptionId}?section_id=${activeSectionId}`)
            .done(function(data) {
                currentQuestions = data.questions;
                $('#questionCountBadge').text(`Total Questions in Test: ${data.current_count} / ${data.max_allowed}`);
                if (currentQuestions.length > 0) {
                    currentQuestionIndex = 0;
                    displayQuestion(currentQuestionIndex);
                    $('#questionNavigation').show();
                    $('#noQuestionsMessage').hide();
                } else {
                    $('#questionsDisplayArea').empty();
                    $('#questionNavigation').hide();
                    $('#noQuestionsMessage').show();
                }
            })
            .fail(() => {
                $('#questionsDisplayArea').empty();
                $('#questionNavigation').hide();
                $('#noQuestionsMessage').text('Error loading questions.').show();
            });
    }
    function displayQuestion(index) {
        const question = currentQuestions[index];
        const displayArea = $('#questionsDisplayArea');
        const questionHtml = `<div class="question-display-card">
                                  <div class="card-header">
                                      <h5 class="mb-0">Question ${index + 1} of ${currentQuestions.length} (ID: ${question.id})</h5>
                                      <div>
                                          <button class="btn btn-outline-secondary btn-sm edit-question-btn" data-id="${question.id}"><i class="fas fa-edit"></i> Edit</button> 
                                          <button class="btn btn-outline-danger btn-sm delete-question-btn" data-id="${question.id}"><i class="fas fa-trash"></i> Delete</button>
                                      </div>
                                  </div>
                                  <div class="question-content-container">${question.question_text || 'N/A'}</div>
                              </div>`;
        displayArea.html(questionHtml);
        renderMathInElement(displayArea[0], { delimiters: [{left: "$$", right: "$$", display: true}, {left: "$", right: "$", display: false}], throwOnError : false });
        displayArea.find('pre').each(function(i, block) { hljs.highlightElement(block); });
        $('#prevQuestionBtn').prop('disabled', index === 0);
        $('#nextQuestionBtn').prop('disabled', index === currentQuestions.length - 1);
    }
    $('#uploadQuestionsCsvForm').on('submit', function(e) {
        e.preventDefault();
        const form = $(this), submitBtn = $('#uploadCsvSubmitBtn'), spinner = submitBtn.find('.spinner-border'), messageDiv = $('#csvUploadMessage'), errorDiv = $('#csvUploadErrors'), errorList = $('#csvErrorList');
        submitBtn.prop('disabled', true);
        spinner.show();
        messageDiv.hide();
        errorDiv.hide();
        errorList.empty();
        const formData = new FormData();
        formData.append('csv_file', $('#csvFile')[0].files[0]);
        formData.append('test_id', activeTestId);
        formData.append('test_key', activeTestKey);
        formData.append('test_description_id', activeTestDescriptionId);
        formData.append('section_id', activeSectionId);
        formData.append('section_name', activeSectionName);
        $.ajax({
            url: '/api/test-questions/upload-csv', type: 'POST', data: formData, processData: false, contentType: false,
            success: (res) => {
                let successMsg = `<strong>${res.message}</strong><br>Inserted: ${res.inserted_count}, Failed: ${res.failed_count}`;
                showMessage(messageDiv, 'success', successMsg);
                if (res.errors && res.errors.length > 0) {
                    errorDiv.show();
                    res.errors.forEach(err => errorList.append(`<li class="list-group-item list-group-item-warning">Row ${err.row_number}: ${err.message}</li>`));
                }
                fetchQuestionsForDisplay();
            },
            error: (xhr) => { showMessage(messageDiv, 'danger', xhr.responseJSON ? xhr.responseJSON.message : "An unknown error occurred."); },
            complete: () => { submitBtn.prop('disabled', false); spinner.hide(); form[0].reset(); }
        });
    });
    $('#uploadQuestionsCsvModal').on('hidden.bs.modal', function () {
        $('#csvUploadMessage').hide();
        $('#csvUploadErrors').hide();
        $('#uploadCsvSubmitBtn').prop('disabled', false).find('.spinner-border').hide();
    });
    $('#addTestDescriptionForm').on('submit', function(e) {
        e.preventDefault();
        const payload = { test_id: $('#addTestDescriptionTestId').val(), test_key: $('#addTestKey').val(), subject_title: $('#addSubjectTitle').val(), subject_subtitle: $('#addSubjectSubtitle').val(), total_questions: $('#addTotalQuestions').val(), total_marks: $('#addTotalMarks').val(), total_duration_minutes: $('#addTotalDurationMinutes').val() };
        $.ajax({
            url: '/api/test-descriptions/add', type: 'POST', contentType: 'application/json', data: JSON.stringify(payload),
            success: (res) => { showMessage('#addTestDescriptionMessage', 'success', res.message); testDescriptionsTable.ajax.reload(); $('#addTestDescriptionForm')[0].reset(); $('#addTestKey').val(''); },
            error: (xhr) => showMessage('#addTestDescriptionMessage', 'danger', xhr.responseJSON.message)
        });
    });
    $('#testDescriptionsTable tbody').on('click', '.delete-desc-btn', function() { descIdToDelete = $(this).data('id'); $('#deleteTestDescriptionModal').modal('show'); });
    $('#confirmDeleteTestDescriptionBtn').on('click', function() {
        $.ajax({
            url: `/api/test-descriptions/delete/${descIdToDelete}`, type: 'DELETE',
            success: (res) => { showMessage('#main-message-area', 'success', res.message, true); testDescriptionsTable.ajax.reload(); $('#deleteTestDescriptionModal').modal('hide'); },
            error: (xhr) => showMessage('#main-message-area', 'danger', xhr.responseJSON.message, true)
        });
    });
    $('#testDescriptionsTable tbody').on('click', '.edit-desc-btn', function() {
        const data = testDescriptionsTable.row($(this).closest('tr')).data();
        $('#editTestDescriptionId').val(data.id); $('#editTestKey').val(data.test_key); $('#editSubjectTitle').val(data.subject_title); $('#editSubjectSubtitle').val(data.subject_subtitle); $('#editTotalQuestions').val(data.total_questions); $('#editTotalMarks').val(data.total_marks); $('#editTotalDurationMinutes').val(data.total_duration_minutes);
        $('#editTestDescriptionModal').modal('show');
    });
    $('#editTestDescriptionForm').on('submit', function(e) {
        e.preventDefault();
        const id = $('#editTestDescriptionId').val();
        const payload = { subject_title: $('#editSubjectTitle').val(), subject_subtitle: $('#editSubjectSubtitle').val(), total_questions: $('#editTotalQuestions').val(), total_marks: $('#editTotalMarks').val(), total_duration_minutes: $('#editTotalDurationMinutes').val() };
        $.ajax({
            url: `/api/test-descriptions/update/${id}`, type: 'PUT', contentType: 'application/json', data: JSON.stringify(payload),
            success: (res) => { showMessage('#editTestDescriptionMessage', 'success', res.message); testDescriptionsTable.ajax.reload(); $('#editTestDescriptionModal').modal('hide'); },
            error: (xhr) => showMessage('#editTestDescriptionMessage', 'danger', xhr.responseJSON.message)
        });
    });
    $('#prevQuestionBtn').on('click', () => { if (currentQuestionIndex > 0) displayQuestion(--currentQuestionIndex); });
    $('#nextQuestionBtn').on('click', () => { if (currentQuestionIndex < currentQuestions.length - 1) displayQuestion(++currentQuestionIndex); });
    $('#addQuestionForm').on('submit', function(e) {
        e.preventDefault();
        const payload = {
            test_id: activeTestId, test_key: activeTestKey, test_description_id: activeTestDescriptionId, section_id: activeSectionId, section_name: activeSectionName,
            question_type: $('#addQuestionType').val(), question_level: $('#addQuestionLevel').val(), correct_marks: $('#addCorrectMarks').val(), negative_marks: $('#addNegativeMarks').val(),
            question_text: quillEditors.addQuestionTextEditor.root.innerHTML, option_a: quillEditors.addOptionAEditor.root.innerHTML, option_b: quillEditors.addOptionBEditor.root.innerHTML,
            option_c: quillEditors.addOptionCEditor.root.innerHTML, option_d: quillEditors.addOptionDEditor.root.innerHTML, correct_option: $('#addCorrectOption').val(),
            answer_text: quillEditors.addAnswerTextEditor.root.innerHTML, answer_link: $('#addAnswerLink').val(),
        };
        $.ajax({
            url: '/api/test-questions/add', type: 'POST', contentType: 'application/json', data: JSON.stringify(payload),
            success: (res) => {
                showMessage('#addQuestionMessage', 'success', res.message); $('#addQuestionForm')[0].reset();
                ['addQuestionTextEditor', 'addOptionAEditor', 'addOptionBEditor', 'addOptionCEditor', 'addOptionDEditor', 'addAnswerTextEditor'].forEach(id => quillEditors[id].setContents([]));
                fetchQuestionsForDisplay(); $('#addQuestionModal').modal('hide');
            },
            error: (xhr) => showMessage('#addQuestionMessage', 'danger', xhr.responseJSON.message)
        });
    });
    $(document).on('click', '.delete-question-btn', function() { questionIdToDelete = $(this).data('id'); $('#deleteQuestionModal').modal('show'); });
    $('#confirmDeleteQuestionBtn').on('click', function() {
        $.ajax({
            url: `/api/test-questions/delete/${questionIdToDelete}`, type: 'DELETE',
            success: (res) => { showMessage('#questionActionMessage', 'success', res.message); fetchQuestionsForDisplay(); $('#deleteQuestionModal').modal('hide'); },
            error: (xhr) => showMessage('#questionActionMessage', 'danger', xhr.responseJSON.message)
        });
    });
    $(document).on('click', '.edit-question-btn', function() {
        const id = $(this).data('id'); const q = currentQuestions.find(q => q.id === id);
        $('#editQuestionId').val(q.id); $('#editQuestionType').val(q.question_type); $('#editQuestionLevel').val(q.question_level); $('#editCorrectMarks').val(q.correct_marks);
        $('#editNegativeMarks').val(q.negative_marks); $('#editCorrectOption').val(q.correct_option); $('#editAnswerLink').val(q.answer_link);
        quillEditors.editQuestionTextEditor.root.innerHTML = q.question_text || ''; quillEditors.editOptionAEditor.root.innerHTML = q.option_a || ''; quillEditors.editOptionBEditor.root.innerHTML = q.option_b || '';
        quillEditors.editOptionCEditor.root.innerHTML = q.option_c || ''; quillEditors.editOptionDEditor.root.innerHTML = q.option_d || ''; quillEditors.editAnswerTextEditor.root.innerHTML = q.answer_text || '';
        $('#editQuestionModal').modal('show');
    });
    $('#editQuestionForm').on('submit', function(e) {
        e.preventDefault();
        const id = $('#editQuestionId').val();
        const payload = {
            question_type: $('#editQuestionType').val(), question_level: $('#editQuestionLevel').val(), correct_marks: $('#editCorrectMarks').val(), negative_marks: $('#editNegativeMarks').val(),
            question_text: quillEditors.editQuestionTextEditor.root.innerHTML, option_a: quillEditors.editOptionAEditor.root.innerHTML, option_b: quillEditors.editOptionBEditor.root.innerHTML,
            option_c: quillEditors.editOptionCEditor.root.innerHTML, option_d: quillEditors.editOptionDEditor.root.innerHTML, correct_option: $('#editCorrectOption').val(),
            answer_text: quillEditors.editAnswerTextEditor.root.innerHTML, answer_link: $('#editAnswerLink').val()
        };
        $.ajax({
            url: `/api/test-questions/update/${id}`, type: 'PUT', contentType: 'application/json', data: JSON.stringify(payload),
            success: (res) => { showMessage('#editQuestionMessage', 'success', res.message); fetchQuestionsForDisplay(); $('#editQuestionModal').modal('hide'); },
            error: (xhr) => showMessage('#editQuestionMessage', 'danger', xhr.responseJSON.message)
        });
    });
});