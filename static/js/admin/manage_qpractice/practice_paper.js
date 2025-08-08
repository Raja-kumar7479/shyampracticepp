$(document).ready(function() {
    let quillEditors = {};
    let currentSearchResults = [];
    let currentQuestionIndex = 0;

    const toolbarOptions = [
        [{'header': [1, 2, 3, 4, 5, 6, false]}],
        ['bold', 'italic', 'underline', 'strike', 'link'],
        [{'script': 'sub'}, {'script': 'super'}],
        ['blockquote', 'code-block'],
        [{'list': 'ordered'}, {'list': 'bullet'}, {'indent': '-1'}, {'indent': '+1'}],
        [{'align': []}],
        ['image', 'video', 'formula'],
        [{'color': []}, {'background': []}],
        ['clean']
    ];

    function selectLocalImage(editor) {
        const input = document.createElement('input');
        input.setAttribute('type', 'file');
        input.setAttribute('accept', 'image/*');
        input.click();
        input.onchange = () => {
            if (!input.files[0]) return;
            const formData = new FormData();
            formData.append('image', input.files[0]);
            fetch('/api/upload-quill-image', {method: 'POST', body: formData})
                .then(response => response.json())
                .then(result => {
                    if (result.url) {
                        editor.insertEmbed(editor.getSelection(true).index, 'image', result.url);
                    } else {
                        alert('Image upload failed: ' + (result.error || 'Unknown error'));
                    }
                }).catch(error => {
                    console.error('Error uploading image:', error);
                    alert('An error occurred during image upload.');
                });
        };
    }

    const createQuill = (selectorId) => {
        if (quillEditors[selectorId]) {
            quillEditors[selectorId].setContents([]);
            return quillEditors[selectorId];
        }
        const editor = new Quill(`#${selectorId}`, {
            theme: 'snow',
            modules: {
                toolbar: { container: toolbarOptions, handlers: { 'image': function() { selectLocalImage(this.quill); } } },
                formula: true
            }
        });
        quillEditors[selectorId] = editor;
        return editor;
    };
    
    const getFullQuestionFormHtml = (prefix) => `
        <input type="hidden" id="${prefix}DbId">
        <div class="row">
            <div class="col-md-3 mb-3"><label class="form-label">Question ID (Number)</label><input type="number" id="${prefix}QuestionId" class="form-control" required></div>
            <div class="col-md-3 mb-3"><label class="form-label">Question Type</label><select id="${prefix}QuestionType" class="form-select" required><option value="">Select...</option><option>MCQ</option><option>MSQ</option><option>NAT</option></select></div>
            <div class="col-md-3 mb-3"><label class="form-label">Year</label><input type="number" id="${prefix}Year" class="form-control"></div>
            <div class="col-md-3 mb-3"><label class="form-label">Paper Set</label><input type="text" id="${prefix}PaperSet" class="form-control"></div>
        </div>
        <div class="mb-3"><label class="form-label">Question Text</label><div id="${prefix}QuestionText" class="quill-editor"></div></div>
        <div class="mb-3"><label class="form-label">Option A</label><div id="${prefix}OptionA" class="quill-editor"></div></div>
        <div class="mb-3"><label class="form-label">Option B</label><div id="${prefix}OptionB" class="quill-editor"></div></div>
        <div class="mb-3"><label class="form-label">Option C</label><div id="${prefix}OptionC" class="quill-editor"></div></div>
        <div class="mb-3"><label class="form-label">Option D</label><div id="${prefix}OptionD" class="quill-editor"></div></div>
        <div class="mb-3"><label class="form-label">Correct Option</label><input type="text" id="${prefix}CorrectOption" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">Answer Explanation</label><div id="${prefix}AnswerText" class="quill-editor"></div></div>
        <div class="mb-3"><label class="form-label">Explanation Link</label><input type="text" id="${prefix}ExplanationLink" class="form-control"></div>
        ${prefix === 'manual' ? '<button type="submit" class="btn btn-success w-100 mt-3"><i class="fas fa-plus"></i> Add This Question</button>' : ''}
    `;

    const createAllQuills = (prefix) => ['QuestionText', 'OptionA', 'OptionB', 'OptionC', 'OptionD', 'AnswerText'].forEach(f => createQuill(`${prefix}${f}`));
    
    function showMessage(selector, type, message, errors = []) {
        let errorHtml = errors.length > 0 ? '<ul>' + errors.map(e => `<li>Row ${e.row}: ${e.error}</li>`).join('') + '</ul>' : '';
        $(selector).removeClass('alert-success alert-danger alert-warning').addClass(`alert-${type}`).html(message + errorHtml).show();
    }

    function populateDropdown(selector, data, defaultOptionText) {
        const dropdown = $(selector);
        dropdown.empty().append($('<option>', { value: '', text: defaultOptionText }));
        $.each(data, (i, item) => {
            dropdown.append($('<option>', { value: item, text: item }));
        });
    }

    $.get('/api/papers/codes', (data) => {
        populateDropdown('#csvPaperCode', data, 'Select a Paper Code...');
        populateDropdown('#manualPaperCode', data, 'Select a Paper Code...');
        populateDropdown('#searchPaperCode', data, 'Select Paper Code...');
    }).fail(() => alert('Failed to load paper codes. Please refresh the page.'));

    $('#searchPaperCode').on('change', function() {
        const paperCode = $(this).val();
        const subjectDropdown = $('#searchSubject');
        const topicDropdown = $('#searchTopic');
        subjectDropdown.empty().append('<option value="">Loading...</option>').prop('disabled', true);
        topicDropdown.empty().append('<option value="">All Topics</option>').prop('disabled', true);
        if (paperCode) {
            $.get('/api/papers/subjects', { paper_code: paperCode }, (data) => {
                populateDropdown('#searchSubject', data, 'Select Subject...');
                subjectDropdown.prop('disabled', false);
            }).fail(() => alert('Failed to load subjects.'));
        }
    });

    $('#searchSubject').on('change', function() {
        const paperCode = $('#searchPaperCode').val();
        const subject = $(this).val();
        const topicDropdown = $('#searchTopic');
        topicDropdown.empty().append('<option value="">Loading...</option>').prop('disabled', true);
        if (paperCode && subject) {
            $.get('/api/papers/topics', { paper_code: paperCode, subject: subject }, (data) => {
                populateDropdown('#searchTopic', data, 'All Topics');
                topicDropdown.prop('disabled', data.length === 0);
            }).fail(() => alert('Failed to load topics.'));
        }
    });

    $('#uploadCsvForm').on('submit', function(e) {
        e.preventDefault();
        const formData = new FormData();
        formData.append('paper_code', $('#csvPaperCode').val());
        formData.append('csv_file', $('#csvFile')[0].files[0]);
        $.ajax({
            url: '/api/questions/upload-csv', type: 'POST', data: formData, processData: false, contentType: false,
            success: (res) => showMessage('#csvUploadMessage', res.failed > 0 ? 'warning' : 'success', `<b>${res.message}</b> Inserted: ${res.inserted}, Failed: ${res.failed}.`, res.errors),
            error: (xhr) => showMessage('#csvUploadMessage', 'danger', `Upload Failed: ${xhr.responseJSON?.message || 'Server error'}`)
        });
    });

    $('#setManualContextBtn').on('click', function() {
        if (!$('#manualPaperCode').val() || !$('#manualSubject').val()) {
            alert('Paper Code and Subject are required.'); return;
        }
        $('#manualContext').hide();
        $('#manualQuestionForm').html(getFullQuestionFormHtml('manual'));
        createAllQuills('manual');
        const topic = $('#manualTopic').val();
        $('#manualContextDisplay').text(`Adding to: ${$('#manualPaperCode').val()} | ${$('#manualSubject').val()} ${topic ? '| ' + topic : ''}`);
        $('#manualQuestionFormContainer').show();
    });

    $('#resetManualContextBtn').on('click', function() {
        $('#manualQuestionFormContainer').hide();
        $('#manualContext').show().find('input, select').val('');
        $('#manualAddMessage').hide();
    });

    $('#manualQuestionForm').on('submit', function(e) {
        e.preventDefault();
        const payload = {
            paper_code: $('#manualPaperCode').val(), subject: $('#manualSubject').val(), topic: $('#manualTopic').val(),
            question_id: $('#manualQuestionId').val(), question_type: $('#manualQuestionType').val(),
            year: $('#manualYear').val(), paper_set: $('#manualPaperSet').val(),
            question_text: quillEditors.manualQuestionText.root.innerHTML,
            option_a: quillEditors.manualOptionA.root.innerHTML, option_b: quillEditors.manualOptionB.root.innerHTML,
            option_c: quillEditors.manualOptionC.root.innerHTML, option_d: quillEditors.manualOptionD.root.innerHTML,
            correct_option: $('#manualCorrectOption').val(), answer_text: quillEditors.manualAnswerText.root.innerHTML,
            explanation_link: $('#manualExplanationLink').val(),
        };
        $.ajax({
            url: '/api/questions/add-manual', type: 'POST', contentType: 'application/json', data: JSON.stringify(payload),
            success: (res) => {
                showMessage('#manualAddMessage', 'success', res.message + ` (DB ID: ${res.id})`);
                $('#manualQuestionForm').trigger('reset');
                Object.values(quillEditors).forEach(editor => editor.setContents([]));
            },
            error: (xhr) => showMessage('#manualAddMessage', 'danger', `Error: ${xhr.responseJSON?.message || 'Could not add question.'}`)
        });
    });

    $('#searchBtn').on('click', function() {
        const paperCode = $('#searchPaperCode').val();
        const subject = $('#searchSubject').val();
        if (!paperCode || !subject) {
            alert('Paper Code and Subject are required.');
            return;
        }
        $.get('/api/questions/search', { paper_code: paperCode, subject: subject, topic: $('#searchTopic').val() })
        .done(function(data) {
            $('#resultsSection').show();
            $('#resultsCount').text(`${data.count} question(s) found.`);
            currentSearchResults = data.questions;
            currentQuestionIndex = 0;
            if (data.count > 0) {
                displayQuestion(0);
                $('#questionNavigation, #questionDisplayArea').show();
            } else {
                $('#questionDisplayArea').html('<div class="alert alert-info">No questions match your criteria.</div>').show();
                $('#questionNavigation').hide();
            }
        })
        .fail((xhr) => alert(`Search failed: ${xhr.responseJSON?.message || 'Server error'}`));
    });
    
    function displayQuestion(index) {
        currentQuestionIndex = index;
        const q = currentSearchResults[index];
        const questionHtml = `
            <div class="card shadow-sm">
                <div class="card-header bg-light d-flex justify-content-between align-items-center">
                    <strong>Question #${q.question_id} (DB ID: ${q.id})</strong>
                    <div>
                        <button class="btn btn-warning btn-sm edit-btn" data-index="${index}"><i class="fas fa-edit"></i> Edit</button>
                        <button class="btn btn-danger btn-sm delete-btn" data-id="${q.id}"><i class="fas fa-trash"></i> Delete</button>
                    </div>
                </div>
                <div class="card-body"><div class="question-render">${q.question_text || ''}</div></div>
            </div>`;
        $('#questionDisplayArea').html(questionHtml);
        if(window.renderMathInElement) {
            renderMathInElement(document.getElementById('questionDisplayArea'), { delimiters: [{left: "$$", right: "$$", display: true}, {left: "$", right: "$", display: false}], throwOnError: false });
        }
        if(window.hljs) {
            document.querySelectorAll('#questionDisplayArea pre').forEach(block => hljs.highlightElement(block));
        }
        $('#prevQuestionBtn').prop('disabled', index === 0);
        $('#nextQuestionBtn').prop('disabled', index === currentSearchResults.length - 1);
    }

    $('#prevQuestionBtn').on('click', () => { if (currentQuestionIndex > 0) displayQuestion(currentQuestionIndex - 1); });
    $('#nextQuestionBtn').on('click', () => { if (currentQuestionIndex < currentSearchResults.length - 1) displayQuestion(currentQuestionIndex + 1); });

    $(document).on('click', '.edit-btn', function() {
        const q = currentSearchResults[$(this).data('index')];
        $('#editQuestionForm').html(getFullQuestionFormHtml('edit'));
        createAllQuills('edit');
        $('#editDbId').val(q.id);
        $('#editQuestionId').val(q.question_id);
        $('#editQuestionType').val(q.question_type);
        $('#editYear').val(q.year);
        $('#editPaperSet').val(q.paper_set);
        quillEditors.editQuestionText.root.innerHTML = q.question_text || '';
        quillEditors.editOptionA.root.innerHTML = q.option_a || '';
        quillEditors.editOptionB.root.innerHTML = q.option_b || '';
        quillEditors.editOptionC.root.innerHTML = q.option_c || '';
        quillEditors.editOptionD.root.innerHTML = q.option_d || '';
        $('#editCorrectOption').val(q.correct_option);
        quillEditors.editAnswerText.root.innerHTML = q.answer_text || '';
        $('#editExplanationLink').val(q.explanation_link);
        $('#editQuestionModal').modal('show');
    });

    $('#saveQuestionChangesBtn').on('click', function() {
        const db_id = $('#editDbId').val();
        const original_question = currentSearchResults.find(q => q.id == db_id);
        const payload = {
            paper_code: original_question.paper_code, subject: original_question.subject, topic: original_question.topic,
            question_id: $('#editQuestionId').val(), question_type: $('#editQuestionType').val(),
            year: $('#editYear').val(), paper_set: $('#editPaperSet').val(),
            question_text: quillEditors.editQuestionText.root.innerHTML,
            option_a: quillEditors.editOptionA.root.innerHTML, option_b: quillEditors.editOptionB.root.innerHTML,
            option_c: quillEditors.editOptionC.root.innerHTML, option_d: quillEditors.editOptionD.root.innerHTML,
            correct_option: $('#editCorrectOption').val(), answer_text: quillEditors.editAnswerText.root.innerHTML,
            explanation_link: $('#editExplanationLink').val(),
        };
        $.ajax({
            url: `/api/questions/update/${db_id}`, type: 'PUT', contentType: 'application/json', data: JSON.stringify(payload),
            success: () => { $('#editQuestionModal').modal('hide'); $('#searchBtn').click(); },
            error: (xhr) => alert(`Update failed: ${xhr.responseJSON?.message || 'Server error'}`)
        });
    });
    
    $(document).on('click', '.delete-btn', function() {
        const id = $(this).data('id');
        if (confirm('Are you sure you want to delete this question?')) {
            $.ajax({
                url: `/api/questions/delete/${id}`, type: 'DELETE',
                success: () => $('#searchBtn').click(),
                error: (xhr) => alert(`Delete failed: ${xhr.responseJSON?.message || 'Server error'}`)
            });
        }
    });
});