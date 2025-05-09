document.addEventListener("DOMContentLoaded", () => {
    let selectedCourse = "";
    let isSubmitting = false;

    function isValidCourse(course) {
        return typeof course === "string" && course.trim().length > 0;
    }

    function fetchCaptcha() {
        fetch("/start_enrollment")
            .then((response) => {
                if (!response.ok) throw new Error("Failed to fetch CAPTCHA");
                return response.json();
            })
            .then((data) => {
                if (data.captcha) {
                    document.getElementById("captcha-label").textContent = data.captcha;
                    document.querySelector('input[name="captcha"]').value = "";
                    document.getElementById("captcha-error").textContent = "";
                }
            })
            .catch((error) => console.error("Error fetching captcha:", error));
    }

    function handleEnrollment(course) {
        if (!isValidCourse(course)) {
            console.error("Invalid course selected.");
            return;
        }

        selectedCourse = course;

        fetch(`/check_enrollment?course_name=${encodeURIComponent(selectedCourse)}`)
            .then((response) => {
                if (!response.ok) throw new Error("Enrollment check failed");
                return response.json();
            })
            .then((data) => {
                if (data.exceeded_limit) {
                    showFlashMessage("error", "You can enroll in a maximum of 2 courses.", "enrollment-limit-message");
                    showPopup("enrollment-limit-popup");
                } else if (data.already_enrolled) {
                    redirectToCourse(selectedCourse);
                } else {
                    document.getElementById("confirm-course-name").textContent = selectedCourse;
                    showPopup("confirm-popup");
                }
            })
            .catch((error) => {
                console.error("Error checking enrollment:", error);
                showFlashMessage("error", "Something went wrong while checking enrollment.");
            });
    }

    function startEnrollment() {
        fetchCaptcha();
        document.getElementById("final-course-name").value = selectedCourse;
        showPopup("enrollment-popup");
    }

    function redirectToCourse(course) {
        fetch(`/get_unique_code?course_name=${encodeURIComponent(course)}`)
            .then((response) => {
                if (!response.ok) throw new Error("Failed to get unique code");
                return response.json();
            })
            .then((data) => {
                if (data.unique_code) {
                    window.location.href = `/dashboard/${encodeURIComponent(course)}/${data.unique_code}`;
                } else {
                    showFlashMessage("error", "Unable to find unique code for this course.");
                }
            })
            .catch((error) => {
                console.error("Error fetching unique code:", error);
                showFlashMessage("error", "Network error. Please try again.");
            });
    }

    document.getElementById("enroll-form").addEventListener("submit", function (event) {
        event.preventDefault();

        const captchaInput = document.querySelector('input[name="captcha"]').value.trim();
        if (captchaInput === "") {
            document.getElementById("captcha-error").textContent = "Please enter the CAPTCHA before proceeding.";
            showPopup("enrollment-popup");
            return;
        }

        if (isSubmitting) return;
        isSubmitting = true;

        const formData = new FormData(this);

        fetch("/final_enroll", {
            method: "POST",
            body: formData,
        })
            .then((response) => {
                isSubmitting = false;
                if (!response.ok) throw new Error("Final enrollment failed");
                return response.json();
            })
            .then((data) => {
                if (data.success) {
                    redirectToCourse(selectedCourse);
                } else {
                    document.getElementById("captcha-error").textContent = data.error || "Enrollment failed.";
                    showPopup("enrollment-popup");
                }
            })
            .catch((error) => {
                isSubmitting = false;
                console.error("Error in final enrollment:", error);
                showFlashMessage("error", "Unexpected error. Please try again.");
            });
    });

    document.querySelector('input[name="captcha"]').addEventListener("input", function () {
        document.getElementById("captcha-error").textContent = "";
    });

    document.querySelectorAll(".enroll-btn").forEach((button) => {
        button.addEventListener("click", () => handleEnrollment(button.dataset.course));
    });

    document.querySelectorAll(".open-btn").forEach((button) => {
        button.addEventListener("click", () => redirectToCourse(button.dataset.course));
    });

    document.querySelector('.popup button[type="submit"]').addEventListener('click', (event) => {
        const captchaInput = document.querySelector('input[name="captcha"]').value.trim();
        if (captchaInput === "") {
            event.preventDefault();
            document.getElementById("captcha-error").textContent = "Please enter the CAPTCHA before proceeding.";
            showPopup('enrollment-popup');
        }
    });

    window.showPhonePopup = startEnrollment;
});
