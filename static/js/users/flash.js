document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    const container = document.getElementById('flash-container');
    if (container) {
      container.classList.add('flash-hide');
      setTimeout(() => {
        container.style.display = 'none';
      }, 500);
    }
  }, 5000);
});
