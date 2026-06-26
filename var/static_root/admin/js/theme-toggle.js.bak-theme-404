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

function requestThemeToggle() {
    const headers = {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCookie('csrftoken') || ''
    };
    const endpoints = ['/dose/toggle-theme/', '/toggle-theme/'];

    function tryEndpoint(index) {
        if (index >= endpoints.length) {
            throw new Error('No working toggle endpoint found');
        }
        return fetch(endpoints[index], { method: 'GET', headers: headers })
            .then((response) => {
                if (response.ok) {
                    return response.json();
                }
                if (response.status === 404 || response.status === 405) {
                    return tryEndpoint(index + 1);
                }
                throw new Error('Toggle request failed with status ' + response.status);
            });
    }

    return tryEndpoint(0);
}

function detectDisplayMode() {
    const modeCookie = (getCookie('display_mode') || '').toLowerCase();
    if (modeCookie === 'dark' || modeCookie === 'light') {
        return modeCookie;
    }
    return document.body.classList.contains('dark-mode') ? 'dark' : 'light';
}

function ensureThemeModeBadge() {
    if (!document.getElementById('ps-theme-mode-badge-style')) {
        const style = document.createElement('style');
        style.id = 'ps-theme-mode-badge-style';
        style.textContent = [
            '.ps-theme-mode-badge {',
            '  margin-left: 8px;',
            '  padding: 2px 8px;',
            '  border-radius: 999px;',
            '  font-size: 11px;',
            '  font-weight: 700;',
            '  letter-spacing: .02em;',
            '  border: 1px solid transparent;',
            '  vertical-align: middle;',
            '}',
            '.ps-theme-mode-badge.ps-theme-light {',
            '  color: #1e40af;',
            '  background: #dbeafe;',
            '  border-color: #93c5fd;',
            '}',
            '.ps-theme-mode-badge.ps-theme-dark {',
            '  color: #e2e8f0;',
            '  background: #334155;',
            '  border-color: #64748b;',
            '}',
        ].join('\n');
        document.head.appendChild(style);
    }

    const mode = detectDisplayMode();
    const controls = Array.from(document.querySelectorAll('a[href*="select-theme"], #ps-theme-toggle-btn, #theme-toggle-btn'));
    controls.forEach(function(control) {
        if (!control) return;
        let badge = control.querySelector('.ps-theme-mode-badge');
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'ps-theme-mode-badge';
            control.appendChild(badge);
        }
        badge.textContent = mode === 'dark' ? 'Dark' : 'Light';
        badge.classList.toggle('ps-theme-dark', mode === 'dark');
        badge.classList.toggle('ps-theme-light', mode !== 'dark');
    });
}

// Toggle light/dark mode on the theme selection page.
document.addEventListener('DOMContentLoaded', function() {
    ensureThemeModeBadge();

    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            requestThemeToggle()
                .then(function(data) {
                    console.log('Theme toggled:', data.theme, data.mode);
                    ensureThemeModeBadge();
                    window.location.reload();
                })
                .catch(function(err) {
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
    }
});
