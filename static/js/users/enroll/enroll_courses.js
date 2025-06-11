document.querySelectorAll(".open-btn").forEach((button) => {
    button.addEventListener("click", () => {
        const courseCode = button.getAttribute("data-course");
        if (courseCode) {
            fetch(`/get_unique_code?course_code=${encodeURIComponent(courseCode)}`)
                .then((response) => response.json())
                .then((data) => {
                    if (data.status === "success" && data.unique_code) {
                        window.location.href = `/dashboard/${encodeURIComponent(courseCode)}/${data.unique_code}`;
                    } else {
                        showFlashMessage("error", "Unable to access course. Not enrolled or error occurred.");
                    }
                })
                .catch((error) => {
                    console.error("Error fetching unique code:", error);
                    showFlashMessage("error", "Error accessing dashboard.");
                });
        }
    });
});
