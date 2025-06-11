const testManager = {
    questions: [],
    userAnswers: [],
    currentQuestionIndex: -1,
    currentSectionId: null,
    timeLeft: initialDurationSeconds,
    timerInterval: null,
    questionIdToIndexMap: new Map(),
    init: async function(testId, courseCode, uniqueCode) {
        console.log("Initializing test with:", testId, courseCode, uniqueCode);
        await this.fetchAllQuestions(testId, courseCode, uniqueCode);
        const numQuestions = this.questions.length;
        this.userAnswers = new Array(numQuestions).fill(null);
        this.questions.forEach((q, index) => {
            this.userAnswers[index] = {
                questionDbId: q.id,
                overallQuestionIndex: index,
                sectionId: q.section_id,
                status: 'not_visited',
                selectedOption: null,
                writtenAnswer: '',
                timeSpentOnQuestion: 0
            };
            this.questionIdToIndexMap.set(q.id, index);
        });
        document.getElementById('not-visited-count').textContent = numQuestions;
        document.getElementById('not-answered-count').textContent = 0;
        document.getElementById('answered-count').textContent = 0;
        document.getElementById('marked-review-count').textContent = 0;
        document.getElementById('answered-marked-count').textContent = 0;
        this.buildQuestionPalette();
        this.attachEventListeners();
        if (numQuestions > 0) {
            if (typeof sectionsData !== 'undefined' && sectionsData.length > 0) {
                this.selectSection(sectionsData[0].section_id);
            } else {
                this.currentSectionId = this.questions[0].section_id;
                this.loadQuestionByIndex(0);
            }
        } else {
            document.getElementById('question-box-container').innerHTML = "<p>No questions available for this test.</p>";
        }
        this.startTimer();
    },

    fetchAllQuestions: async function(testId, courseCode, uniqueCode) {
        try {
            const response = await fetch(`/fetch-questions/${testId}/${courseCode}/${uniqueCode}`);
            if (!response.ok) {
                const errText = await response.text();
                console.error("Error response body:", errText);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.questions = await response.json();

            this.questions.forEach(q => {
                if (q.question_text && q.question_image) {
                    
                    const imagePlaceholderRegex = /\[IMAGE:\s*[^\]]*\]/g;

                    q.question_text = q.question_text.replace(
                        imagePlaceholderRegex,
                        `<img src="${q.question_image}" alt="Question Image">`
                    );
                }
            });
            console.log("Questions loaded and processed:", this.questions.length);
        } catch (error) {
            console.error("Failed to fetch questions:", error);
            alert("Failed to load questions. Please refresh the page.");
        }
    },


    buildQuestionPalette: function() {
        const paletteContainer = document.getElementById('question-palette-container');
        paletteContainer.innerHTML = '';
        const fragment = document.createDocumentFragment();
        sectionsData.forEach(section => {
            const sectionId = String(section.section_id);
            const sectionBox = document.createElement('div');
            sectionBox.className = 'section-box';
            sectionBox.id = `section-palette-${sectionId}`;
            if (this.currentSectionId && this.currentSectionId !== sectionId) {
                sectionBox.style.display = 'none';
            }
            const sectionTitle = document.createElement('div');
            sectionTitle.className = 'section-title';
            sectionTitle.textContent = section.section_name;
            sectionBox.appendChild(sectionTitle);
            const chooseLabel = document.createElement('div');
            chooseLabel.className = 'choose-label';
            chooseLabel.textContent = 'Choose a Question';
            sectionBox.appendChild(chooseLabel);
            const grid = document.createElement('div');
            grid.className = 'question-grid';
            this.questions.filter(q => String(q.section_id) === sectionId).forEach(q => {
                const btn = document.createElement('button');
                btn.className = 'qbtn gray-box';
                btn.textContent = q.question_number_in_section;
                btn.id = `qbtn_${q.id}`;
                btn.type = 'button';
                btn.onclick = () => this.loadQuestionByIndex(this.questionIdToIndexMap.get(q.id));
                grid.appendChild(btn);
            });
            sectionBox.appendChild(grid);
            fragment.appendChild(sectionBox);
        });
        paletteContainer.appendChild(fragment);
    },

    updateQuestionPaletteButton: function(questionDbId, newStatus) {
        const btn = document.getElementById(`qbtn_${questionDbId}`);
        if (!btn) return;
        let newClassName = 'qbtn ';
        const buttonNumberText = btn.textContent.match(/\d+/) ? btn.textContent.match(/\d+/)[0] : btn.textContent;
        btn.innerHTML = '';
        switch(newStatus) {
            case 'answered':
                newClassName += 'shield green-shield';
                btn.textContent = buttonNumberText;
                break;
            case 'not_answered':
                newClassName += 'shield red-shield';
                btn.textContent = buttonNumberText;
                break;
            case 'marked_review':
                newClassName += 'circle purple-circle';
                btn.textContent = buttonNumberText;
                break;
            case 'answered_marked_review':
                newClassName += 'purple-green-circle';
                const iconSpan = document.createElement('span');
                iconSpan.className = 'center-icon';
                iconSpan.textContent = '✓';
                btn.appendChild(iconSpan);
                btn.appendChild(document.createTextNode(` ${buttonNumberText}`));
                break;
            case 'not_visited':
                newClassName += 'box gray-box';
                btn.textContent = buttonNumberText;
                break;
            default:
                newClassName += 'box gray-box';
                btn.textContent = buttonNumberText;
        }
        btn.className = newClassName;
    },

    updateStatusCounts: function() {
        const counts = { answered: 0, not_answered: 0, not_visited: 0, marked_review: 0, answered_marked_review: 0 };
        this.userAnswers.forEach(ua => {
            if (ua && counts[ua.status] !== undefined) {
                counts[ua.status]++;
            }
        });
        document.getElementById('answered-count').textContent = counts.answered + counts.answered_marked_review;
        document.getElementById('not-answered-count').textContent = counts.not_answered;
        document.getElementById('not-visited-count').textContent = counts.not_visited;
        document.getElementById('marked-review-count').textContent = counts.marked_review + counts.answered_marked_review;
        document.getElementById('answered-marked-count').textContent = counts.answered_marked_review;
    },
    loadQuestionByIndex: function(index) {
        if (index < 0 || index >= this.questions.length) {
            console.warn("Invalid question index:", index);
            const numQuestions = this.questions.length;
            if (numQuestions > 0) {
                if (index >= numQuestions) {
                    this.currentQuestionIndex = numQuestions - 1;
                    alert("You are at the last question.");
                } else {
                    this.currentQuestionIndex = 0;
                    alert("You are at the first question.");
                }
                this._renderQuestion(this.questions[this.currentQuestionIndex]);
            }
            return;
        }
        this.currentQuestionIndex = index;
        const question = this.questions[this.currentQuestionIndex];
        const userAnswer = this.userAnswers[this.currentQuestionIndex];
        if (userAnswer.status === 'not_visited') {
            userAnswer.status = 'not_answered';
            this.updateQuestionPaletteButton(question.id, 'not_answered');
            this.updateStatusCounts();
        }
        if (this.currentSectionId !== question.section_id) {
            this.currentSectionId = question.section_id;
            this.updateSectionTabActive();
            this.showPaletteForSection(this.currentSectionId);
        }
        this._renderQuestion(question);
        this.highlightCurrentQuestionInPalette();
    },

    _renderQuestion: function(question) {
    document.getElementById('question-type-display').textContent = question.question_type;
    document.getElementById('correct-marks-display').textContent = question.correct_marks;
    document.getElementById('negative-marks-display').textContent = question.negative_marks || '0';
    document.getElementById('question-number-display').textContent = `Question No. ${question.question_number_in_section} (Overall: ${question.overall_question_index + 1})`;
    document.getElementById('question-text-area').innerHTML = question.question_text;
    document.getElementById('question-image-area').innerHTML = '';

    const optionsArea = document.getElementById('question-options-area');
    optionsArea.innerHTML = '';
    const userAnswer = this.userAnswers[this.currentQuestionIndex];
    const fragment = document.createDocumentFragment();

    if (question.question_type === 'MCQ' || question.question_type === 'MSQ') {
        const optionType = question.question_type === 'MCQ' ? 'radio' : 'checkbox';
        ['a', 'b', 'c', 'd'].forEach(optKey => {
            if (question.options && question.options[optKey]) {
                const label = document.createElement('label');
                label.className = 'option-label';
                const input = document.createElement('input');
                input.type = optionType;
                input.name = `q_${question.id}_option`;
                input.value = optKey;
                input.dataset.questionDbId = question.id;
                if (question.question_type === 'MCQ' && userAnswer.selectedOption === optKey) {
                    input.checked = true;
                } else if (question.question_type === 'MSQ' && Array.isArray(userAnswer.selectedOption) && userAnswer.selectedOption.includes(optKey)) {
                    input.checked = true;
                }
                label.appendChild(input);
                label.appendChild(document.createTextNode(` ${question.options[optKey]}`));
                fragment.appendChild(label);
                fragment.appendChild(document.createElement('br'));
            }
        });
    } else if (question.question_type === 'NAT') {
        const natContainer = document.createElement('div');
        natContainer.className = 'nat-keypad-container';

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'nat-input';
        input.placeholder = 'Enter your answer here';
        input.dataset.questionDbId = question.id;
        input.value = userAnswer.writtenAnswer || '';

        input.addEventListener('keydown', (e) => {
            if (['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Home', 'End'].includes(e.key)) {
                return;
            }
            if (e.key === '-' && e.target.selectionStart === 0 && !e.target.value.includes('-')) {
                return;
            }
            if (e.key === '.' && !e.target.value.includes('.')) {
                return;
            }
            if (/\d/.test(e.key)) {
                return;
            }
            e.preventDefault();
        });

        natContainer.appendChild(input);

        const keypad = document.createElement('div');
        keypad.className = 'keypad';

        const buttonsLayout = [
            ['Backspace'],
            ['7', '8', '9'],
            ['4', '5', '6'],
            ['1', '2', '3'],
            ['0', '.', '-'],
            ['\u2190', '\u2192'],
            ['Clear All']
        ];

        buttonsLayout.forEach(row => {
            const rowDiv = document.createElement('div');
            rowDiv.className = 'keypad-row';
            row.forEach(key => {
                const button = document.createElement('button');
                button.type = 'button';
                button.textContent = key;
                button.className = 'keypad-btn';
                if (key === 'Backspace' || key === 'Clear All') {
                    button.classList.add('keypad-btn-wide');
                }

                button.addEventListener('click', () => {
                    const start = input.selectionStart;
                    const end = input.selectionEnd;
                    const currentValue = input.value;
                    input.focus();

                    switch (key) {
                        case 'Backspace':
                            if (start > 0) {
                                input.value = currentValue.substring(0, start - 1) + currentValue.substring(end);
                                input.setSelectionRange(start - 1, start - 1);
                            }
                            break;
                        case 'Clear All':
                            input.value = '';
                            break;
                        case '\u2190': 
                            if (start > 0) {
                                input.setSelectionRange(start - 1, start - 1);
                            }
                            break;
                        case '\u2192': 
                            if (start < currentValue.length) {
                                input.setSelectionRange(start + 1, start + 1);
                            }
                            break;
                        case '.':
                            if (!currentValue.includes('.')) {
                                input.value = currentValue.slice(0, start) + key + currentValue.slice(end);
                                input.setSelectionRange(start + 1, start + 1);
                            }
                            break;
                        case '-':
                            if (start === 0 && !currentValue.includes('-')) {
                                input.value = key + currentValue;
                                input.setSelectionRange(start + 1, start + 1);
                            }
                            break;
                        default:
                            input.value = currentValue.slice(0, start) + key + currentValue.slice(end);
                            input.setSelectionRange(start + 1, start + 1);
                            break;
                    }
                });
                rowDiv.appendChild(button);
            });
            keypad.appendChild(rowDiv);
        });

        natContainer.appendChild(keypad);
        fragment.appendChild(natContainer);
    }
    optionsArea.appendChild(fragment);
   },

    lastHighlightedButtonId: null,
    highlightCurrentQuestionInPalette: function() {
        if (this.lastHighlightedButtonId) {
            const prevBtn = document.getElementById(this.lastHighlightedButtonId);
            if (prevBtn) {
                prevBtn.style.border = "1px solid #999";
            }
        }
        if (this.currentQuestionIndex !== -1) {
            const currentQuestion = this.questions[this.currentQuestionIndex];
            const currentBtnId = `qbtn_${currentQuestion.id}`;
            const currentBtn = document.getElementById(currentBtnId);
            if (currentBtn) {
                currentBtn.style.border = "2px solid #007bff";
                this.lastHighlightedButtonId = currentBtnId;
                currentBtn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                this.lastHighlightedButtonId = null;
            }
        } else {
            this.lastHighlightedButtonId = null;
        }
    },

    selectSection: function(sectionId) {
        this.currentSectionId = sectionId;
        this.updateSectionTabActive();
        this.showPaletteForSection(sectionId);
        const firstQuestionOfSectionIndex = this.questions.findIndex(q => String(q.section_id) === String(sectionId));
        if (firstQuestionOfSectionIndex !== -1) {
            this.loadQuestionByIndex(firstQuestionOfSectionIndex);
        } else {
            console.warn("No questions in selected section:", sectionId);
            document.getElementById('question-box-container').innerHTML = `<p>No questions available in section ${sectionsData.find(s=>String(s.section_id) === String(sectionId))?.section_name || sectionId}.</p>`;
            this.currentQuestionIndex = -1;
            this.highlightCurrentQuestionInPalette();
        }
    },
    
    updateSectionTabActive: function() {
        document.querySelectorAll('#section-tabs-container .tab').forEach(tab => {
            if (String(tab.dataset.sectionId) === String(this.currentSectionId)) {
                tab.classList.add('active-tab');
                tab.classList.remove('inactive-tab');
            } else {
                tab.classList.remove('active-tab');
                tab.classList.add('inactive-tab');
            }
        });
    },

    showPaletteForSection: function(sectionId) {
        document.querySelectorAll('.section-box').forEach(box => {
            if (box.id === `section-palette-${sectionId}`) {
                box.style.display = 'block';
            } else {
                box.style.display = 'none';
            }
        });
    },

    _handleSave: function(isMarkForReview = false) {
        if (this.currentQuestionIndex === -1 || this.questions.length === 0) return;
        const question = this.questions[this.currentQuestionIndex];
        const userAnswer = this.userAnswers[this.currentQuestionIndex];
        const optionsArea = document.getElementById('question-options-area');
        let answered = false;
        if (question.question_type === 'MCQ') {
            const selectedRadio = optionsArea.querySelector(`input[name="q_${question.id}_option"]:checked`);
            if (selectedRadio) {
                userAnswer.selectedOption = selectedRadio.value;
                answered = true;
            } else {
                userAnswer.selectedOption = null;
            }
        } else if (question.question_type === 'MSQ') {
            const selectedCheckboxes = Array.from(optionsArea.querySelectorAll(`input[name="q_${question.id}_option"]:checked`));
            if (selectedCheckboxes.length > 0) {
                userAnswer.selectedOption = selectedCheckboxes.map(cb => cb.value);
                answered = true;
            } else {
                userAnswer.selectedOption = [];
            }
        } else if (question.question_type === 'NAT') {
            const natInput = optionsArea.querySelector(`.nat-input[data-question-db-id="${question.id}"]`);
            if (natInput && natInput.value.trim() !== '') {
                userAnswer.writtenAnswer = natInput.value.trim();
                answered = true;
            } else {
                userAnswer.writtenAnswer = '';
            }
        }
        if (isMarkForReview) {
            userAnswer.status = answered ? 'answered_marked_review' : 'marked_review';
        } else {
            userAnswer.status = answered ? 'answered' : 'not_answered';
        }
        this.updateQuestionPaletteButton(question.id, userAnswer.status);
        this.updateStatusCounts();
        if (this.currentQuestionIndex < this.questions.length - 1) {
            this.loadQuestionByIndex(this.currentQuestionIndex + 1);
        } else {
             if (confirm("You have reached the end of the question. Do you want to go to the first question of the current section? ")) {
                let sectionToFind = this.currentSectionId;
                if (!sectionToFind && this.questions.length > 0 && this.questions[0]) {
                    sectionToFind = String(this.questions[0].section_id);
                }

                let firstQuestionIndexInSection = -1;
                if (sectionToFind) {
                    firstQuestionIndexInSection = this.questions.findIndex(q => String(q.section_id) === sectionToFind);
                }

                if (firstQuestionIndexInSection !== -1) {
                    this.loadQuestionByIndex(firstQuestionIndexInSection);
                } else if (this.questions.length > 0) {
                    this.loadQuestionByIndex(0);
                } else {
                    this.highlightCurrentQuestionInPalette();
                }
            } else {
                this.highlightCurrentQuestionInPalette();
            }
        }
        
    },

    clearResponse: function() {
        if (this.currentQuestionIndex === -1 || this.questions.length === 0) return;
        const question = this.questions[this.currentQuestionIndex];
        const userAnswer = this.userAnswers[this.currentQuestionIndex];
        const optionsArea = document.getElementById('question-options-area');
        if (question.question_type === 'MCQ' || question.question_type === 'MSQ') {
            optionsArea.querySelectorAll(`input[name="q_${question.id}_option"]:checked`).forEach(input => input.checked = false);
            userAnswer.selectedOption = question.question_type === 'MSQ' ? [] : null;
        } else if (question.question_type === 'NAT') {
            const natInput = optionsArea.querySelector(`.nat-input[data-question-db-id="${question.id}"]`);
            if (natInput) natInput.value = '';
            userAnswer.writtenAnswer = '';
        }
        if (userAnswer.status === 'answered_marked_review') {
            userAnswer.status = 'marked_review';
        } else {
            userAnswer.status = 'not_answered';
        }
        this.updateQuestionPaletteButton(question.id, userAnswer.status);
        this.updateStatusCounts();
    },

    startTimer: function() {
    const timerDisplay = document.getElementById('time-left-display');
    if (!timerDisplay) {
        console.error("Timer display element not found.");
        return;
    }
    this.timerInterval = setInterval(() => {
        this.timeLeft--;
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        timerDisplay.textContent = `Time Left : ${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        if (this.timeLeft <= 0) {
            clearInterval(this.timerInterval);
            timerDisplay.textContent = "Time Up! Submitting Test...";
            document.getElementById('submit-test-btn').disabled = false;
            this.submitTest(true);
        }
    }, 1000);
},

    submitTest: async function(isAutoSubmit = false) {
    clearInterval(this.timerInterval);

    if (this.currentQuestionStartTime && this.currentQuestionIndex !== -1 && this.userAnswers[this.currentQuestionIndex]) {
        const timeSpent = (Date.now() - this.currentQuestionStartTime) 
        this.userAnswers[this.currentQuestionIndex].timeSpentOnQuestion = (this.userAnswers[this.currentQuestionIndex].timeSpentOnQuestion || 0) + timeSpent; // Accumulate if already some time was there
        this.currentQuestionStartTime = null; 
    }

    const submissionData = {
        test_id: testId, 
        answers: this.userAnswers.map(ua => ({
            question_id: ua.questionDbId,
            status_from_client: ua.status,
            selected_option: ua.selectedOption,
            written_answer: ua.writtenAnswer,
            time_spent_on_question: ua.timeSpentOnQuestion || 0
        })),
        total_time_taken: initialDurationSeconds - Math.max(0, this.timeLeft),

    };

    console.log("Submitting test data:", submissionData);

    ['submit-test-btn', 'save-next-btn', 'mark-review-next-btn', 'clear-response-btn'].forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.disabled = true;
    });
    document.querySelectorAll('.qbtn, .section-tab, .option-label input, .nat-input').forEach(el => el.disabled = true);


    try {
       const response = await fetch(`/submit-test-action/${testId}/${courseCode}/${uniqueCode}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(submissionData)
            });

        if (!response.ok) { 
                const errorText = await response.text();
                console.error("Server error response (raw):", errorText); 
                let errorMessage = `Server error (status ${response.status}). Check server logs.`;
                try {

                    const errorData = JSON.parse(errorText);
                    if (errorData && errorData.error) {
                        errorMessage = errorData.error;
                    }
                } catch (e) {
                    
                    errorMessage = `Server returned non-JSON error (status ${response.status}). Preview: ${errorText.substring(0, 150)}...`;
                }
                throw new Error(errorMessage);
            }

       const result = await response.json();
            console.log("Submission successful:", result);
            if (result.redirect_url) {
                window.location.href = result.redirect_url;
            } else {
                alert("Test submitted successfully! Result processing complete. (No redirect URL)");
            }

    }  catch (error) { 
            console.error("Failed to submit test (client-side catch):", error);
            alert(`Test submission failed: ${error.message}. Please contact support.`);
        }
},

    autoSubmit: function() {
        this.submitTest(true);
    },
    togglePopup: function(popupId, show) {
        const popup = document.getElementById(popupId);
        if (popup) {
            popup.style.display = show ? 'flex' : 'none';
            if (popupId === 'question-paper-popup' && show) {
                this.renderQuestionPaper();
            }
        }
    },
    
    renderQuestionPaper: function() {
        const container = document.getElementById('question-paper-content');
        if (!container) return;
        container.innerHTML = '';
        const fragment = document.createDocumentFragment();
        this.questions.forEach((q) => {
            const qDiv = document.createElement('div');
            qDiv.className = 'question-paper-entry';
            qDiv.innerHTML = `<strong>Q ${q.question_number_in_section} (Sec: ${sectionsData.find(s=>String(s.section_id) === String(q.section_id))?.section_name || 'N/A'}):</strong> ${q.question_text}`;
            fragment.appendChild(qDiv);
        });
        container.appendChild(fragment);
    },
  
    
    attachEventListeners: function() {
        document.getElementById('save-next-btn').onclick = () => this._handleSave(false);
        document.getElementById('mark-review-next-btn').onclick = () => this._handleSave(true);
        document.getElementById('clear-response-btn').onclick = () => this.clearResponse();
        document.getElementById('submit-test-btn').onclick = () => {
            if (confirm("Are you sure you want to submit the test?")) {
                this.submitTest();
            }
        };
        const submitTestBtn = document.getElementById('submit-test-btn');
        if (submitTestBtn) {
            submitTestBtn.onclick = () => {
                if (confirm("Are you sure you want to submit the test?")) {
                    this.submitTest();
                }
            };
        }
        document.getElementById('view-instructions-btn').onclick = () => this.togglePopup('instructions-popup', true);
        document.getElementById('view-question-paper-btn').onclick = () => this.togglePopup('question-paper-popup', true);
        
    }
};

