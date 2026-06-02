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

document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.getElementById('theme-toggle-btn') || document.querySelector('.usermenu a[href="javascript:void(0)"]');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            requestThemeToggle()
                .then(function() {
                    window.location.reload();
                })
                .catch(function(err) {
                    console.error('Failed to toggle theme:', err);
                    alert('Failed to toggle theme. Please try again.');
                });
        });
    }
});
