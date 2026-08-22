(function () {
    'use strict';

    var script = document.currentScript;
    var root = script && script.closest('.ps-slack-mock');
    if (!root || root.dataset.wireframeReady === '1') return;
    root.dataset.wireframeReady = '1';

    var result = root.querySelector('.ps-slack-mock__result');
    root.querySelectorAll('.ps-slack-mock__channel').forEach(function (button) {
        button.addEventListener('click', function () {
            root.querySelectorAll('.ps-slack-mock__channel').forEach(function (item) {
                item.classList.remove('is-active');
            });
            button.classList.add('is-active');
            root.querySelector('.ps-slack-mock__channel-title').textContent =
                button.dataset.channel;
            result.textContent = 'Viewing #' + button.dataset.channel + ' — wireframe';
        });
    });

    function getCookie(name) {
        var prefix = name + '=';
        var parts = document.cookie ? document.cookie.split(';') : [];
        for (var i = 0; i < parts.length; i += 1) {
            var value = parts[i].trim();
            if (value.indexOf(prefix) === 0) {
                return decodeURIComponent(value.substring(prefix.length));
            }
        }
        return '';
    }

    function updateBar(path, status, eventText) {
        var barPath = document.getElementById('pss-action-path');
        var barStatus = document.getElementById('pss-orch-status');
        var barEvent = document.getElementById('pss-orch-event');
        if (barPath) barPath.textContent = path;
        if (barStatus) barStatus.textContent = status;
        if (barEvent) {
            barEvent.style.display = 'inline-block';
            barEvent.textContent = eventText;
        }
    }

    function outcomeText(kind, mailboxResult) {
        var orchestration = mailboxResult && mailboxResult.result;
        var atomic = orchestration && orchestration.results && orchestration.results[0];
        if (!atomic) {
            return orchestration && orchestration.status === 'no_instruction'
                ? 'No consumer is bound to this webhook'
                : 'Webhook processed without a consumer result';
        }
        if (atomic.status !== 'success') {
            return 'Consumer failed: ' + (atomic.detail || atomic.error || 'unknown error');
        }
        if (kind === 'contact') {
            return 'Odoo contact ready — partner #' + atomic.partner_id;
        }
        return 'Odoo draft quotation ' + (atomic.order_name || ('#' + atomic.order_id));
    }

    async function waitForMailbox(mailboxId, kind, path) {
        var statusBase = root.dataset.statusUrl;
        for (var attempt = 0; attempt < 20; attempt += 1) {
            await new Promise(function (resolve) { window.setTimeout(resolve, 1000); });
            var response = await fetch(statusBase + mailboxId + '/', {
                credentials: 'same-origin',
                headers: {'Accept': 'application/json'}
            });
            var data = await response.json();
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Could not read mailbox status');
            }
            if (data.status === 'failed' || data.status === 'expired') {
                throw new Error(data.error || ('Mailbox ' + data.status));
            }
            if (data.status === 'processed') {
                var text = outcomeText(kind, data);
                result.textContent = text + ' · ' + path;
                updateBar(path, 'POST ' + path + ' — processed', text);
                return;
            }
        }
        throw new Error('Consumer did not finish within 20 seconds');
    }

    root.querySelectorAll('[data-demo]').forEach(function (button) {
        button.addEventListener('click', async function () {
            var kind = button.dataset.demo;
            var path = kind === 'sale'
                ? '/events/slack/webhook/sale'
                : (kind === 'contact'
                    ? '/events/slack/webhook/contact'
                    : '/mock/slack/thread/1');
            if (kind === 'browse') {
                result.textContent = 'Sample thread opened · ' + path;
                return;
            }

            var triggerUrl = kind === 'sale'
                ? root.dataset.saleUrl
                : root.dataset.contactUrl;
            button.disabled = true;
            result.textContent = 'Queueing real ' + kind + ' webhook…';
            updateBar(path, 'POST ' + path + ' — queueing', 'Waiting for mailbox');
            try {
                var response = await fetch(triggerUrl, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: '{}'
                });
                var data = await response.json();
                if (!response.ok || !data.success) {
                    throw new Error(data.error || 'Webhook could not be queued');
                }
                result.textContent = 'Mailbox #' + data.mailbox_id + ' queued · ' + path;
                updateBar(path, 'POST ' + path + ' — queued', 'Mailbox #' + data.mailbox_id);
                await waitForMailbox(data.mailbox_id, kind, path);
            } catch (error) {
                result.textContent = 'Live webhook failed — ' + error.message;
                updateBar(path, 'POST ' + path + ' — failed', error.message);
            } finally {
                button.disabled = false;
            }
        });
    });
})();
