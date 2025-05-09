document.addEventListener('DOMContentLoaded', () => {
  function handleQuestionTypeChange() {
    const type = document.getElementById("question_type").value;
    const mcqFields = ['option_a', 'option_b', 'option_c', 'option_d'];

    mcqFields.forEach(field => {
      const container = document.getElementById(`${field}_container`);
      const input = document.getElementById(field);
      if (type === 'NAT') {
        container.style.display = 'none';
        input.removeAttribute('required');
      } else {
        container.style.display = 'block';
        input.setAttribute('required', 'required');
      }
    });

    document.getElementById("mcq_field").style.display = (type === 'MCQ' || type === 'MSQ') ? 'block' : 'none';
    document.getElementById("nat_field").style.display = (type === 'NAT') ? 'block' : 'none';

    const label = document.getElementById("mcq_label");
    label.innerText = type === 'MSQ'
      ? "Correct Option(s) (comma-separated, e.g., A,B)"
      : "Correct Option";
  }

  const select = document.getElementById("question_type");
  if (select) {
    handleQuestionTypeChange();
    select.addEventListener('change', handleQuestionTypeChange);
  }
});
