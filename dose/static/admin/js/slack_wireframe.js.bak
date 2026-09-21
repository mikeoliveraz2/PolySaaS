// THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
// BINGO: Slack Odoo contact/sale forms — 2026-08-25
// BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
(function () {
    'use strict';

    var script = document.currentScript;
    var root = script && script.closest('.ps-slack-mock');
    if (!root || root.dataset.wireframeReady === '1') return;
    root.dataset.wireframeReady = '1';

    var result = root.querySelector('.ps-slack-mock__result');
    var messagesEl = root.querySelector('#ps-slack-messages');
    var composer = root.querySelector('#ps-slack-composer');
    var seenIds = {};

    root.querySelectorAll('.ps-slack-mock__channel').forEach(function (button) {
        button.addEventListener('click', function () {
            root.querySelectorAll('.ps-slack-mock__channel').forEach(function (item) {
                item.classList.remove('is-active');
            });
            button.classList.add('is-active');
            root.querySelector('.ps-slack-mock__channel-title').textContent =
                button.dataset.channel;
            result.textContent = 'Viewing #' + button.dataset.channel + ' — wireframe';
            if (composer) {
                composer.querySelector('input').placeholder = 'Message #' + button.dataset.channel;
            }
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

    function updateBar(path, status, eventText, state, extra) {
        extra = extra || {};
        if (window.PolySaaSTransactionBar) {
            window.PolySaaSTransactionBar.update({
                path: path,
                label: status,
                detail: eventText,
                state: state || 'idle',
                result: extra.result,
                match: extra.match
            });
            return;
        }
        var barStatus = document.getElementById('pss-orch-status');
        var barPath = document.getElementById('pss-action-path');
        var barEvent = document.getElementById('pss-orch-event');
        if (barPath) barPath.textContent = path;
        if (barStatus) barStatus.textContent = status;
        if (barEvent) barEvent.textContent = eventText;
    }

    function appendMessage(author, text, opts) {
        opts = opts || {};
        if (!messagesEl || !text) return;
        if (opts.id) {
            if (seenIds[opts.id]) return;
            seenIds[opts.id] = true;
        }
        var row = document.createElement('div');
        row.className = 'ps-slack-mock__message';
        if (opts.id) row.dataset.messageId = String(opts.id);
        var initial = (author || 'P').charAt(0).toUpperCase();
        var avatarClass = 'ps-slack-mock__avatar' + (opts.bot ? ' is-bot' : '');
        row.innerHTML =
            '<div class="' + avatarClass + '">' + initial + '</div>' +
            '<div><div><span class="ps-slack-mock__name"></span>' +
            '<span class="ps-slack-mock__time"></span></div>' +
            '<p class="ps-slack-mock__body"></p></div>';
        row.querySelector('.ps-slack-mock__name').textContent = author || 'PolySaaS';
        row.querySelector('.ps-slack-mock__time').textContent = opts.time || 'just now';
        row.querySelector('.ps-slack-mock__body').textContent = text;
        messagesEl.appendChild(row);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function renderServerMessages(items) {
        (items || []).forEach(function (item) {
            appendMessage(
                item.author || 'PolySaaS',
                item.message,
                {
                    id: item.id,
                    bot: !item.author || item.author === 'PolySaaS',
                    time: (item.created_at || '').replace('T', ' ').slice(0, 19)
                }
            );
        });
    }

    async function refreshMessages() {
        var url = root.dataset.messagesUrl;
        if (!url) return;
        var response = await fetch(url, {
            credentials: 'same-origin',
            headers: {'Accept': 'application/json'}
        });
        var data = await response.json();
        if (response.ok && data.success) {
            renderServerMessages(data.messages);
        }
    }

    function matchLine(orchestration, path) {
        if (window.PolySaaSTransactionBar && window.PolySaaSTransactionBar.describeMatch) {
            return window.PolySaaSTransactionBar.describeMatch(orchestration, path);
        }
        return '';
    }

    function transactionOutcome(kind, mailboxResult) {
        var orchestration = mailboxResult && mailboxResult.result;
        var atomic = orchestration && orchestration.results && orchestration.results[0];
        var match = matchLine(orchestration, mailboxResult && mailboxResult.action_path);
        if (!atomic) {
            var noConsumer = orchestration && (
                orchestration.status === 'no_instruction' || orchestration.matched === 0
            );
            return {
                state: noConsumer ? 'no_consumer' : 'error',
                label: noConsumer ? 'NO CONSUMER' : 'NO RESULT',
                text: noConsumer
                    ? 'No consumer is bound to this webhook'
                    : 'Webhook processed without a consumer result',
                match: match,
                result: orchestration
            };
        }
        if (atomic.status !== 'success') {
            return {
                state: 'error',
                label: 'FAILED',
                text: 'Consumer failed: ' + (atomic.detail || atomic.error || 'unknown error'),
                match: match,
                result: orchestration
            };
        }
        if (kind === 'contact') {
            var partnerName = atomic.name || '';
            return {
                state: 'success',
                label: 'SUCCESS',
                text: partnerName
                    ? ('Shown in Odoo Contacts — ' + partnerName + ' (#' + atomic.partner_id + ')')
                    : ('Shown in Odoo Contacts — partner #' + atomic.partner_id),
                match: match,
                result: orchestration
            };
        }
        return {
            state: 'success',
            label: 'SUCCESS',
            text: 'Shown in Odoo Sales — ' + (atomic.order_name || ('quotation #' + atomic.order_id)),
            match: match,
            result: orchestration
        };
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
                updateBar(
                    path,
                    data.status === 'expired' ? 'EXPIRED' : 'FAILED',
                    data.error || ('Mailbox ' + data.status),
                    'error'
                );
                throw new Error(data.error || ('Mailbox ' + data.status));
            }
            if (data.status === 'pending') {
                updateBar(path, 'PENDING', 'Mailbox #' + mailboxId + ' is waiting', 'queued', {
                    match: 'Waiting for consumer on ' + path
                });
            } else if (data.status === 'claimed') {
                updateBar(path, 'PROCESSING', 'Consumer is running', 'processing', {
                    match: 'Matching ' + path
                });
            }
            if (data.status === 'processed') {
                var outcome = transactionOutcome(kind, data);
                result.textContent = outcome.text + ' · ' + path;
                updateBar(path, outcome.label, outcome.text, outcome.state, {
                    match: outcome.match,
                    result: outcome.result
                });
                appendMessage('PolySaaS', outcome.text, {bot: true});
                await refreshMessages();
                return;
            }
        }
        throw new Error('Consumer did not finish within 20 seconds');
    }

    function formPayload(scope) {
        var data = {};
        if (!scope) return data;
        scope.querySelectorAll('input[name], select[name], textarea[name]').forEach(function (el) {
            if (el.disabled) return;
            if (el.type === 'radio' && !el.checked) return;
            if (el.type === 'checkbox' && !el.checked) return;
            var value = (el.value || '').trim();
            if (value) data[el.name] = value;
        });
        return data;
    }

    var modalArmedAt = 0;
    var armTimer = null;

    function isModalArmed() {
        return Date.now() >= modalArmedAt;
    }

    function openForm(kind) {
        closeForms();
        var modal = root.querySelector('#ps-slack-modal-' + kind);
        if (!modal) return;
        // Defer paint until after the opening click fully settles, then arm inputs.
        window.setTimeout(function () {
            modal.classList.add('is-open', 'is-arming');
            modal.removeAttribute('hidden');
            modalArmedAt = Date.now() + 350;
            if (armTimer) window.clearTimeout(armTimer);
            armTimer = window.setTimeout(function () {
                modal.classList.remove('is-arming');
                var first = modal.querySelector('.ps-odoo-contact__name, .ps-odoo-sale__customer') ||
                    modal.querySelector('input:not([type="radio"]):not([type="checkbox"]), textarea');
                if (first) first.focus();
            }, 350);
        }, 0);
    }

    function closeForms() {
        if (armTimer) {
            window.clearTimeout(armTimer);
            armTimer = null;
        }
        modalArmedAt = 0;
        root.querySelectorAll('.ps-slack-mock__modal').forEach(function (modal) {
            modal.classList.remove('is-open', 'is-arming');
            modal.setAttribute('hidden', 'hidden');
        });
    }

    async function queueWebhook(kind, payload) {
        var path = kind === 'sale'
            ? '/events/slack/webhook/sale'
            : '/events/slack/webhook/contact';
        var triggerUrl = kind === 'sale'
            ? root.dataset.saleUrl
            : root.dataset.contactUrl;
        result.textContent = 'Queueing real ' + kind + ' webhook…';
        updateBar(path, 'SUBMITTING', 'Sending transaction to mailbox', 'queueing', {
            match: 'POST REQ ' + path
        });
        var response = await fetch(triggerUrl, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(payload || {})
        });
        var data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Webhook could not be queued');
        }
        result.textContent = 'Mailbox #' + data.mailbox_id + ' queued · ' + path;
        updateBar(path, 'QUEUED', 'Mailbox #' + data.mailbox_id, 'queued', {
            match: 'POST REQ ' + path
        });
        return {
            mailboxId: data.mailbox_id,
            path: path
        };
    }

    function setFormStatus(kind, text) {
        var statusEl = root.querySelector('[data-form-status="' + kind + '"]');
        if (statusEl) statusEl.textContent = text || '';
    }

    async function submitKind(kind) {
        var modal = root.querySelector('#ps-slack-modal-' + kind);
        var form = root.querySelector('#ps-slack-form-' + kind);
        var payload = formPayload(modal || form);
        var path = kind === 'sale'
            ? '/events/slack/webhook/sale'
            : '/events/slack/webhook/contact';
        var savingLabel = kind === 'sale'
            ? 'Saving sale to mailbox'
            : 'Saving contact to mailbox';
        if (kind === 'contact' && !payload.name) {
            result.textContent = 'Name is required for contact';
            setFormStatus(kind, 'Name is required');
            updateBar(path, 'FAILED', 'Name is required', 'error');
            return;
        }
        if (kind === 'sale' && (!payload.partner_name || !payload.order_reference)) {
            result.textContent = 'Customer name and order reference are required';
            setFormStatus(kind, 'Customer and order reference required');
            updateBar(path, 'FAILED', 'Customer name and order reference are required', 'error');
            return;
        }
        var submitBtn = root.querySelector('[data-form-submit="' + kind + '"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.dataset.originalLabel = submitBtn.textContent;
            submitBtn.textContent = 'Saving…';
        }
        setFormStatus(kind, 'Saving…');
        updateBar(path, 'SUBMITTING', savingLabel, 'queueing', {
            match: 'POST REQ ' + path
        });
        try {
            appendMessage(
                'you',
                kind === 'sale'
                    ? ('New sale: ' + payload.partner_name + ' / ' + payload.order_reference)
                    : ('newpolysaascontact ' + payload.name),
                {}
            );
            var queued = await queueWebhook(kind, payload);
            setFormStatus(kind, queued && queued.mailboxId
                ? ('Queued mailbox #' + queued.mailboxId)
                : 'Queued');
            if (form) {
                form.querySelectorAll('input[name], select[name], textarea[name]').forEach(function (el) {
                    if (el.type === 'radio' || el.type === 'checkbox') return;
                    if (el.tagName === 'SELECT') {
                        el.selectedIndex = 0;
                        return;
                    }
                    el.value = '';
                });
            }
            closeForms();
            if (queued && queued.mailboxId) {
                await waitForMailbox(queued.mailboxId, kind, queued.path);
            }
        } catch (error) {
            result.textContent = 'Live webhook failed — ' + error.message;
            setFormStatus(kind, error.message);
            updateBar(path, 'FAILED', error.message, 'error');
            appendMessage('PolySaaS', 'Live webhook failed — ' + error.message, {bot: true});
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = submitBtn.dataset.originalLabel || 'Save';
            }
        }
    }

    function updateContactAvatar() {
        var avatar = root.querySelector('[data-contact-avatar]');
        var nameInput = root.querySelector('.ps-odoo-contact__name');
        if (!avatar || !nameInput) return;
        var icon = avatar.querySelector('.ps-odoo-contact__avatar-icon');
        var letter = avatar.querySelector('.ps-odoo-contact__avatar-letter');
        var initial = (nameInput.value || '').trim().charAt(0).toUpperCase();
        if (letter) {
            letter.textContent = initial;
            if (initial) letter.removeAttribute('hidden');
            else letter.setAttribute('hidden', 'hidden');
        }
        if (icon) icon.style.display = initial ? 'none' : '';
    }

    var contactName = root.querySelector('.ps-odoo-contact__name');
    if (contactName) {
        contactName.addEventListener('input', updateContactAvatar);
        updateContactAvatar();
    }

    root.querySelectorAll('[data-form]').forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            event.stopPropagation();
            openForm(button.dataset.form);
        });
    });

    root.querySelectorAll('[data-modal-dismiss]').forEach(function (el) {
        el.addEventListener('click', function (event) {
            event.preventDefault();
            event.stopPropagation();
            if (!isModalArmed()) return;
            closeForms();
            result.textContent = 'Ready — form cancelled';
        });
    });

    root.addEventListener('click', function (event) {
        var button = event.target.closest('[data-form-submit]');
        if (!button || !root.contains(button)) return;
        event.preventDefault();
        event.stopPropagation();
        submitKind(button.getAttribute('data-form-submit'));
    });

    // Capture-phase: Enter inside an open modal must never submit Jazzmin/composer forms
    // (that reloads the page and looks like the modal "vanished" mid-fill).
    document.addEventListener('keydown', function (event) {
        if (!root.querySelector('.ps-slack-mock__modal.is-open')) return;
        if (!root.contains(event.target)) return;
        if (event.key === 'Enter' && event.target && event.target.tagName !== 'TEXTAREA') {
            event.preventDefault();
            event.stopPropagation();
        }
    }, true);

    // Composer must not steal Enter / submit while a modal is open.
    if (composer) {
        composer.addEventListener('submit', function (event) {
            if (root.querySelector('.ps-slack-mock__modal.is-open')) {
                event.preventDefault();
                event.stopPropagation();
            }
        }, true);
    }

    root.querySelectorAll('[data-demo]').forEach(function (button) {
        button.addEventListener('click', function () {
            if (button.dataset.demo !== 'browse') return;
            result.textContent = 'Sample thread opened · /mock/slack/thread/1';
            appendMessage('PolySaaS', 'Sample thread opened in the wireframe.', {bot: true});
        });
    });

    if (composer) {
        composer.addEventListener('submit', async function (event) {
            event.preventDefault();
            var input = composer.querySelector('input[name="message"]');
            var text = (input && input.value || '').trim();
            if (!text) return;
            var postUrl = root.dataset.postUrl;
            composer.querySelector('button').disabled = true;
            try {
                var response = await fetch(postUrl, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({message: text})
                });
                var data = await response.json();
                if (!response.ok || !data.success) {
                    throw new Error(data.error || 'Could not send message');
                }
                input.value = '';
                if (data.message) {
                    appendMessage(
                        data.message.author || 'you',
                        data.message.message,
                        {id: data.message.id}
                    );
                }
                renderServerMessages(data.messages);
                result.textContent = 'Message sent';
            } catch (error) {
                result.textContent = 'Send failed — ' + error.message;
            } finally {
                composer.querySelector('button').disabled = false;
                if (input) input.focus();
            }
        });
    }

    refreshMessages().catch(function () {});
})();
