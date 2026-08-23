(function () {
    'use strict';

    var root = document.querySelector('[data-endpoint-home]');
    if (!root) return;

    function bar(state, label, detail, path) {
        if (window.PolySaaSTransactionBar) {
            window.PolySaaSTransactionBar.update({
                state: state,
                label: label,
                detail: detail,
                path: path
            });
        }
    }

    async function waitForMailbox(mailboxId, path) {
        var statusBase = root.dataset.statusUrl || '';
        for (var attempt = 0; attempt < 30; attempt += 1) {
            var response = await fetch(statusBase + mailboxId + '/', {
                credentials: 'same-origin',
                headers: {'Accept': 'application/json'}
            });
            var data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Could not read mailbox status');
            }
            if (data.status === 'pending') {
                bar('pending', 'PENDING', 'Mailbox #' + mailboxId + ' is waiting', path);
            } else if (data.status === 'claimed') {
                bar('claimed', 'PROCESSING', 'Consumer is running', path);
            } else if (data.status === 'failed' || data.status === 'expired') {
                throw new Error(data.error || ('Mailbox ' + data.status));
            } else if (data.status === 'processed') {
                var result = data.result || {};
                var atomics = result.results || [];
                var failed = atomics.some(function (item) {
                    return item && (item.status === 'error' || item.status === 'failed');
                });
                var noConsumer = result.status === 'no_instruction' || result.matched === 0;
                if (failed || noConsumer) {
                    bar(
                        'failed',
                        noConsumer ? 'NO CONSUMER' : 'FAILED',
                        noConsumer ? 'No consumer is bound' : 'Consumer failed',
                        path
                    );
                } else {
                    bar('success', 'SUCCESS', 'Transaction completed', path);
                }
                return;
            }
            await new Promise(function (resolve) { window.setTimeout(resolve, 600); });
        }
        throw new Error('Mailbox processing timed out');
    }

    async function fireDirect(button) {
        var url = button.dataset.actionUrl;
        if (!url) return;
        var target = button.dataset.bookmarkTarget || '';
        bar('submitting', 'SUBMITTING', 'Sending transaction to mailbox', target);
        var response = await fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': (document.cookie.match(/(?:^|; )csrftoken=([^;]*)/) || [])[1] || ''
            },
            body: '{}'
        });
        var data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Action could not be queued');
        }
        bar('queued', 'QUEUED', 'Mailbox #' + data.mailbox_id, data.action_path || target);
        await waitForMailbox(data.mailbox_id, data.action_path || target);
    }

    root.addEventListener('click', function (event) {
        var button = event.target.closest('[data-bookmark-type]');
        if (!button || button.disabled) return;
        var type = button.dataset.bookmarkType;
        var target = button.dataset.bookmarkTarget || '';
        if (type === 'popup_form') {
            var formKey = target.split('.').pop();
            var launcher = root.querySelector('[data-form="' + formKey + '"]');
            if (launcher) launcher.click();
            root.dispatchEvent(new CustomEvent('polysaas:bookmark', {
                detail: {type: type, target: target}
            }));
        } else if (type === 'direct_event') {
            button.disabled = true;
            fireDirect(button).catch(function (error) {
                bar('failed', 'FAILED', error.message, target);
            }).finally(function () {
                button.disabled = false;
            });
        } else if (type === 'mock_surface') {
            root.dispatchEvent(new CustomEvent('polysaas:bookmark', {
                detail: {type: type, target: target}
            }));
        }
    });
})();
