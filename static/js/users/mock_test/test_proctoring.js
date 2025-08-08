class ProctoringSystem {
    constructor(testKey, userEmail, courseCode, uniqueCode) {
        this.testKey = testKey;
        this.userEmail = userEmail;
        this.courseCode = courseCode;
        this.uniqueCode = uniqueCode;
        this.isTerminated = false;
        this.violationCount = 0;
        this.initialize();
    }

    initialize() {
        this.detectDevTools();
        this.handleVisibilityChange();
        this.handleFullscreenChange();
        this.disableContextMenu();
        this.disableCopyPaste();
    }

    async sendViolation(violationType, details) {
        if (this.isTerminated) {
            console.warn("Test already terminated. No more violations will be sent.");
            return;
        }

        this.violationCount++;
        console.warn(`Violation detected (${this.violationCount}): ${violationType}`, details);

        try {
            const response = await fetch(`/api/record-violation/${this.testKey}/${this.courseCode}/${this.uniqueCode}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ violationType, details })
            });

            if (response.status === 403) {
                const result = await response.json();
                if (result.status === 'terminated') {
                    this.isTerminated = true;
                    window.location.href = `/test-terminated/${this.testKey}/${this.courseCode}/${this.uniqueCode}/${violationType}`;
                }
            } else if (!response.ok) {
                console.error(`Server error on sending violation: ${response.status}`);
            }
        } catch (error) {
            console.error('Failed to send violation report:', error);
        }
    }

    detectDevTools() {
        const threshold = 160;
        const checkDevTools = () => {
            if (window.outerWidth - window.innerWidth > threshold || window.outerHeight - window.innerHeight > threshold) {
                this.sendViolation('devtools_open', 'Developer tools were opened.');
            }
        };
        setInterval(checkDevTools, 1000);
    }

    handleVisibilityChange() {
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') {
                this.sendViolation('tab_switch', 'User switched to another tab or minimized the window.');
            }
        });
    }

    handleFullscreenChange() {
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement) {
                this.sendViolation('fullscreen_exit', 'User exited full-screen mode.');
            }
        });
    }

    disableContextMenu() {
        window.addEventListener('contextmenu', e => {
            e.preventDefault();
            this.sendViolation('context_menu', 'Right-click (context menu) was disabled and attempted.');
        });
    }

    disableCopyPaste() {
        const events = ['copy', 'paste', 'cut'];
        events.forEach(event => {
            window.addEventListener(event, e => {
                e.preventDefault();
                this.sendViolation(`clipboard_${event}`, `Attempted to ${event} content.`);
            });
        });
    }
}