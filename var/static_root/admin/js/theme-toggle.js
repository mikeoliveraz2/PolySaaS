console.log('Theme toggle JS loaded');

document.addEventListener('DOMContentLoaded', function() {
    // Find both dropdown and top menu toggle links
    const toggleDropdowns = Array.from(document.querySelectorAll('a.dropdown-item')).filter(a => a.textContent.trim().includes('Toggle Theme'));
    const toggleTopMenus = Array.from(document.querySelectorAll('a')).filter(a => a.textContent.trim().includes('Toggle light/dark') || a.textContent.trim().includes('Change to'));
    const allToggleLinks = [...toggleDropdowns, ...toggleTopMenus];
    
    // Also check for usermenu toggle
    const userMenuToggle = document.querySelector('.usermenu a[href="javascript:void(0)"]');
    if (userMenuToggle && !allToggleLinks.includes(userMenuToggle)) {
        allToggleLinks.push(userMenuToggle);
    }
    
    // Set initial button text based on current state
    const isDark = document.body.classList.contains('dark-mode') || document.body.classList.contains('theme-dark');
    const buttonText = isDark ? 'Change to Light' : 'Change to Dark';
    const iconClass = isDark ? 'fa-sun' : 'fa-moon';
    
    if (allToggleLinks.length === 0) {
        console.log('No theme toggle links found');
    } else {
        allToggleLinks.forEach(function(toggleBtn) {
            // Update button text to show opposite state
            toggleBtn.innerHTML = `<i class="fas ${iconClass}"></i> ${buttonText}`;
            console.log('Theme toggle link found:', toggleBtn);
            toggleBtn.addEventListener('click', function(e) {
                e.preventDefault();
                const body = document.body;
                // Try both possible class names for light/dark
                const isLight = body.classList.contains('theme-light') || body.classList.contains('light-mode');
                const isDark = body.classList.contains('theme-dark') || body.classList.contains('dark-mode');
                if (isLight) {
                    body.classList.remove('theme-light', 'light-mode');
                    body.classList.add('theme-dark', 'dark-mode');
                } else if (isDark) {
                    body.classList.remove('theme-dark', 'dark-mode');
                    body.classList.add('theme-light', 'light-mode');
                } else {
                    // Default: toggle to dark
                    body.classList.add('theme-dark', 'dark-mode');
                }
                console.log('Theme toggled. Current body classes:', body.className);
            });
        });
    }

    // THEME PICKER LOGIC (for actual Jazzmin picker)
    const jazzminPicker = document.getElementById('jazzmin-theme-chooser');
    if (jazzminPicker) {
        console.log('[ThemePicker] Jazzmin picker found, current value:', jazzminPicker.value);
            // DISABLED: POST on theme select event for Jazzmin picker. Now handled by Save button in override template.
            // jazzminPicker.addEventListener('change', function() {
            //     const selectedTheme = jazzminPicker.value;
            //     console.log('[ThemePicker] Jazzmin picker changed, selected:', selectedTheme);
            //     fetch('/admin/set-theme/', {
            //         method: 'POST',
            //         headers: {
            //             'Content-Type': 'application/x-www-form-urlencoded',
            //             'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken')),
            //         },
            //         body: `type=light&theme=${encodeURIComponent(selectedTheme)}`
            //     })
            //     .then(response => {
            //         console.log('[ThemePicker] POST response status:', response.status);
            //         return response.json();
            //     })
            //     .then(data => {
            //         console.log('[ThemePicker] POST response data:', data);
            //         window.location.reload();
            //     });
            // });
    } else {
        console.log('[ThemePicker] Jazzmin picker element not found');
    }
});
