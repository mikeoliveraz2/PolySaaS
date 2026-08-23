(function () {
    'use strict';

    var script = document.currentScript || document.getElementById('pss-mailbox-bridge');
    if (!script) return;

    var pollUrl = script.dataset.pollUrl || '';
    var actionPath = script.dataset.actionPath || '';
    var method = script.dataset.method || 'POST';
    var direction = script.dataset.direction || 'REQ';
    var launchUrl = script.dataset.launchUrl || '';
    var lastMailboxId = 0;
    window.__PS_ORCH_ACTION_PATH = actionPath;

    var pathNode = document.getElementById('pss-action-path');
    if (pathNode) pathNode.textContent = actionPath;

    var bindButton = document.getElementById('pss-insert-instruction-btn');
    if (bindButton) {
        bindButton.textContent = '+ Attach Webhook / Consumer';
        bindButton.onclick = function (event) {
            event.preventDefault();
            event.stopImmediatePropagation();
            var url = '/admin/dose/instruction/add/?requestpath=' +
                encodeURIComponent(actionPath) +
                '&requestmethod=' + encodeURIComponent(method) +
                '&direction=' + encodeURIComponent(direction) +
                '&match_type=path&bind_only=1';
            window.open(url, '_blank', 'noopener');
            return false;
        };
    }

    var copyButton = document.getElementById('pss-copy-slack-url');
    var copyStatus = document.getElementById('pss-copy-slack-status');
    var copyInput = document.getElementById('pss-slack-url-value');
    var embeddedButton = document.getElementById('pss-open-slack-embedded');
    var embeddedCloseButton = document.getElementById('pss-close-slack-embedded');
    var launchChoices = document.getElementById('pss-slack-launch-choices');
    var embeddedContent = document.getElementById('pss-slack-embedded-content');

    if (embeddedButton && launchChoices && embeddedContent) {
        embeddedButton.onclick = function () {
            launchChoices.style.display = 'none';
            embeddedContent.style.display = 'block';
        };
    }

    if (embeddedCloseButton && launchChoices && embeddedContent) {
        embeddedCloseButton.onclick = function () {
            embeddedContent.style.display = 'none';
            launchChoices.style.display = 'flex';
        };
    }

    function setCopyStatus(message, isError) {
        if (!copyStatus) return;
        copyStatus.textContent = message;
        copyStatus.style.color = isError ? '#fca5a5' : '#86efac';
    }

    function copyWithTextarea(value) {
        var textarea = document.createElement('textarea');
        textarea.value = value;
        textarea.setAttribute('readonly', '');
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        var copied = document.execCommand('copy');
        document.body.removeChild(textarea);
        if (!copied) throw new Error('Copy command was rejected');
    }

    if (copyButton) {
        copyButton.onclick = async function () {
            if (!launchUrl) {
                setCopyStatus('Slack URL is unavailable.', true);
                return;
            }
            try {
                if (navigator.clipboard && window.isSecureContext) {
                    try {
                        await navigator.clipboard.writeText(launchUrl);
                    } catch (clipboardError) {
                        copyWithTextarea(launchUrl);
                    }
                } else {
                    copyWithTextarea(launchUrl);
                }
                setCopyStatus('Copied. Paste the URL into Chrome or Edge.', false);
            } catch (error) {
                if (copyInput) {
                    copyInput.style.display = 'block';
                    copyInput.focus();
                    copyInput.select();
                    setCopyStatus(
                        'Clipboard access is blocked here. The URL is selected — press Ctrl+C.',
                        false
                    );
                } else {
                    setCopyStatus(
                        'Copy failed. Use the link below and copy its address.',
                        true
                    );
                }
            }
        };
    }

    function showEvent(item) {
        if (!item || !item.id) return;
        lastMailboxId = Math.max(lastMailboxId, item.id);
        var state = item.transaction_state || item.status || 'processed';
        var detail = item.outcome || item.error ||
            ((item.event_key || 'Event') + ': ' + JSON.stringify(item.payload || {}));
        if (window.PolySaaSTransactionBar) {
            window.PolySaaSTransactionBar.update({
                state: state,
                path: item.action_path || actionPath,
                detail: detail
            });
        }
    }

    async function pollMailbox() {
        try {
            var joiner = pollUrl.indexOf('?') >= 0 ? '&' : '?';
            var response = await fetch(
                pollUrl + joiner + 'mailbox_since_id=' + lastMailboxId,
                {
                    credentials: 'same-origin',
                    cache: 'no-store',
                    headers: {'Accept': 'application/json'}
                }
            );
            var data = await response.json();
            if (!data.success) return;
            (data.mailbox_events || [])
                .sort(function (a, b) { return a.id - b.id; })
                .forEach(showEvent);
        } catch (error) {
            if (window.PolySaaSTransactionBar) {
                window.PolySaaSTransactionBar.update({
                    state: 'failed',
                    path: actionPath,
                    label: 'MAILBOX UNAVAILABLE',
                    detail: error.message
                });
            }
        }
    }

    pollMailbox();
    window.setInterval(pollMailbox, 1500);
})();
