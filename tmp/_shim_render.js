
(function() {
    var PROXY_PREFIX = '/pt/polysniff/app.slack.com';
    var PS_TENANT = 'olient';
    var UPSTREAM_ORIGIN = 'https://app.slack.com' || 'https://app.slack.com';
    var SLACK_PATHS = ['/auth'];

    /* Hide _ps_tenant from location.search so Slack's client does not copy it
       into /auth?... (it already has PS_TENANT in this closure for rewrites). */
    try {
        if (window.location.search.indexOf('_ps_tenant=') !== -1) {
            var clean = new URL(window.location.href);
            clean.searchParams.delete('_ps_tenant');
            window.history.replaceState(null, '', clean.pathname + clean.search + clean.hash);
        }
    } catch (e) {}

    /* Auth iframe does parent.postMessage(..., 'https://app.slack.com'). That
       looks up postMessage on the PARENT window object — a Window.prototype
       patch in this frame alone is not enough (confirmed live: credentials
       ready, then native targetOrigin mismatch, no shim log). Patch this
       window AND same-origin parent/top directly. */
    function patchPostMessage(win, label) {
        if (!win) return;
        try {
            var orig = win.postMessage.bind(win);
            win.postMessage = function(message, targetOrigin, transfer) {
                if (typeof targetOrigin === 'string' && targetOrigin.indexOf(UPSTREAM_ORIGIN) === 0) {
                    var dest = (win.location && win.location.origin) || window.location.origin;
                    console.log('[SLACK SHIM] postMessage(' + label + ') ' + targetOrigin + ' -> ' + dest);
                    targetOrigin = dest;
                }
                if (arguments.length > 2) return orig(message, targetOrigin, transfer);
                return orig(message, targetOrigin);
            };
        } catch (e) {
            console.warn('[SLACK SHIM] postMessage patch failed for ' + label, e);
        }
    }
    try {
        var _pmProto = Window.prototype.postMessage;
        Window.prototype.postMessage = function(message, targetOrigin, transfer) {
            if (typeof targetOrigin === 'string' && targetOrigin.indexOf(UPSTREAM_ORIGIN) === 0) {
                var dest = window.location.origin;
                try { if (this && this.location) dest = this.location.origin; } catch (e) {}
                console.log('[SLACK SHIM] postMessage(proto) ' + targetOrigin + ' -> ' + dest);
                targetOrigin = dest;
            }
            if (arguments.length > 2) return _pmProto.call(this, message, targetOrigin, transfer);
            return _pmProto.call(this, message, targetOrigin);
        };
    } catch (e) {}
    patchPostMessage(window, 'self');
    try { if (window.parent && window.parent !== window) patchPostMessage(window.parent, 'parent'); } catch (e) {}
    try { if (window.top && window.top !== window) patchPostMessage(window.top, 'top'); } catch (e) {}

    /* Receivers check event.origin === https://app.slack.com (and often
       event instanceof MessageEvent). postMessage now delivers, but the
       parent still timed out — spoof origin via a real MessageEvent, and
       also wrap window.onmessage (not only addEventListener). */
    function spoofMessageEvent(event) {
        if (!event || event.origin !== window.location.origin) return event;
        /* Redefine origin on the delivered event first. A synthetic
           MessageEvent is untrusted (isTrusted false) and can drop `source`,
           and iframe handshakes routinely check
           event.source === iframe.contentWindow, so replacing the event is a
           last resort rather than the default. */
        try {
            Object.defineProperty(event, 'origin', {
                get: function() { return UPSTREAM_ORIGIN; },
                configurable: true
            });
            if (event.origin === UPSTREAM_ORIGIN) return event;
        } catch (e) {}
        try {
            return new MessageEvent('message', {
                data: event.data,
                origin: UPSTREAM_ORIGIN,
                lastEventId: event.lastEventId || '',
                source: event.source,
                ports: event.ports ? Array.prototype.slice.call(event.ports) : []
            });
        } catch (e) {
            return {
                data: event.data,
                origin: UPSTREAM_ORIGIN,
                source: event.source,
                ports: event.ports,
                lastEventId: event.lastEventId,
                type: 'message'
            };
        }
    }
    try {
        var _ael = EventTarget.prototype.addEventListener;
        EventTarget.prototype.addEventListener = function(type, listener, options) {
            if (type === 'message' && typeof listener === 'function') {
                var wrapped = function(event) {
                    var ev = spoofMessageEvent(event);
                    if (ev && ev.origin === UPSTREAM_ORIGIN) {
                        console.log('[SLACK SHIM] credential message origin=' + ev.origin
                            + ' inPlace=' + (ev === event)
                            + ' source=' + (ev.source ? 'kept' : 'lost')
                            + ' trusted=' + (ev.isTrusted === true)
                            + ' data=' + (ev.data && typeof ev.data === 'object'
                                ? Object.keys(ev.data).join(',') : typeof ev.data));
                    }
                    return listener.call(this, ev);
                };
                return _ael.call(this, type, wrapped, options);
            }
            return _ael.call(this, type, listener, options);
        };
    } catch (e) {}
    try {
        var _onMsgDesc = Object.getOwnPropertyDescriptor(Window.prototype, 'onmessage');
        if (_onMsgDesc && _onMsgDesc.set) {
            Object.defineProperty(window, 'onmessage', {
                configurable: true,
                enumerable: true,
                get: function() { return this.__ps_onmessage; },
                set: function(fn) {
                    this.__ps_onmessage = fn;
                    if (typeof fn === 'function') {
                        _onMsgDesc.set.call(this, function(event) {
                            return fn.call(this, spoofMessageEvent(event));
                        });
                    } else {
                        _onMsgDesc.set.call(this, fn);
                    }
                }
            });
        }
    } catch (e) {}
    /* Capture-phase safety net: if Slack registered before our wrap somehow,
       re-dispatch is too late; at least log what arrives. */
    try {
        window.addEventListener('message', function(event) {
            if (event && event.origin === window.location.origin) {
                console.log('[SLACK SHIM] saw same-origin message; data keys=',
                    event.data && typeof event.data === 'object' ? Object.keys(event.data) : typeof event.data);
            }
        }, true);
    } catch (e) {}

    function shouldRewrite(path) {
        if (!path || typeof path !== 'string' || path.charAt(0) !== '/') return false;
        if (path.indexOf(PROXY_PREFIX) === 0) return false;
        for (var i = 0; i < SLACK_PATHS.length; i++) {
            if (path === SLACK_PATHS[i] || path.indexOf(SLACK_PATHS[i]) === 0) return true;
        }
        return false;
    }

    function withTenant(url) {
        if (!PS_TENANT) return url;
        if (url.indexOf('_ps_tenant=') !== -1) return url;
        return url + (url.indexOf('?') >= 0 ? '&' : '?') + '_ps_tenant=' + encodeURIComponent(PS_TENANT);
    }

    function rewriteUrl(url) {
        if (typeof url !== 'string' || !url) return url;
        var path = url;
        try {
            if (url.charAt(0) !== '/') {
                var parsed = new URL(url, window.location.origin);
                if (parsed.origin !== window.location.origin) return url;
                path = parsed.pathname + parsed.search + parsed.hash;
            }
        } catch (e) { return url; }
        if (shouldRewrite(path)) {
            var rewritten = withTenant(PROXY_PREFIX + path);
            console.log('[SLACK SHIM] proxy-relay rewrite ' + url + ' -> ' + rewritten);
            return rewritten;
        }
        return url;
    }

    var _f = window.fetch;
    window.fetch = function(input, init) {
        if (typeof input === 'string') {
            input = rewriteUrl(input);
        } else if (input && input.url) {
            var rw = rewriteUrl(input.url);
            if (rw !== input.url) { try { input = new Request(rw, input); } catch (e) {} }
        }
        return _f.call(this, input, init);
    };

    var _xo = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url) {
        var args = Array.prototype.slice.call(arguments);
        args[1] = rewriteUrl(url);
        return _xo.apply(this, args);
    };

    try {
        var _srcDesc = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'src');
        if (_srcDesc && _srcDesc.set) {
            Object.defineProperty(HTMLIFrameElement.prototype, 'src', {
                get: _srcDesc.get,
                set: function(v) { _srcDesc.set.call(this, rewriteUrl(String(v || ''))); },
                configurable: true
            });
        }
    } catch (e) {}

    /* Navigation is NOT interceptable from page script: window.location is an
       own non-configurable property and Location.prototype.href / .assign do not
       exist (both [LegacyUnforgeable]; verified in Chrome). Slack's fallback
       `window.location = '/auth?...'` is relayed server-side instead — see
       stray_root_paths() on this handler. */

    console.log('[SLACK SHIM] Installed proxy-relay + postMessage bridge. Proxy prefix: ' + PROXY_PREFIX);
})();
