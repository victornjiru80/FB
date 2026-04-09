// Custom Admin Sidebar JavaScript
(function($) {
    'use strict';
    
    $(document).ready(function() {
        // Ensure sidebar only responds to clicks, not hover
        const navSidebar = document.getElementById('nav-sidebar');
        const toggleButton = document.getElementById('toggle-nav-sidebar');
        const main = document.getElementById('main');
        
        if (toggleButton && navSidebar && main) {
            // Remove any hover-based behavior
            navSidebar.style.pointerEvents = 'auto';
            
            // Enhanced click handler
            toggleButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                let navSidebarIsOpen = localStorage.getItem('django.admin.navSidebarIsOpen');
                if (navSidebarIsOpen === null) {
                    navSidebarIsOpen = 'true';
                }
                
                if (navSidebarIsOpen === 'true') {
                    navSidebarIsOpen = 'false';
                } else {
                    navSidebarIsOpen = 'true';
                }
                
                localStorage.setItem('django.admin.navSidebarIsOpen', navSidebarIsOpen);
                main.classList.toggle('shifted');
                navSidebar.setAttribute('aria-expanded', navSidebarIsOpen);
                
                // Add smooth transition
                navSidebar.style.transition = 'margin-left 0.3s ease, visibility 0.3s ease';
            });
            
            // Prevent any hover-based expansion
            navSidebar.addEventListener('mouseenter', function(e) {
                e.stopPropagation();
            });
            
            navSidebar.addEventListener('mouseleave', function(e) {
                e.stopPropagation();
            });
            
            // Initialize sidebar state
            let navSidebarIsOpen = localStorage.getItem('django.admin.navSidebarIsOpen');
            if (navSidebarIsOpen === null) {
                navSidebarIsOpen = 'true';
            }
            main.classList.toggle('shifted', navSidebarIsOpen === 'true');
            navSidebar.setAttribute('aria-expanded', navSidebarIsOpen);
        }
        
        // Improve search filter functionality
        const navFilter = document.getElementById('nav-filter');
        if (navFilter) {
            navFilter.addEventListener('input', function(e) {
                const filterValue = e.target.value.toLowerCase();
                const navLinks = navSidebar.querySelectorAll('th[scope=row] a');
                
                navLinks.forEach(function(link) {
                    const row = link.closest('tr');
                    if (row) {
                        const text = link.textContent.toLowerCase();
                        if (text.includes(filterValue)) {
                            row.style.display = '';
                        } else {
                            row.style.display = 'none';
                        }
                    }
                });
                
                // Update filter styling
                if (filterValue) {
                    navFilter.classList.remove('no-results');
                    const visibleRows = navSidebar.querySelectorAll('tr[style=""]').length;
                    if (visibleRows === 0) {
                        navFilter.classList.add('no-results');
                    }
                } else {
                    navFilter.classList.remove('no-results');
                    navLinks.forEach(function(link) {
                        const row = link.closest('tr');
                        if (row) {
                            row.style.display = '';
                        }
                    });
                }
            });
        }
    });
    
})(django.jQuery); 