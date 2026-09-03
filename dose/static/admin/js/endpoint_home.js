// THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
// BINGO: Slack producer/consumer home — 2026-08-24
// BINGO: Slack → Odoo + HubSpot dual-feed — 2026-08-28
// FIX 2026-08-27 (owner-approved): sync direct_event (Odoo Invoices → CallBackData).
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
        bar('submitting', 'SUBMITTING', 'Sending transaction', target);
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
        // Sync direct_event (e.g. Odoo Invoices) — no mailbox round-trip.
        if (data.sync || !data.mailbox_id) {
            bar(
                'success',
                'SUCCESS',
                data.detail || ('Completed ' + (data.action_path || target)),
                data.action_path || target
            );
            if (data.popup === 'callback_record') {
                openCallbackDialog(data);
            }
            return;
        }
        bar('queued', 'QUEUED', 'Mailbox #' + data.mailbox_id, data.action_path || target);
        await waitForMailbox(data.mailbox_id, data.action_path || target);
    }

    var callbackDialog = root.querySelector('[data-callback-dialog]');
    var callbackTitle = root.querySelector('[data-callback-title]');
    var callbackSub = root.querySelector('[data-callback-sub]');
    var callbackMeta = root.querySelector('[data-callback-meta]');
    var callbackBody = root.querySelector('[data-callback-body]');

    // BINGO: Unified Endpoint Workspace — 2026-09-01
    var table = window.PolySaaSTable;
    var esc = table.esc;

    /* Envelope for a direct_event result. Falls back to the deprecated
     * per-vendor keys so an older payload still renders. */
    function resolveEnvelope(data) {
        if (data.envelope && Array.isArray(data.envelope.rows)) return data.envelope;
        var legacy = data.list_kind
            || (String(data.action_path || data.matching_event_key || '').indexOf('list_contacts') !== -1 && 'contacts')
            || (String(data.action_path || data.matching_event_key || '').indexOf('list_sales') !== -1 && 'sales')
            || 'invoices';
        return {
            status: data.status || 'success',
            rows: Array.isArray(data[legacy]) ? data[legacy] : [],
            columns: [],
            empty_message: 'Nothing was returned. The CallBackData row was still saved with count 0.'
        };
    }

    function openCallbackDialog(data) {
        if (!callbackDialog || !callbackBody) return;
        var envelope = resolveEnvelope(data);
        var rows = envelope.rows;
        var count = data.count != null ? data.count : rows.length;
        var odoo = data.odoo || {};
        var hubspot = data.hubspot || {};
        if (callbackTitle) {
            callbackTitle.textContent = data.callback_description || 'CallBackData record';
        }
        if (callbackSub) {
            callbackSub.textContent = data.detail || '';
        }
        if (callbackMeta) {
            var metaHtml =
                '<div><span>Event</span><strong>' + esc(data.matching_event_key || data.action_path || '') + '</strong></div>' +
                '<div><span>Status</span><strong>' + esc(data.status || 'success') + '</strong></div>' +
                '<div><span>Callback #</span><strong>' + esc(data.callback_id != null ? data.callback_id : '—') + '</strong></div>' +
                '<div><span>Count</span><strong>' + esc(count) + '</strong></div>';
            if (hubspot.portal_id || hubspot.token_type) {
                metaHtml +=
                    '<div><span>HubSpot portal</span><strong>' + esc(hubspot.portal_id || '—') + '</strong></div>' +
                    '<div><span>Token</span><strong>' + esc(hubspot.token_type || '—') + '</strong></div>';
            } else {
                metaHtml +=
                    '<div><span>Odoo DB</span><strong>' + esc(odoo.db || '—') + '</strong></div>' +
                    '<div><span>Odoo URL</span><strong>' + esc(odoo.url || '—') + '</strong></div>';
            }
            callbackMeta.innerHTML = metaHtml;
        }
        if (!rows.length) {
            callbackBody.innerHTML =
                '<div class="polysaas-callback-dialog__empty">' +
                esc(envelope.empty_message || 'Nothing was returned.') + '</div>';
        } else {
            callbackBody.innerHTML = table.render(envelope, {
                wrapClass: 'polysaas-callback-dialog__table-wrap',
                tableClass: 'polysaas-callback-dialog__table'
            });
        }
        callbackDialog.hidden = false;
        callbackDialog.removeAttribute('hidden');
        try {
            callbackDialog.scrollIntoView({behavior: 'smooth', block: 'nearest'});
        } catch (err) {
            callbackDialog.scrollIntoView();
        }
    }

    function closeCallbackPanel() {
        if (!callbackDialog) return;
        callbackDialog.hidden = true;
        callbackDialog.setAttribute('hidden', 'hidden');
    }

    root.querySelectorAll('[data-callback-close]').forEach(function (btn) {
        btn.addEventListener('click', closeCallbackPanel);
    });

    root.addEventListener('click', function (event) {
        var runBtn = event.target.closest('[data-form]');
        if (runBtn && root.contains(runBtn) && !runBtn.closest('.ps-slack-mock')) {
            event.preventDefault();
            var formKind = runBtn.dataset.form;
            var launcher = root.querySelector(
                '.polysaas-endpoint-home__form-host [data-form="' + formKind + '"]'
            );
            if (launcher) launcher.click();
            return;
        }

        var pairBtn = event.target.closest('[data-pair-producer]');
        if (pairBtn && root.contains(pairBtn)) {
            event.preventDefault();
            openPairDialog(pairBtn);
            return;
        }

        var button = event.target.closest('[data-bookmark-type]');
        if (!button || button.disabled) return;
        var type = button.dataset.bookmarkType;
        var target = button.dataset.bookmarkTarget || '';
        if (type === 'popup_form') {
            var formKey = target.split('.').pop();
            var popupLauncher = root.querySelector(
                '.polysaas-endpoint-home__form-host [data-form="' + formKey + '"]'
            );
            if (popupLauncher) popupLauncher.click();
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

    var pairDialog = root.querySelector('[data-pair-dialog]');
    var pairChoices = root.querySelector('[data-pair-choices]');
    var pairTitle = root.querySelector('[data-pair-title]');
    var pairSave = root.querySelector('[data-pair-save]');
    var activeEventKey = '';
    var initiallyPaired = {};

    function openPairDialog(button) {
        if (!pairDialog || !pairChoices) return;
        activeEventKey = button.dataset.eventKey || '';
        initiallyPaired = {};
        (button.dataset.pairedIds || '').split(',').forEach(function (id) {
            id = (id || '').trim();
            if (id) initiallyPaired[id] = true;
        });
        if (pairTitle) {
            pairTitle.textContent = 'Pair: ' + activeEventKey;
        }
        pairChoices.innerHTML = '';
        root.querySelectorAll('[data-consumer-list] [data-consumer-id]').forEach(function (row) {
            var id = row.getAttribute('data-consumer-id');
            var titleEl = row.querySelector('.polysaas-consumer-list__title');
            var label = document.createElement('label');
            var input = document.createElement('input');
            input.type = 'checkbox';
            input.value = id;
            input.checked = !!initiallyPaired[id];
            label.appendChild(input);
            label.appendChild(document.createTextNode(' ' + ((titleEl && titleEl.textContent) || ('Consumer #' + id))));
            pairChoices.appendChild(label);
        });
        if (typeof pairDialog.showModal === 'function') {
            pairDialog.showModal();
        } else {
            pairDialog.setAttribute('open', 'open');
        }
    }

    if (pairSave) {
        pairSave.addEventListener('click', function () {
            var pairUrl = root.dataset.pairUrl || '';
            if (!pairUrl || !activeEventKey) return;
            var selected = [];
            pairChoices.querySelectorAll('input[type="checkbox"]').forEach(function (box) {
                if (box.checked) selected.push(box.value);
            });
            var toPair = selected.filter(function (id) { return !initiallyPaired[id]; });
            var toUnpair = Object.keys(initiallyPaired).filter(function (id) {
                return selected.indexOf(id) === -1;
            });
            pairSave.disabled = true;
            Promise.resolve()
                .then(function () {
                    if (!toPair.length) return null;
                    return fetch(pairUrl, {
                        method: 'POST',
                        credentials: 'same-origin',
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                            'X-CSRFToken': (document.cookie.match(/(?:^|; )csrftoken=([^;]*)/) || [])[1] || ''
                        },
                        body: JSON.stringify({
                            action: 'pair',
                            event_key: activeEventKey,
                            consumer_ids: toPair
                        })
                    }).then(function (r) { return r.json().then(function (d) { return {ok: r.ok, data: d}; }); });
                })
                .then(function (first) {
                    if (first && (!first.ok || !first.data.success)) {
                        throw new Error((first.data && first.data.error) || 'Pair failed');
                    }
                    if (!toUnpair.length) return null;
                    return fetch(pairUrl, {
                        method: 'POST',
                        credentials: 'same-origin',
                        headers: {
                            'Accept': 'application/json',
                            'Content-Type': 'application/json',
                            'X-CSRFToken': (document.cookie.match(/(?:^|; )csrftoken=([^;]*)/) || [])[1] || ''
                        },
                        body: JSON.stringify({
                            action: 'unpair',
                            event_key: activeEventKey,
                            consumer_ids: toUnpair
                        })
                    }).then(function (r) { return r.json().then(function (d) { return {ok: r.ok, data: d}; }); });
                })
                .then(function (second) {
                    if (second && (!second.ok || !second.data.success)) {
                        throw new Error((second.data && second.data.error) || 'Unpair failed');
                    }
                    window.location.reload();
                })
                .catch(function (error) {
                    window.alert(error.message || 'Could not save pairing');
                })
                .finally(function () {
                    pairSave.disabled = false;
                });
        });
    }
})();

