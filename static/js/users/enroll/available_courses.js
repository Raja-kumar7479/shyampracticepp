document.addEventListener("DOMContentLoaded", () => {
    let selectedCourseCode = "";
    let selectedCourseName = "";
    let isSubmitting = false;

    function isValidCourse(code) {
        return typeof code === "string" && code.trim().length > 0;
    }

    function fetchCaptcha() {
        fetch("/start_enrollment")
            .then(res => res.json())
            .then(data => {
                if (data.captcha) {
                    document.getElementById("captcha-label").textContent = data.captcha;
                    document.querySelector('input[name="captcha"]').value = "";
                    document.getElementById("captcha-error").textContent = "";
                }
            })
            .catch(err => console.error("Captcha fetch error:", err));
    }

    function handleEnrollment(code, name) {
        if (!isValidCourse(code)) return;

        selectedCourseCode = code;
        selectedCourseName = name;

        fetch(`/check_enrollment?course_code=${encodeURIComponent(code)}`)
            .then(res => res.json())
            .then(data => {
                if (data.exceeded_limit) {
                    showFlashMessage("error", "You can enroll in a maximum of 2 courses.", "enrollment-limit-message");
                    showPopup("enrollment-limit-popup");
                } else if (data.already_enrolled) {
                    redirectToCourse(code);
                } else {
                    document.getElementById("confirm-course-code").textContent = code;
                    showPopup("confirm-popup");
                }
            })
            .catch(err => {
                console.error("Enrollment check failed:", err);
                showFlashMessage("error", "Something went wrong while checking enrollment.");
            });
    }

    function redirectToCourse(code) {
        fetch(`/get_unique_code?course_code=${encodeURIComponent(code)}`)
            .then(res => res.json())
            .then(data => {
                if (data.unique_code) {
                    window.location.href = `/dashboard/${encodeURIComponent(code)}/${data.unique_code}`;
                } else {
                    showFlashMessage("error", "Unable to find unique code for this course.");
                }
            })
            .catch(err => {
                console.error("Unique code fetch error:", err);
                showFlashMessage("error", "Network error. Please try again.");
            });
    }

    function showPhonePopup() {
        fetchCaptcha();
        document.getElementById("final-course-code").value = selectedCourseCode;
        document.getElementById("final-course-name").value = selectedCourseName;
        showPopup("enrollment-popup");
    }

    document.getElementById("enroll-form").addEventListener("submit", function (e) {
        e.preventDefault();
        if (isSubmitting) return;
        isSubmitting = true;

        const formData = new FormData(this);

        fetch("/final_enroll", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            isSubmitting = false;
            if (data.success) {
                closePopup("enrollment-popup");

                // Optional: Update UI visually if needed
                const boxes = document.querySelectorAll(".exam-box");
                boxes.forEach(box => {
                    const codeDiv = box.querySelector(".exam-code");
                    if (codeDiv?.textContent.trim() === selectedCourseCode) {
                        box.querySelector(".card-body").innerHTML =
                            `<h3 class="card-title">${selectedCourseName}</h3>
                             <p class="card-text">You have successfully enrolled.</p>
                             <button class="btn btn-success open-btn" data-course="${selectedCourseCode}">Active</button>`;
                        const icon = box.querySelector(".exam-icon");
                        if (icon) {
                            const label = document.createElement("span");
                            label.classList.add("enrolled-label");
                            label.textContent = "Enrolled";
                            icon.prepend(label);
                        }
                    }
                });

                // Automatically redirect to dashboard after enrollment
                if (data.unique_code) {
                    window.location.href = `/dashboard/${encodeURIComponent(selectedCourseCode)}/${data.unique_code}`;
                } else {
                    // Fallback if unique_code not returned from enrollment response
                    redirectToCourse(selectedCourseCode);
                }
            } else {
                document.getElementById("captcha-error").textContent = data.error || "Something went wrong.";
            }
        })
        .catch(err => {
            isSubmitting = false;
            console.error("Final enrollment error:", err);
            document.getElementById("captcha-error").textContent = "Unexpected error occurred.";
        });
    });

    document.querySelector('input[name="captcha"]').addEventListener("input", () => {
        document.getElementById("captcha-error").textContent = "";
    });

    document.querySelectorAll(".enroll-btn").forEach((button) => {
        button.addEventListener("click", () => {
            const courseCode = button.dataset.course;
            const courseName = button.closest(".exam-box").querySelector(".card-title").textContent;
            handleEnrollment(courseCode, courseName);
        });
    });

    document.querySelectorAll(".open-btn").forEach((button) => {
        button.addEventListener("click", () => redirectToCourse(button.dataset.course));
    });

    document.querySelector('#confirm-popup .btn-primary').addEventListener("click", () => {
        closePopup("confirm-popup");
        showPopup("details-popup");
    });

    document.querySelector('#details-popup .btn-primary').addEventListener("click", () => {
        closePopup("details-popup");
        showPhonePopup();
    });
});
