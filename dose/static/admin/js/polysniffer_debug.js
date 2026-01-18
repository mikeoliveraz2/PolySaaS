/**
 * PolySniffer Debug Integration
 * Adds "Sniff" button to debug passthrough endpoints
 */

/**
 * Open PolySniffer with pre-configured endpoint URL
 * @param {string} endpointUrl - The endpoint URL to debug
 * @param {string} endpointName - Name of the endpoint (for display)
 */
function openPolySnifferDebug(endpointUrl, endpointName = 'Endpoint') {
    // Get PolySniffer URL (can be configured via settings or use default)
    const polysnifferUrl = window.POLYSNIFFER_URL || 'https://polysniffer.up.railway.app';

    // Build PolySniffer URL with endpoint pre-filled
    const snifferUrl = `${polysnifferUrl}?url=${encodeURIComponent(endpointUrl)}&name=${encodeURIComponent(endpointName)}`;

    // Open in new window
    const snifferWindow = window.open(
        snifferUrl,
        'PolySniffer',
        'width=1400,height=900,resizable=yes,scrollbars=yes'
    );

    if (!snifferWindow) {
        alert('Please allow popups to use PolySniffer debug feature');
        return;
    }

    console.log(`[PolySniffer] Opening debug session for: ${endpointName}`);
    console.log(`[PolySniffer] Endpoint URL: ${endpointUrl}`);

    return snifferWindow;
}

/**
 * Add Sniff button to table row (for Django admin list views)
 * @param {string} rowId - ID of the row/element
 * @param {string} endpointUrl - The endpoint URL to debug
 * @param {string} endpointName - Name of the endpoint
 */
function addSniffButtonToRow(rowId, endpointUrl, endpointName) {
    const row = document.getElementById(rowId) || document.querySelector(`[data-id="${rowId}"]`);
    if (!row) {
        console.warn(`[PolySniffer] Row not found: ${rowId}`);
        return;
    }

    // Check if button already exists
    if (row.querySelector('.polysniffer-sniff-btn')) {
        return;
    }

    // Create button
    const button = document.createElement('button');
    button.className = 'polysniffer-sniff-btn';
    button.innerHTML = '🔍 Sniff';
    button.title = `Debug ${endpointName} with PolySniffer`;
    button.style.cssText = 'margin-left: 5px; padding: 4px 8px; font-size: 12px; cursor: pointer;';

    button.onclick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        openPolySnifferDebug(endpointUrl, endpointName);
    };

    // Find actions column or add to last cell
    const actionsCell = row.querySelector('.field-get_actions, .actions, td:last-child');
    if (actionsCell) {
        actionsCell.appendChild(button);
    } else {
        // Create new cell if needed
        const cell = document.createElement('td');
        cell.className = 'polysniffer-debug-cell';
        cell.appendChild(button);
        row.appendChild(cell);
    }
}

/**
 * Initialize PolySniffer debug buttons for PassThroughEndpoint admin
 * Call this after the admin list view loads
 */
function initPolySnifferDebugButtons() {
    // Find all endpoint rows (adjust selector based on your admin structure)
    const endpointRows = document.querySelectorAll('#result_list tbody tr, .results tbody tr');

    endpointRows.forEach((row, index) => {
        // Try to extract endpoint URL from row data
        // This will depend on your admin list_display configuration
        const endpointUrlCell = row.querySelector('.field-endpoint_url, .field-get_endpoint_url');
        if (endpointUrlCell) {
            const endpointUrl = endpointUrlCell.textContent.trim();
            const nameCell = row.querySelector('.field-trigger_path, .field-get_trigger_path, td:first-child');
            const endpointName = nameCell ? nameCell.textContent.trim() : `Endpoint ${index + 1}`;

            // Get row ID (Django admin uses field-select for checkboxes)
            const checkbox = row.querySelector('input[type="checkbox"]');
            const rowId = checkbox ? checkbox.value : `row-${index}`;

            // Add debug button
            addSniffButtonToRow(rowId, endpointUrl, endpointName);
        }
    });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPolySnifferDebugButtons);
} else {
    initPolySnifferDebugButtons();
}

// Re-initialize after AJAX updates (Django admin uses AJAX for filtering/searching)
if (typeof django !== 'undefined' && django.jQuery) {
    django.jQuery(document).on('DOMNodeInserted', function(e) {
        if (e.target.querySelector && e.target.querySelector('#result_list')) {
            initPolySnifferDebugButtons();
        }
    });
}

