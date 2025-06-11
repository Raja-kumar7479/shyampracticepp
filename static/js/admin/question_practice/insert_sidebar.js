document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    const sidebarCollapseClose = document.getElementById('sidebarCollapseClose');
    const content = document.getElementById('content');

    const toggleSidebar = () => {
        sidebar.classList.toggle('active');
    };

    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', () => {
            toggleSidebar();
        });
    }

    if (sidebarCollapseClose) {
        sidebarCollapseClose.addEventListener('click', () => {
            toggleSidebar();
        });
    }

    const adjustSidebarOnResize = () => {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('active');
        } else {
            if (!sidebar.classList.contains('active')) {
                sidebar.classList.add('active');
            }
        }
    };

    adjustSidebarOnResize();
    window.addEventListener('resize', adjustSidebarOnResize);
});
