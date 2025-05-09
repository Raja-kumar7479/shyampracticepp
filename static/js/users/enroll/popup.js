document.addEventListener("DOMContentLoaded", () => {
    let popupsOpen = 0;

    function togglePopup(popupId, show = true) {
        const popup = document.getElementById(popupId);
        if (popup) {
            popup.style.display = show ? "flex" : "none";
            popupsOpen = show ? popupsOpen + 1 : Math.max(0, popupsOpen - 1);
            document.body.classList.toggle("popup-active", popupsOpen > 0);
        }
    }

    function closePopup(popupId) {
        togglePopup(popupId, false);
    }

    function showPopup(popupId) {
        togglePopup(popupId, true);
    }

    function showFlashMessage(type, message, containerId = "flash-messages") {
        const flashMessageContainer = document.getElementById(containerId);
        if (flashMessageContainer) {
            flashMessageContainer.innerHTML = `<div class="flash-message ${type}">${message}</div>`;
            setTimeout(() => (flashMessageContainer.innerHTML = ""), 5000);
        }
    }
    
    window.closePopup = closePopup;
    window.showPopup = showPopup;
    window.showFlashMessage = showFlashMessage;

    document.querySelectorAll(".popup").forEach((popup) => {
        popup.addEventListener("click", (event) => {
            if (!event.target.closest(".popup-content")) {
                event.stopPropagation();
            }
        });
    });

    document.querySelectorAll(".btn-primary, .btn-secondary, .btn-close").forEach((button) => {
        button.addEventListener("click", (event) => {
            event.stopPropagation();
            const popup = button.closest(".popup");
            if (popup) closePopup(popup.id);
        });
    });
});
