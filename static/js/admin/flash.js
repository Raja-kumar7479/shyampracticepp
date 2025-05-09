
  window.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
      const flashMessages = document.querySelectorAll('.custom-flash');
      flashMessages.forEach(function (msg) {
        msg.classList.add('flash-hide');
        setTimeout(() => {
          msg.style.display = 'none';
        }, 500); // after fade
      });
    }, 5000);
  });

