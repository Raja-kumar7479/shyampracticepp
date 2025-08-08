let answeredQuestions = 0;
let correctAnswers = 0;
let incorrectAnswers = 0;
const totalQuestions = document.querySelectorAll('.question-container').length;

function escapeHtml(text) {
    if (text === null || text === undefined) return "";
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showPerformanceSummary() {
    document.getElementById('correct-count').textContent = correctAnswers;
    document.getElementById('incorrect-count').textContent = incorrectAnswers;
    document.getElementById('performance-summary').style.display = 'block';
}

function highlightOptions(questionContainer, userSelection, correctOptionsStr) {
    const correctOptions = new Set(correctOptionsStr.split(',').map(s => s.trim()));
    const userSelections = new Set(Array.isArray(userSelection) ? userSelection : [String(userSelection)]);

    const optionLabels = questionContainer.querySelectorAll('.option-label');
    optionLabels.forEach(label => {
        const optionValue = label.dataset.optionValue;
        const isCorrect = correctOptions.has(optionValue);
        const isSelected = userSelections.has(optionValue);

        if (isCorrect) {
            label.classList.add('correct-answer');
        } else if (isSelected && !isCorrect) {
            label.classList.add('incorrect-answer');
        }
    });
}

function submitAnswer(event, questionId, questionType) {
    event.preventDefault();

    const form = event.target.closest('form');
    let selectedValues = [];

    if (questionType === 'NAT') {
        const input = document.querySelector(`input[name="selected_option_${questionId}"]`);
        if (!input.value.trim()) {
            alert("Please enter your answer.");
            return;
        }
        selectedValues = input.value.trim();
    } else {
        const checkedOptions = form.querySelectorAll(`input[name="selected_option_${questionId}"]:checked`);
        if (checkedOptions.length === 0) {
            alert("Please select at least one option.");
            return;
        }
        checkedOptions.forEach(cb => selectedValues.push(cb.value));
        if (questionType === 'MCQ') {
            selectedValues = selectedValues[0];
        }
    }

    const confidence = document.getElementById(`confidence-${questionId}`).value;
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) submitButton.disabled = true;

    const summaryDiv = document.getElementById(`summary-${questionId}`);
    summaryDiv.innerHTML = `<p>⏳ Checking your answer...</p>`;

    fetch(`/check_answer/${questionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            selected_option: selectedValues,
            confidence: confidence 
        })
    })
    .then(response => response.json())
    .then(data => {
        const questionContainer = document.getElementById(`question-${questionId}`);
        const controlsDiv = document.getElementById(`controls-${questionId}`);
        const toggleBtn = document.getElementById(`toggle-btn-${questionId}`);
        const explanationDiv = document.getElementById(`explanation-${questionId}`);

        if (data.error) {
            summaryDiv.innerHTML = `<p class="incorrect">⚠️ ${escapeHtml(data.error)}</p>`;
            return;
        }
        
        answeredQuestions++;
        if (data.is_correct) {
            correctAnswers++;
        } else {
            incorrectAnswers++;
        }

        if (answeredQuestions === totalQuestions) {
            showPerformanceSummary();
        }

        form.querySelectorAll(`input, select`).forEach(input => {
            input.disabled = true;
        });

        summaryDiv.innerHTML = data.is_correct ? `<p class="correct">✅ Correct Answer</p>` : `<p class="incorrect">❌ Incorrect.</p>`;
        
        const correctOptionHtml = `<p><strong>Correct Option(s):</strong> ${escapeHtml(data.correct_option)}</p>`;
        const answerHtml = data.answer_text ? `<div class="answer-text"><strong>Detailed Answer:</strong> ${data.answer_text}</div>` : '';
        const explanationLinkHtml = data.explanation_link ? `<p><strong>Explanation Link:</strong> <a href="${escapeHtml(data.explanation_link)}" target="_blank">View Explanation</a></p>` : '';
        explanationDiv.innerHTML = `${correctOptionHtml}${answerHtml}${explanationLinkHtml}`;

        controlsDiv.style.display = 'block';

        toggleBtn.onclick = function() {
            const isHidden = explanationDiv.style.display === 'none';
            explanationDiv.style.display = isHidden ? 'block' : 'none';
            this.textContent = isHidden ? 'Hide Explanation' : 'Show Explanation';
        };
        
        if (questionType !== 'NAT') {
            highlightOptions(questionContainer, selectedValues, data.correct_option);
        }
    })
    .catch(error => {
        console.error('Error submitting answer:', error);
        summaryDiv.innerHTML = `<p class="incorrect">⚠️ Network or server error. Please try again.</p>`;
        if (submitButton) submitButton.disabled = false;
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('report-issue-modal');
    const closeBtn = document.getElementById('report-modal-close-btn');
    const reportForm = document.getElementById('report-issue-form');
    const modalBody = document.getElementById('report-modal-body');
    const successMessage = document.getElementById('report-success-message');
    
    document.querySelectorAll('.report-issue-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            const questionId = event.target.dataset.questionId;
            if (!questionId) return;
            
            modalBody.style.display = 'block';
            successMessage.style.display = 'none';
            reportForm.reset();
            reportForm.dataset.questionId = questionId;
            document.getElementById('report-modal-feedback').textContent = '';
            document.getElementById('submit-report-btn').disabled = false;
            modal.style.display = 'block';
        });
    });

    closeBtn.onclick = () => {
        modal.style.display = 'none';
    };

    window.onclick = (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };
    
    reportForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const questionId = reportForm.dataset.questionId;
        const problemDescription = document.getElementById('report-problem-textarea').value.trim();
        const feedbackDiv = document.getElementById('report-modal-feedback');
        const submitBtn = document.getElementById('submit-report-btn');

        if (problemDescription.length < 10) {
            feedbackDiv.textContent = 'Please provide a more detailed description (at least 10 characters).';
            feedbackDiv.className = 'error';
            return;
        }

        submitBtn.disabled = true;
        feedbackDiv.textContent = 'Submitting...';
        feedbackDiv.className = '';

        fetch(`/report_issue/${questionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ problem: problemDescription })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                feedbackDiv.textContent = data.error;
                feedbackDiv.className = 'error';
                submitBtn.disabled = false;
            } else {
                modalBody.style.display = 'none';
                successMessage.style.display = 'block';

                const originalReportBtn = document.getElementById(`report-btn-${questionId}`);
                if (originalReportBtn) {
                    originalReportBtn.disabled = true;
                    originalReportBtn.textContent = 'Reported';
                }
                
                setTimeout(() => {
                    modal.style.display = 'none';
                }, 4000);
            }
        })
        .catch(error => {
            console.error('Error reporting issue:', error);
            feedbackDiv.textContent = 'A network or server error occurred. Please try again.';
            feedbackDiv.className = 'error';
            submitBtn.disabled = false;
        });
    });
});