document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.querySelector('.usermenu a[href="javascript:void(0)"]');
    if (!toggleBtn) return;
    const isDark = document.body.classList.contains('dark-mode');
    toggleBtn.classList.toggle('dark-mode', isDark);
    // Show opposite state: "Change to Dark" when light, "Change to Light" when dark
    toggleBtn.innerHTML = isDark 
        ? '<i class="fas fa-sun"></i> Change to Light' 
        : '<i class="fas fa-moon"></i> Change to Dark';
    toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        fetch('/toggle-theme/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
        })
        .then(response => response.json())
        .then(data => {
            window.location.reload();
        });
    });
    // Jazzmin theme picker integration
    const jazzminPicker = document.querySelector('.theme-switcher select');
    // DISABLED: POST on theme select event for Jazzmin picker. Now handled by Save button in override template.
    // if (jazzminPicker) {
    //     console.log('Jazzmin theme picker found');
    //     jazzminPicker.addEventListener('change', function(e) {
    //         const themeValue = e.target.value;
    //         console.log('Theme picker changed:', themeValue);
    //         // List of dark themes
    //         const darkThemes = ['darkly', 'cyborg', 'slate', 'superhero', 'solar'];
    //         const themeType = darkThemes.includes(themeValue) ? 'dark' : 'light';
    //         const csrfTokenElem = document.querySelector('[name=csrfmiddlewaretoken]');
    //         if (!csrfTokenElem) {
    //             console.error('CSRF token not found');
    //             return;
    //         }
    //         console.log('Sending POST to /admin/set-theme/ with:', themeType, themeValue);
    //         fetch('/admin/set-theme/', {
    //             method: 'POST',
    //             headers: {
    //                 'Content-Type': 'application/x-www-form-urlencoded',
    //                 'X-CSRFToken': csrfTokenElem.value,
    //             },
    //             body: `type=${themeType}&theme=${encodeURIComponent(themeValue)}`
    //         })
    //         .then(response => response.json())
    //         .then(data => {
    //             console.log('Theme POST response:', data);
    //             if (data.status === 'ok') {
    //                 window.location.reload();
    //             }
    //         })
    //         .catch(err => {
    //             console.error('Theme POST error:', err);
    //         });
    //     });
    // } else {
    //     console.warn('Jazzmin theme picker not found');
    // }
});
