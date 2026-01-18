// Example JS for GUI theme picker persistence
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
const csrftoken = getCookie('csrftoken');

// Replace this with your actual picker element and event
// DISABLED: POST on theme select event. Now handled by Save button in override template.
// const picker = document.getElementById('theme-picker');
// if (picker) {
//     console.log('[ThemePicker] Picker found, current value:', picker.value);
//     picker.addEventListener('change', function() {
//         const selectedTheme = picker.value;
//         console.log('[ThemePicker] Picker changed, selected:', selectedTheme);
//         fetch('/dose/set-theme/', {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//                 'X-CSRFToken': csrftoken,
//             },
//             body: JSON.stringify({ theme: selectedTheme })
//         })
//         .then(response => {
//             console.log('[ThemePicker] POST response status:', response.status);
//             return response.json();
//         })
//         .then(data => {
//             console.log('[ThemePicker] POST response data:', data);
//             window.location.reload();
//         });
//     });
// } else {
//     console.log('[ThemePicker] Picker element not found');
// }
