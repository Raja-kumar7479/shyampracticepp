document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.querySelector('.toggle-sidebar');
  const closeBtn = document.querySelector('.close-sidebar');
  const sidebar = document.getElementById('sidebar');
  const content = document.getElementById('content');

  toggleBtn.addEventListener('click', () => {
    if (window.innerWidth <= 768) {
      sidebar.classList.toggle('show');
    } else {
      sidebar.classList.toggle('collapsed');
      content.classList.toggle('collapsed');
    }
  });

  closeBtn.addEventListener('click', () => {
    sidebar.classList.remove('show');
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
      sidebar.classList.remove('show');
    }
  });
});
