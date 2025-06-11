class ProctoringSystem {
    constructor(testId, uniqueCode, courseCode) {
        this.testId = testId;
        this.uniqueCode = uniqueCode;
        this.courseCode = courseCode;
        this.tabSwitchCount = 0;
        this.init();
    }

    init() {
        this.checkInitialWindowMode();
        this.attachEventListeners();
        this.detectDevTools();
    }

    terminateTest(violationType) {
        const url = `/test-terminated/${testId}/${courseCode}/${uniqueCode}/${violationType}`;
        window.location.href = url;
    }

    attachEventListeners() {
        document.addEventListener('visibilitychange', this.handleVisibility.bind(this));
        document.addEventListener('contextmenu', this.blockContextMenu.bind(this));
        document.addEventListener('mouseleave', this.handleMouseLeave.bind(this));
        window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
    }

    blockAllInput(e) {
        e.preventDefault();
        e.stopPropagation();
        return false;
    }

    blockContextMenu(e) {
        e.preventDefault();
        this.recordAndCheckViolation('right_click', 'Right-click detected');
    }

    handleVisibility() {
        if (document.hidden) {
            this.tabSwitchCount += 1;
            this.recordAndCheckViolation('tab_switch', `Tab switch detected (count: ${this.tabSwitchCount})`);
        }
    }

    handleMouseLeave() {
        this.recordAndCheckViolation('mouse_leave', 'Mouse moved outside test window');
    }

    handleBeforeUnload(e) {
        this.recordAndCheckViolation('page_exit_attempt', 'Page refresh/close attempt');
    }
    
    detectDevTools() {
        const threshold = 160;
        setInterval(() => {
            if (window.outerWidth - window.innerWidth > threshold ||
                window.outerHeight - window.innerHeight > threshold) {
                this.recordAndCheckViolation('devtools_open', 'DevTools detected');
            }
        }, 3000);
    }

    checkInitialWindowMode() {
        const isFullPopup = window.opener && !window.opener.closed &&
                            window.innerWidth === screen.availWidth &&
                            window.innerHeight === screen.availHeight;

        const isFullscreen = document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement;

        const isManuallyMaximized = (window.screenLeft === 0 || window.screenX === 0) &&
                                    (window.screenTop === 0 || window.screenY === 0) &&
                                    (window.innerWidth === screen.availWidth) &&
                                    (window.innerHeight === screen.availHeight);

        if (!isFullPopup && !isFullscreen && !isManuallyMaximized) {
            this.recordAndCheckViolation('initial_window_mode', 'Test not in expected window mode on load');
        }
    }

    async recordAndCheckViolation(type, details) {
        try {
            const response = await fetch(`/api/record-violation/${testId}/${courseCode}/${uniqueCode}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    violationType: type,
                    details: details
                })
            });         

            if (response.status === 403) {
                this.terminateTest(type);
            }
        } catch (error) {
            console.error("Error recording violation:", error);
        }
    }
}