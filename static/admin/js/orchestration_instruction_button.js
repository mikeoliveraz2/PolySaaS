// THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
// BINGO: Nextcloud in Jazzmin panel, no iframe — 2026-08-13
// BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
// Owner-approved 2026-09-22: Type 3 standing_by on invoice SPA (refine fires on Post, not list GET).
/**
 * Passthrough orchestration bar + green instruction button (new top-level window → Django admin).
 */
(function (global) {
    'use strict';

    function getBrowserPathname() {
        try {
            var a = document.createElement('a');
            a.href = global.location.href;
            return a.pathname || global.location.pathname || '/';
        } catch (e) {
            return global.location.pathname || '/';
        }
    }

    function isProxyPath(path) {
        var p = (path || '').toLowerCase();
        return p.indexOf('/pt/polysniff/') === 0 || p.indexOf('/pt/admin/') === 0;
    }

    function getUpstreamActionPathHint() {
        try {
            if (typeof global.__PS_GET_UPSTREAM_PATH === 'function') {
                return normalizeActionPath(global.__PS_GET_UPSTREAM_PATH());
            }
            if (typeof global.__PS_ORCH_ACTION_PATH === 'string' && global.__PS_ORCH_ACTION_PATH) {
                return normalizeActionPath(global.__PS_ORCH_ACTION_PATH);
            }
        } catch (e) {}
        return '';
    }

    function getCsrfToken() {
        var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        if (m) return decodeURIComponent(m[1]);
        var el = document.querySelector('[name=csrfmiddlewaretoken]');
        return el && el.value ? el.value : '';
    }

    function buildInstructionApiUrl(actionPath) {
        var path = (actionPath || '').trim();
        if (!path) return '';
        if (!path.startsWith('/')) path = '/' + path;
        var segments = path.replace(/^\/+|\/+$/g, '').split('/').filter(Boolean);
        if (!segments.length) return '/dose/api/orchestration-instruction/';
        return '/dose/api/orchestration-instruction/' + segments.map(encodeURIComponent).join('/') + '/';
    }

    function normalizeActionPath(actionPath) {
        var path = (actionPath || '').trim();
        if (!path) return '/';
        return path.startsWith('/') ? path : '/' + path;
    }

    function getActiveThemeInfo() {
        var dt = document.documentElement.getAttribute('data-ps-theme');
        var mode = '';
        try {
            mode = localStorage.getItem('ps_theme_mode') || '';
        } catch (e) {}
        if (mode === 'system') {
            mode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
                ? 'dark' : 'light';
        }
        if (!mode) {
            var mc = document.cookie.match(/(?:^|;\s*)display_mode=([^;]+)/);
            mode = mc ? decodeURIComponent(mc[1]).toLowerCase() : '';
        }
        if (!mode && dt) {
            mode = 'dark';
        }
        if (!mode) {
            mode = 'light';
        }
        var theme = dt || '';
        if (!theme) {
            var link = document.getElementById('jazzmin-theme');
            if (link && link.href) {
                var m = link.href.match(/bootswatch\/([^/]+)\//i);
                if (m && m[1]) {
                    theme = m[1].toLowerCase();
                }
            }
        }
        if (!theme) {
            try {
                theme = mode === 'dark'
                    ? (localStorage.getItem('ps_dark_theme') || 'darkly')
                    : (localStorage.getItem('ps_light_theme') || 'flatly');
            } catch (e) {
                theme = mode === 'dark' ? 'darkly' : 'flatly';
            }
        }
        return { theme: (theme || 'flatly').toLowerCase(), mode: mode };
    }

    function appendOrchTheme(url) {
        if (/[?&]orch_theme=/.test(url)) {
            return url;
        }
        var info = getActiveThemeInfo();
        var sep = url.indexOf('?') >= 0 ? '&' : '?';
        return url + sep + 'orch_theme=' + encodeURIComponent(info.theme)
            + '&orch_mode=' + encodeURIComponent(info.mode);
    }

    function resolveAdminUrl(data, fallbackPath) {
        var url;
        if (data && data.admin_url) {
            url = data.admin_url;
        } else {
            var actionPath = normalizeActionPath((data && data.action_path) || fallbackPath);
            if (data && data.mode === 'update' && data.id) {
                url = '/dose/orchestration/instruction/' + data.id + '/change/?_popup=1';
            } else {
                url = '/dose/orchestration/instruction/add/?requestpath='
                    + encodeURIComponent(actionPath)
                    + '&match_type=path&direction=REQ&requestmethod=GET&_popup=1';
            }
        }
        return appendOrchTheme(url);
    }

    function resolveFullAdminUrl(data, fallbackPath) {
        if (data && data.full_admin_url) return data.full_admin_url;
        var actionPath = normalizeActionPath((data && data.action_path) || fallbackPath);
        if (data && data.mode === 'update' && data.id) {
            return '/admin/dose/instruction/' + data.id + '/change/';
        }
        return '/admin/dose/instruction/add/?requestpath='
            + encodeURIComponent(actionPath)
            + '&match_type=path&direction=REQ&requestmethod=GET';
    }

    function injectModalStyles() {
        if (document.getElementById('ps-orch-instruction-modal-style')) return;
        var style = document.createElement('style');
        style.id = 'ps-orch-instruction-modal-style';
        style.textContent = [
            'body.ps-orch-modal-active{overflow:hidden!important;}',
            '#ps-orch-instruction-modal{display:none;position:fixed;inset:0;z-index:2147483646;',
            'align-items:center;justify-content:center;padding:24px;box-sizing:border-box;pointer-events:none;}',
            '#ps-orch-instruction-modal.ps-orch-modal-open{display:flex!important;pointer-events:auto!important;}',
            '#ps-orch-instruction-modal .ps-orch-modal-backdrop{position:absolute;inset:0;background:rgba(0,0,0,.6);}',
            '#ps-orch-instruction-modal .ps-orch-modal-panel{position:relative;z-index:1;width:min(960px,96vw);',
            'height:min(88vh,900px);background:#fff;border-radius:8px;box-shadow:0 12px 40px rgba(0,0,0,.35);',
            'display:flex;flex-direction:column;overflow:hidden;}',
            '#ps-orch-instruction-modal .ps-orch-modal-header{display:flex;align-items:center;justify-content:space-between;',
            'padding:10px 14px;background:#1e293b;color:#f8fafc;font-size:14px;font-weight:600;}',
            '#ps-orch-instruction-modal .ps-orch-modal-close{background:transparent;border:none;color:#f8fafc;',
            'font-size:22px;line-height:1;cursor:pointer;padding:0 4px;}'
        ].join('');
        document.head.appendChild(style);
    }

    function OrchestrationBar(config) {
        this.config = config;
        this._lastOrchPath = '';
        this._hooksInstalled = false;
    }

    OrchestrationBar.prototype.getPathInfo = function () {
        var browserPath = getBrowserPathname();
        var spaPath = global.location.pathname || browserPath;
        var hash = global.location.hash || '';
        var search = global.location.search || '';
        var m = browserPath.match(/\/pt\/admin\/[^/]+(\/.*)$/);
        var path = m ? m[1].replace(/\/$/, '') || '/' : spaPath;
        var hintedPath = getUpstreamActionPathHint();
        if (hintedPath && !isProxyPath(hintedPath)) {
            path = hintedPath;
        }
        if (!m && !isProxyPath(browserPath) && isProxyPath(path)) {
            path = browserPath;
        }
        if (!m && path.indexOf('/pt/admin/') === 0) path = '/';

        var menuId = '';
        var action = '';
        var base = path.split('?')[0].split('#')[0];
        var mm = base.match(/\/odoo\/[^/]+\/(\d+)(?:\/|$)/);
        if (mm) menuId = mm[1];

        var params = new URLSearchParams(search + hash.replace(/^#/, '?'));
        menuId = menuId || params.get('menu_id') || '';
        action = params.get('action') || '';
        if (!action && hash) {
            var hm = hash.match(/action=([^&]+)/);
            if (hm) action = decodeURIComponent(hm[1]);
        }

        return {
            path: path,
            pathOnly: path.split('?')[0].split('#')[0],
            fullPath: path + search + hash,
            menuId: menuId,
            action: action
        };
    };

    OrchestrationBar.prototype.setStatus = function (text, ok) {
        var el = document.getElementById(this.config.statusElId);
        if (!el) return;
        el.textContent = text;
        el.style.color = ok ? '#86efac' : (ok === false ? '#fca5a5' : '#93c5fd');
    };

    OrchestrationBar.prototype.showEvent = function (msg) {
        if (!this.config.eventElId) return;
        var el = document.getElementById(this.config.eventElId);
        if (!el) return;
        el.textContent = msg.indexOf('⚡') === 0 ? msg : ('⚡ ' + msg);
        el.style.display = 'inline';
        clearTimeout(el._t);
        el._t = setTimeout(function () { el.style.display = 'none'; }, 12000);
    };

    OrchestrationBar.prototype.notifyOrchestration = function (fullPath, pathOnly, force) {
        if (!pathOnly) return;
        // Ignore placeholder / root until Odoo SPA settles on a real action path.
        if (pathOnly === '/' || pathOnly === 'loading…' || pathOnly === 'detecting…' || pathOnly === '—') {
            return;
        }
        // force=true: re-hit navigate API on same path (first paint can race CSRF/tenant/seed).
        if (!force && pathOnly === this._lastOrchPath) return;
        var pathChanged = pathOnly !== this._lastOrchPath;
        this._lastOrchPath = pathOnly;
        var self = this;
        // Drop stale responses: early "/" notify must not overwrite a later invoice-path result.
        var seq = (this._orchNotifySeq = (this._orchNotifySeq || 0) + 1);
        var notifyPath = pathOnly;
        var stEl0 = document.getElementById(this.config.statusElId);
        if (pathChanged && stEl0) {
            stEl0.removeAttribute('data-ps-orch-result');
        }
        // Confirm result stays until the user navigates. Page GETs do not paint Type 3.
        if (stEl0 && stEl0.getAttribute('data-ps-orch-result') === '1') {
            return;
        }
        this.setStatus('checking…', null);
        // Send pathOnly (stable SPA path) — fullPath can include hash noise.
        fetch('/dose/api/orchestration-navigate/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ path: pathOnly, method: 'GET' })
        }).then(function (r) {
            if (seq !== self._orchNotifySeq) return null;
            if (!r.ok) {
                self.setStatus('API error (' + r.status + ')', false);
                self.showEvent('orchestration API failed (' + r.status + ')');
                return null;
            }
            return r.json();
        }).then(function (data) {
            if (!data || seq !== self._orchNotifySeq) return;
            // Path changed while in flight — discard.
            if (notifyPath !== self._lastOrchPath) return;
            if (data.status === 'no_tenant') {
                self.setStatus('no tenant', false);
                self.showEvent('orchestration: no tenant');
                return;
            }
            var stNow = document.getElementById(self.config.statusElId);
            if (stNow && stNow.getAttribute('data-ps-orch-result') === '1') {
                return;
            }
            var matched = data.matched || 0;
            var saved = data.callback_saved || 0;
            if (matched > 0) {
                self.setStatus('matched ' + matched + ', saved ' + saved, saved > 0);
                self.showEvent('matched ' + matched + ' — CallBackData saved: ' + saved);
                self.updateButtonLabel(true);
            } else {
                self.setStatus('waiting…', null);
                self.updateButtonLabel(false);
            }
        }).catch(function () {
            if (seq !== self._orchNotifySeq) return;
            self.setStatus('API error', false);
            self.showEvent('orchestration API failed');
        });
    };

    OrchestrationBar.prototype.updateButtonLabel = function (hasMatch) {
        if (!this.config.btnId) return;
        var btn = document.getElementById(this.config.btnId);
        if (!btn) return;
        btn.textContent = hasMatch ? 'Edit Orchestration Instruction' : '+ Insert Orchestration Instruction';
    };

    OrchestrationBar.prototype.updateBar = function (forceNotify) {
        var info = this.getPathInfo();
        var pathEl = document.getElementById(this.config.pathElId);
        var menuEl = this.config.menuElId ? document.getElementById(this.config.menuElId) : null;
        var actionEl = this.config.actionElId ? document.getElementById(this.config.actionElId) : null;

        if (pathEl) pathEl.textContent = info.pathOnly || '—';
        if (menuEl) menuEl.textContent = info.menuId || '—';
        if (actionEl) actionEl.textContent = info.action || '—';

        if (forceNotify || info.pathOnly !== this._lastOrchPath) {
            this.notifyOrchestration(info.fullPath, info.pathOnly, !!forceNotify);
        }
    };

    OrchestrationBar.prototype.installHistoryHooks = function () {
        if (this._hooksInstalled && this.config.singleHookInstall) return;
        var self = this;
        var _pushState = history.pushState;
        var _replaceState = history.replaceState;
        history.pushState = function () {
            var r = _pushState.apply(history, arguments);
            self.updateBar(true);
            return r;
        };
        history.replaceState = function () {
            var r = _replaceState.apply(history, arguments);
            self.updateBar(true);
            return r;
        };
        global.addEventListener('popstate', function () { self.updateBar(true); });
        this._hooksInstalled = true;
    };

    OrchestrationBar.prototype.ensureModalMounted = function () {
        injectModalStyles();
        var modal = document.getElementById('ps-orch-instruction-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'ps-orch-instruction-modal';
            modal.setAttribute('aria-hidden', 'true');
            modal.setAttribute('role', 'dialog');
            modal.innerHTML = [
                '<div class="ps-orch-modal-backdrop" data-orch-modal-close></div>',
                '<div class="ps-orch-modal-panel">',
                '<div class="ps-orch-modal-header">',
                '<span id="ps-orch-modal-title">Orchestration Instruction</span>',
                '<span style="display:flex;align-items:center;gap:12px;">',
                '<a id="ps-orch-modal-open-tab" href="#" target="_blank" rel="noopener" ',
                'style="color:#93c5fd;font-size:12px;font-weight:500;text-decoration:none;">Open in new tab</a>',
                '<button type="button" class="ps-orch-modal-close" id="ps-orch-modal-close" aria-label="Close">&times;</button>',
                '</span></div>',
                '<p style="margin:24px;font:14px/1.4 system-ui,sans-serif;">Instruction form opens in a new window.</p>',
                '</div>'
            ].join('');
            document.body.appendChild(modal);
            this.bindModalClose();
        } else if (modal.parentNode !== document.body) {
            document.body.appendChild(modal);
        }
        return modal;
    };

    OrchestrationBar.prototype.openInstructionModal = function (adminUrl, mode, actionPath, fullAdminUrl) {
        var url = fullAdminUrl || adminUrl;
        global.open(url, '_blank', 'noopener,width=1024,height=820');
        this.showEvent(mode === 'update'
            ? 'Edit instruction form opened in new window'
            : 'Create instruction form opened in new window');
        console.log('[ORCH-BTN] top-level window →', url);
    };

    OrchestrationBar.prototype.closeInstructionModal = function () {
        var modal = document.getElementById('ps-orch-instruction-modal');
        if (!modal) return;
        modal.classList.remove('ps-orch-modal-open');
        modal.style.display = 'none';
        modal.style.pointerEvents = 'none';
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('ps-orch-modal-active');
        this.updateBar(true);
    };

    OrchestrationBar.prototype.handleInstructionButtonClick = function (e) {
        if (this._openingInstruction) return;
        this._openingInstruction = true;
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }
        var pathEl = document.getElementById(this.config.pathElId);
        var path = pathEl ? pathEl.textContent.trim() : this.getPathInfo().pathOnly;
        if (!path || path === 'loading…' || path === 'detecting…' || path === '—') {
            path = this.getPathInfo().pathOnly;
        }
        if (!path) {
            this.showEvent('No action path found');
            this._openingInstruction = false;
            return;
        }

        var apiUrl = buildInstructionApiUrl(path);
        var self = this;
        var btn = document.getElementById(this.config.btnId);
        var btnLabel = btn ? btn.textContent : '';
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Opening…';
        }
        console.log('[ORCH-BTN] click →', apiUrl);
        fetch(apiUrl, {
            method: 'GET',
            credentials: 'same-origin',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        }).then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        }).then(function (data) {
            console.log('[ORCH-BTN] API response', data);
            if (data.status === 'no_tenant') {
                self.showEvent('No tenant — log in again');
                return;
            }
            var adminUrl = resolveAdminUrl(data, path);
            var fullAdminUrl = resolveFullAdminUrl(data, path);
            var mode = (data && data.mode) || 'create';
            var actionPath = (data && data.action_path) || path;
            console.log('[ORCH-BTN] admin URL →', adminUrl);
            self.openInstructionModal(adminUrl, mode, actionPath, fullAdminUrl);
        }).catch(function (err) {
            console.error('[ORCH-BTN]', err);
            var fallbackUrl = resolveAdminUrl(null, path);
            var fallbackFull = resolveFullAdminUrl(null, path);
            console.log('[ORCH-BTN] API failed — fallback URL →', fallbackUrl);
            self.openInstructionModal(fallbackUrl, 'create', path, fallbackFull);
            self.showEvent('Opened form (API fallback)');
        }).finally(function () {
            self._openingInstruction = false;
            if (btn) {
                btn.disabled = false;
                btn.textContent = btnLabel || '+ Insert Orchestration Instruction';
            }
        });
    };

    OrchestrationBar.prototype.bindInstructionButton = function () {
        if (!this.config.btnId || global.__psOrchInstructionBtnBound) return;
        var self = this;
        global.__psOrchInstructionBtnBound = true;
        global.__psOrchBarInstance = this;

        document.addEventListener('click', function (e) {
            var btn = e.target && e.target.closest
                ? e.target.closest('#' + self.config.btnId)
                : null;
            if (!btn) return;
            self.handleInstructionButtonClick(e);
        }, true);
    };

    OrchestrationBar.prototype.bindModalClose = function () {
        if (global.__psOrchModalCloseBound) return;
        global.__psOrchModalCloseBound = true;
        var self = this;
        global.addEventListener('message', function (e) {
            if (!e.data || e.data.type !== 'ps-orch-instruction-saved') return;
            var bar = global.__psOrchBarInstance;
            if (!bar) return;
            bar.showEvent('Instruction saved');
            bar.closeInstructionModal();
        });
        document.addEventListener('click', function (e) {
            var closeBtn = e.target && e.target.closest
                ? e.target.closest('#ps-orch-modal-close,[data-orch-modal-close]')
                : null;
            if (!closeBtn) return;
            if (!document.getElementById('ps-orch-instruction-modal')) return;
            e.preventDefault();
            self.closeInstructionModal();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && document.querySelector('#ps-orch-instruction-modal.ps-orch-modal-open')) {
                self.closeInstructionModal();
            }
        });
    };

    OrchestrationBar.prototype.start = function () {
        var self = this;
        this.ensureModalMounted();
        this.bindInstructionButton();
        this.bindModalClose();
        this.installHistoryHooks();
        this.updateBar(true);
        setInterval(function () {
            var st = document.getElementById(self.config.statusElId);
            var txt = st ? (st.textContent || '') : '';
            if (/no instruction match|checking|API error/i.test(txt)) {
                self.updateBar(true);
            } else {
                self.updateBar(false);
            }
        }, 2000);
        [500, 1500, 3500, 6000].forEach(function (ms) {
            setTimeout(function () {
                if (self.config.reinstallHooks) self._hooksInstalled = false;
                self.installHistoryHooks();
                self.updateBar(true);
            }, ms);
        });
    };

    function bootOrchBar(factory) {
        var run = function () { return factory(); };
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', run);
            return null;
        }
        return run();
    }

    global.PolySaaSOrchBar = {
        openFromButton: function (evt) {
            if (evt) {
                evt.preventDefault();
                evt.stopPropagation();
            }
            var bar = global.__psOrchBarInstance;
            if (bar) {
                bar.handleInstructionButtonClick(evt);
                return;
            }
            console.warn('[ORCH-BTN] bar not ready yet');
        },
        init: function (config) {
            return bootOrchBar(function () {
                var bar = new OrchestrationBar(config || {});
                bar.start();
                return bar;
            });
        },
        initEmbed: function () {
            if (global.__psEmbedOrchBar && global.__psOrchBarInstance) {
                return global.__psOrchBarInstance;
            }
            return bootOrchBar(function () {
                var bar = new OrchestrationBar({
                    pathElId: 'pss-action-path',
                    menuElId: 'pss-orch-menu',
                    statusElId: 'pss-orch-status',
                    eventElId: 'pss-orch-event',
                    btnId: 'pss-insert-instruction-btn',
                    reinstallHooks: false,
                    singleHookInstall: false
                });
                bar.start();
                global.__psEmbedOrchBar = {
                    updateBar: function (force) { bar.updateBar(!!force); },
                    installHistoryHooks: function () { bar.installHistoryHooks(); }
                };
                console.log('[ORCH-BTN] embed bar ready');
                return bar;
            });
        },
        initDisplay: function () {
            return bootOrchBar(function () {
            var bar = new OrchestrationBar({
                pathElId: 'ps-orch-path',
                menuElId: 'ps-orch-menu',
                actionElId: 'ps-orch-action',
                statusElId: 'ps-orch-status',
                eventElId: 'ps-orch-event',
                btnId: 'ps-insert-instruction-btn',
                reinstallHooks: true,
                singleHookInstall: true
            });
            bar.start();
            global.__psShowOrchEvent = function (msg) { bar.showEvent(msg); };
            global.__psOrchBar = {
                updateBar: function () { bar.updateBar(true); },
                installHistoryHooks: function () { bar.installHistoryHooks(); },
                getOdooInfo: function () { return bar.getPathInfo(); }
            };
            console.log('[ORCH-BTN] display bar ready');
            return bar;
            });
        }
    };
})(window);
