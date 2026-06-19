// THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
// BINGO: Font and Theme Toggle — commit 1dcca3bd
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
    const controls = Array.from(document.querySelectorAll(
        'a[href="#ps-theme-toggle"], a[href*="select-theme"], #ps-theme-toggle-btn, #theme-toggle-btn'
    ));
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

let themeToggleInFlight = false;

function ensureThemeToggleOverlayStyle() {
    if (document.getElementById('ps-theme-toggle-overlay-style')) {
        return;
    }
    const style = document.createElement('style');
    style.id = 'ps-theme-toggle-overlay-style';
    style.textContent = [
        '.ps-theme-toggle-overlay {',
        '  position: fixed;',
        '  inset: 0;',
        '  z-index: 2147483646;',
        '  background: rgba(15, 23, 42, 0.18);',
        '  display: none;',
        '  align-items: center;',
        '  justify-content: center;',
        '}',
        '.ps-theme-toggle-overlay.is-visible {',
        '  display: flex;',
        '}',
        '.ps-theme-toggle-spinner {',
        '  width: 58px;',
        '  height: 58px;',
        '  border: 5px solid rgba(148, 163, 184, 0.45);',
        '  border-top-color: #2563eb;',
        '  border-radius: 999px;',
        '  animation: ps-theme-spin 0.9s linear infinite;',
        '  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.22);',
        '}',
        '@keyframes ps-theme-spin {',
        '  to { transform: rotate(360deg); }',
        '}'
    ].join('\n');
    document.head.appendChild(style);
}

function getThemeToggleOverlay() {
    ensureThemeToggleOverlayStyle();
    let overlay = document.getElementById('ps-theme-toggle-overlay');
    if (overlay) {
        return overlay;
    }
    overlay = document.createElement('div');
    overlay.id = 'ps-theme-toggle-overlay';
    overlay.className = 'ps-theme-toggle-overlay';
    overlay.setAttribute('aria-hidden', 'true');

    const spinner = document.createElement('div');
    spinner.className = 'ps-theme-toggle-spinner';
    spinner.setAttribute('aria-label', 'Switching theme');
    overlay.appendChild(spinner);

    document.body.appendChild(overlay);
    return overlay;
}

function setThemeToggleOverlayVisible(isVisible) {
    const overlay = getThemeToggleOverlay();
    overlay.classList.toggle('is-visible', !!isVisible);
    overlay.setAttribute('aria-hidden', isVisible ? 'false' : 'true');
}

function getThemeToggleControls() {
    const allAnchors = Array.from(document.querySelectorAll('a, #ps-theme-toggle-btn, #theme-toggle-btn'));
    return allAnchors.filter(function(node) {
        if (!node) return false;
        if (node.id === 'ps-theme-toggle-btn' || node.id === 'theme-toggle-btn') return true;
        return isToggleMenuLink(node);
    });
}

function setThemeToggleBusyState(isBusy) {
    const controls = getThemeToggleControls();
    controls.forEach(function(control) {
        if (!control) return;
        control.style.pointerEvents = isBusy ? 'none' : '';
        control.style.opacity = isBusy ? '0.7' : '';
        if (isBusy) {
            control.setAttribute('aria-disabled', 'true');
            control.setAttribute('aria-busy', 'true');
        } else {
            control.removeAttribute('aria-disabled');
            control.removeAttribute('aria-busy');
        }

        const badge = control.querySelector('.ps-theme-mode-badge');
        if (badge && isBusy) {
            badge.textContent = 'Switching...';
            badge.classList.remove('ps-theme-dark', 'ps-theme-light');
        }
    });
    document.body.style.cursor = isBusy ? 'progress' : '';
    setThemeToggleOverlayVisible(isBusy);
}

function executeThemeToggle() {
    if (themeToggleInFlight) {
        return;
    }
    themeToggleInFlight = true;
    setThemeToggleBusyState(true);
    requestThemeToggle()
        .then(function() {
            ensureThemeModeBadge();
            window.location.reload();
        })
        .catch(function(err) {
            themeToggleInFlight = false;
            setThemeToggleBusyState(false);
            ensureThemeModeBadge();
            console.error('Failed to toggle theme:', err);
            alert('Failed to toggle theme. Please try again.');
        });
}

function bindThemeToggleControl(control) {
    if (!control || control.dataset.psThemeToggleBound === '1') {
        return;
    }
    control.dataset.psThemeToggleBound = '1';
    control.addEventListener('click', function(e) {
        e.preventDefault();
        executeThemeToggle();
    });
}

function isToggleMenuLink(anchor) {
    if (!anchor || !anchor.getAttribute) return false;
    const href = (anchor.getAttribute('href') || '').toLowerCase();
    const text = (anchor.textContent || '').toLowerCase();
    if (href === '#ps-theme-toggle') return true;
    if (href.indexOf('#ps-theme-toggle') !== -1) return true;
    if (href.indexOf('select-theme') !== -1 && text.indexOf('toggle') !== -1) return true;
    if (text.indexOf('toggle light') !== -1 || text.indexOf('toggle theme') !== -1) return true;
    return false;
}

function findToggleAnchorFromEventTarget(target) {
    if (!target) return null;
    if (target.tagName === 'A') return target;
    if (typeof target.closest === 'function') {
        return target.closest('a');
    }
    return null;
}

document.addEventListener('DOMContentLoaded', function() {
    ensureThemeModeBadge();

    document.querySelectorAll('a[href="#ps-theme-toggle"], a[href*="select-theme"]').forEach(function(a) {
        if (isToggleMenuLink(a)) {
            bindThemeToggleControl(a);
        }
    });

    document.querySelectorAll('.navbar-nav a.nav-link, .nav-item a').forEach(function(a) {
        if (isToggleMenuLink(a)) {
            bindThemeToggleControl(a);
        }
    });

    const userToggle = document.querySelector('.usermenu a[href="javascript:void(0)"]');
    if (userToggle && (userToggle.textContent || '').toLowerCase().indexOf('toggle theme') !== -1) {
        bindThemeToggleControl(userToggle);
    }

    bindThemeToggleControl(document.getElementById('theme-toggle-btn'));
    bindThemeToggleControl(document.getElementById('ps-theme-toggle-btn'));

    // Delegate clicks so dynamically rendered/replaced navbar links keep working.
    document.addEventListener('click', function(e) {
        const anchor = findToggleAnchorFromEventTarget(e.target);
        if (!isToggleMenuLink(anchor)) {
            return;
        }
        // First click on dynamically rendered links should toggle immediately.
        if (anchor.dataset.psThemeToggleBound !== '1') {
            e.preventDefault();
            bindThemeToggleControl(anchor);
            executeThemeToggle();
            return;
        }
    }, true);
});