// Geronimo first-visit nudge (Option B: dismiss + action routing)
(function () {
    'use strict';

    var nudgeEl = document.querySelector('[data-geronimo-nudge]');
    if (!nudgeEl) return;

    // Restore dismissal state from session storage
    if (sessionStorage.getItem('geronimo_nudge_dismissed')) {
        document.body.classList.add('geronimo-nudge-dismissed');
    }

    // Handle close button
    var closeBtn = nudgeEl.querySelector('[data-dismiss-nudge]');
    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.add('geronimo-nudge-dismissed');
            sessionStorage.setItem('geronimo_nudge_dismissed', '1');
            // Mark nudge as seen in the session
            fetch(window.location.href, {
                method: 'POST',
                headers: {'X-Requested-With': 'XMLHttpRequest'},
                credentials: 'same-origin',
                body: JSON.stringify({action: 'mark_nudge_seen'})
            }).catch(function() { /* silently fail */ });
        });
    }

    // Handle action buttons
    nudgeEl.querySelectorAll('[data-nudge-action]').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            var action = this.dataset.nudgeAction;
            
            // Mark nudge as seen
            document.body.classList.add('geronimo-nudge-dismissed');
            sessionStorage.setItem('geronimo_nudge_dismissed', '1');

            if (action === 'open-data') {
                // Scroll to first data panel
                var firstPanel = document.querySelector('[data-polysaas-panel]');
                if (firstPanel) {
                    firstPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            } else if (action === 'browse-app') {
                // Click the Browse button
                var browseBtn = document.querySelector('.polysaas-endpoint-home__launch');
                if (browseBtn) {
                    browseBtn.click();
                }
            } else if (action === 'pair-consumer') {
                // Open pair dialog and scroll to Wiring section
                var wiringSection = document.querySelector('[data-pair-dialog]');
                if (wiringSection) {
                    wiringSection.showModal();
                } else {
                    // Fallback: scroll to Wiring details
                    var wiringDetails = document.querySelector('details[data-polysaas-wiring]');
                    if (wiringDetails) {
                        wiringDetails.open = true;
                        wiringDetails.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }
            }
        });
    });
})();
