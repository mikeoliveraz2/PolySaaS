console.log('Theme toggle JS loaded');

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Toggle light/dark mode on the theme selection page
document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
        console.log('Theme toggle button found on theme page');
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            fetch('/dose/toggle-theme/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Theme toggled:', data.theme);
                window.location.reload();
            })
            .catch(err => {
                console.error('Failed to toggle theme:', err);
                alert('Failed to toggle theme. Please try again.');
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
