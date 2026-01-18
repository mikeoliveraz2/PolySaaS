console.log('Theme toggle JS loaded');

document.addEventListener('DOMContentLoaded', function() {
    // Find both dropdown and top menu toggle links
    const toggleDropdowns = Array.from(document.querySelectorAll('a.dropdown-item')).filter(a => a.textContent.trim().includes('Toggle Theme'));
    const toggleTopMenus = Array.from(document.querySelectorAll('a')).filter(a => a.textContent.trim().includes('Toggle light/dark'));
    const allToggleLinks = [...toggleDropdowns, ...toggleTopMenus];
    if (allToggleLinks.length === 0) {
        console.log('No theme toggle links found');
    } else {
        allToggleLinks.forEach(function(toggleBtn) {
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
    } else {
        console.log('[ThemePicker] Jazzmin picker element not found');
    }
});

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

// ============================================================================
// NOTIFICATION SYSTEM
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    const notificationBell = document.getElementById('notificationDropdown');
    const notificationBadge = document.getElementById('notification-badge');

    if (!notificationBell || !notificationBadge) {
        console.log('Notification elements not found');
        return;
    }

    // Add pulse animation to badge
    notificationBadge.classList.add('pulse');

    // Fetch notifications from backend
    function fetchNotifications() {
        fetch('/dose/api/notifications/unread/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            const count = data.unread_count || 0;
            const notifications = data.notifications || [];

            // Update badge
            if (count > 0) {
                notificationBadge.textContent = count > 99 ? '99+' : count;
                notificationBadge.style.display = 'inline-flex';

                // Trigger bell animation for new notifications
                const bellIcon = notificationBell.querySelector('.fa-bell');
                if (bellIcon) {
                    bellIcon.classList.add('new-notification');
                    setTimeout(() => bellIcon.classList.remove('new-notification'), 500);
                }
            } else {
                notificationBadge.style.display = 'none';
            }

            // Update dropdown content with real notifications
            const dropdown = document.querySelector('.dropdown-menu[aria-labelledby="notificationDropdown"]');
            if (dropdown && notifications.length > 0) {
                let dropdownHTML = `
                    <span class="dropdown-item dropdown-header" style="font-weight: 600; border-bottom: 1px solid #dee2e6;">${count} Notification${count !== 1 ? 's' : ''}</span>
                    <div class="dropdown-divider"></div>
                `;

                notifications.forEach((notif, index) => {
                    const timeAgo = getTimeAgo(notif.created_at);
                    dropdownHTML += `
                        <a href="#" class="dropdown-item">
                            <i class="fas fa-envelope mr-2"></i> ${notif.subject || notif.preview}
                            <span class="float-right text-muted text-sm">${timeAgo}</span>
                        </a>
                    `;
                    if (index < notifications.length - 1) {
                        dropdownHTML += '<div class="dropdown-divider"></div>';
                    }
                });

                dropdownHTML += `
                    <div class="dropdown-divider"></div>
                    <a href="/admin/dose/dosemessage/" class="dropdown-item dropdown-footer">See All Notifications</a>
                `;

                dropdown.innerHTML = dropdownHTML;
            } else if (dropdown) {
                dropdown.innerHTML = `
                    <span class="dropdown-item dropdown-header" style="font-weight: 600; border-bottom: 1px solid #dee2e6;">No Notifications</span>
                    <div class="dropdown-divider"></div>
                    <div class="dropdown-item text-center text-muted">No unread messages</div>
                `;
            }
        })
        .catch(error => {
            console.log('Could not fetch notifications:', error);
        });
    }

    // Helper function to format time ago
    function getTimeAgo(dateString) {
        if (!dateString) return 'just now';
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        if (seconds < 60) return 'just now';
        if (seconds < 3600) return Math.floor(seconds / 60) + ' mins';
        if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours';
        return Math.floor(seconds / 86400) + ' days';
    }

    // Initial fetch
    fetchNotifications();

    // Poll for new notifications every 30 seconds
    setInterval(fetchNotifications, 30000);

    // Track if dropdown is currently open and if messages have been marked
    let dropdownOpen = false;
    let markedAsRead = false;

    // Mark notifications as read when dropdown is opened
    notificationBell.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdownOpen = !dropdownOpen;

        if (dropdownOpen) {
            console.log('Notification dropdown opened, messages displayed to user');
            // Don't mark as read yet - wait for dropdown to close
        }
    });

    // Mark as read and update badge when dropdown is CLOSED
    document.addEventListener('click', function(e) {
        const dropdown = document.querySelector('.dropdown-menu[aria-labelledby="notificationDropdown"]');

        // Check if click is outside the dropdown and bell
        if (dropdown && !dropdown.contains(e.target) && e.target !== notificationBell && !notificationBell.contains(e.target)) {
            if (dropdownOpen && !markedAsRead) {
                console.log('Dropdown closed, marking notifications as read...');

                // Mark all as read via POST request
                fetch('/dose/api/unread-dosemessages/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    console.log('Marked as read:', data);
                    markedAsRead = true;

                    // Update badge to show 0
                    notificationBadge.textContent = '0';
                    notificationBadge.style.display = 'none';

                    // Refresh count to check for any new notifications
                    setTimeout(fetchNotifications, 500);
                })
                .catch(error => {
                    console.error('Error marking as read:', error);
                });
            }

            dropdownOpen = false;
            markedAsRead = false;
        }
    });
});
