function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function submitAnswer(event, questionId, questionType) {
    event.preventDefault();

    const form = event.target.closest('form');
    const resultDiv = document.getElementById(`result-${questionId}`);
    resultDiv.setAttribute("aria-live", "polite");

    let selectedValues = [];

    if (questionType === 'NAT') {
        const input = document.querySelector(`input[name="selected_option_${questionId}"]`);
        if (!input.value.trim()) {
            alert("Please enter your answer.");
            return;
        }
        selectedValues = input.value.trim();
    } else if (questionType === 'MSQ') {
        document.querySelectorAll(`input[name="selected_option_${questionId}"]:checked`)
            .forEach(cb => selectedValues.push(cb.value));
        if (selectedValues.length === 0) {
            alert("Please select at least one option.");
            return;
        }
    } else { 
        const selected = document.querySelector(`input[name="selected_option_${questionId}"]:checked`);
        if (!selected) {
            alert("Please select an option.");
            return;
        }
        selectedValues = selected.value;
    }

    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) submitButton.disabled = true;

    resultDiv.innerHTML = `<p>⏳ Checking your answer...</p>`;

    fetch(`/check_answer/${questionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selected_option: selectedValues })
    })
    .then(response => response.json())
    .then(data => {
        resultDiv.innerHTML = ''; 

        if (data.error) {
            resultDiv.innerHTML = `<p class="incorrect">⚠️ ${escapeHtml(data.error)}</p>`;
            return;
        }
        
        document.querySelectorAll(`input[name="selected_option_${questionId}"]`).forEach(input => {
            input.disabled = true;
        });

        if (data.partial_match) {
            resultDiv.innerHTML = `
                <p class="incorrect">❌ Partially Correct: ${escapeHtml(data.matched_count)} out of ${escapeHtml(data.total_correct)} correct options selected.</p>
                <p><strong>Correct Option(s):</strong> ${escapeHtml(data.correct_option)}</p>
                <p><strong>Answer:</strong> ${escapeHtml(data.answer_text || 'Not Available')}</p>
            `;
        } 
        else if (data.is_correct) {
            resultDiv.innerHTML = `
                <p class="correct">✅ Correct Answer</p>
                <p><strong>Correct Option:</strong> ${escapeHtml(data.correct_option)}</p>
                <p><strong>Answer:</strong> ${escapeHtml(data.answer_text || 'Not Available')}</p>
            `;
        } 
        else {
            resultDiv.innerHTML = `
                <p class="incorrect">❌ Incorrect.</p>
                <p><strong>Correct Option:</strong> ${escapeHtml(data.correct_option)}</p>
                <p><strong>Answer:</strong> ${escapeHtml(data.answer_text || 'Not Available')}</p>
            `;
        }
        if (data.explanation_link) {
            resultDiv.innerHTML += `<p><strong>Explanation:</strong> <a href="${escapeHtml(data.explanation_link)}" target="_blank">View Explanation</a></p>`;
        } else {
            resultDiv.innerHTML += `<p><strong>Explanation:</strong> Not Available</p>`;
        }
    })
    .catch(error => {
        console.error('Error submitting answer:', error);
        resultDiv.innerHTML = `<p class="incorrect">⚠️ Network or server error. Please try again.</p>`;

        fetch('/log_client_error', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: error.message, stack: error.stack })
        });
    })
    .finally(() => {
        if (submitButton) submitButton.disabled = false;
    });
}
