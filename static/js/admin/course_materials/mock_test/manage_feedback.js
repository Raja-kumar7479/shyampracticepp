
    document.addEventListener('DOMContentLoaded', function() {
        const truncateFeedbackBtn = document.getElementById('truncateFeedbackBtn');
        const feedbackTableBody = document.querySelector('#feedbackTable tbody');

        truncateFeedbackBtn.addEventListener('click', function() {
            if (confirm("Are you absolutely sure you want to DELETE ALL FEEDBACK DATA? This action cannot be undone.")) {
                fetch('/truncate_feedback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        feedbackTableBody.innerHTML = '<tr><td colspan="8" class="text-center">No feedback data available.</td></tr>';
                    } else {
                        alert(`Error: ${data.message}`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while trying to delete feedback data.');
                });
            }
        });
    });