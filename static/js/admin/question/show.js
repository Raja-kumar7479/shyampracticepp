document.addEventListener('DOMContentLoaded', () => {
  window.deleteQuestion = function (questionId, btn) {
    if (!confirm("Are you sure you want to delete this question?")) return;
    fetch(`/admin/delete_question/${questionId}`, {
      method: 'POST',
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        btn.closest('.question-box').remove();
      } else {
        alert('Delete failed: ' + data.error);
      }
    });
  };

  window.saveChanges = function (button, originalId) {
    const box = button.closest('.question-box');
    const editableFields = box.querySelectorAll('.editable');
    let updatedData = {};
    let newId = originalId;

    editableFields.forEach(el => {
      const field = el.dataset.field;
      let val = el.innerText.trim();
      if (field === 'question_id') {
        newId = val;
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
        new_id: newId,
        updates: updatedData
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert("Changes saved.");
        if (updatedData.image_path) {
          const imgEl = document.getElementById(`img-${originalId}`);
          if (imgEl) {
            imgEl.src = updatedData.image_path + '?v=' + new Date().getTime();
          }
        }
        location.reload();
      } else {
        alert("Update failed: " + data.error);
      }
    });
  };
});
