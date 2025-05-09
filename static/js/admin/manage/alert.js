document.addEventListener('DOMContentLoaded', () => {
  window.confirmDelete = function (title) {
    if (confirm("Are you sure you want to delete this book?")) {
      document.getElementById('deleteForm-' + title).submit();
    }
  };

  window.confirmAdd = function (event) {
    if (!confirm("Are you sure you want to add this book?")) {
      event.preventDefault();
    }
  };

  window.confirmUpdate = function (event) {
    if (!confirm("Are you sure you want to update this book?")) {
      event.preventDefault();
    }
  };

  window.showAlertAndSubmitDelete = function (code) {
    alert("You are about to delete this course.");
    document.getElementById('deleteForm-' + code).submit();
  };

  window.showAlertBeforeAdd = function (event) {
    alert("You are about to add this course.");
  };

  window.showAlertBeforeUpdate = function (event) {
    alert("You are about to update this course.");
  };
});
