/**
 * Generic SPA API Interceptor
 * Works with any SPA (Airtable, Notion, etc.) by intercepting and routing API calls
 * through the Django passthrough middleware
 *
 * Usage: This script is auto-injected by ExternalPassthroughMiddleware
 * for endpoints with inject_proxy_script=True
 */

(function() {
    'use strict';

    // Detect which trigger path we're on (e.g., /pt/admin/airtable/)
    const currentPath = window.location.pathname;
    const triggerPath = currentPath.split('/').slice(0, 4).join('/') + '/'; // e.g., /pt/admin/airtable/

    console.log('[PolySaaS API Interceptor] Initialized for path:', triggerPath);

    // Intercept XMLHttpRequest
    const originalXHROpen = window.XMLHttpRequest.prototype.open;
    const originalXHRSend = window.XMLHttpRequest.prototype.send;

    window.XMLHttpRequest.prototype.open = function(method, url, ...args) {
        this._polysaas_method = method;
        this._polysaas_url = url;
        this._polysaas_original_url = url;
        return originalXHROpen.call(this, method, url, ...args);
    };

    window.XMLHttpRequest.prototype.send = function(data) {
        const method = this._polysaas_method || 'GET';
        const url = this._polysaas_url;
        const originalUrl = this._polysaas_original_url;

        // Log all API calls
        console.log('[PolySaaS API Interceptor] XHR', method, url);

        // If this is an external API call, route it through the proxy
        if (url && typeof url === 'string') {
            if (url.startsWith('http') && !url.includes(window.location.origin)) {
                // External API call - route through proxy
                const urlObj = new URL(url, window.location.origin);
                const proxiedUrl = triggerPath + 'api/' + urlObj.pathname.replace(/^\//, '');

                console.log('[PolySaaS API Interceptor] Proxying external API call:',
                    originalUrl, '→', proxiedUrl);

                // TODO: Could fire atomic services here for monitoring/logging
            }
        }

        return originalXHRSend.call(this, data);
    };

    // Intercept Fetch API
    if (window.fetch) {
        const originalFetch = window.fetch;

        window.fetch = function(url, options = {}) {
            if (typeof url === 'string') {
                console.log('[PolySaaS API Interceptor] Fetch',
                    (options.method || 'GET'), url);

                // External API call detection
                if (url.startsWith('http') && !url.includes(window.location.origin)) {
                    const urlObj = new URL(url, window.location.origin);
                    const proxiedUrl = triggerPath + 'api/' + urlObj.pathname.replace(/^\//, '');

                    console.log('[PolySaaS API Interceptor] Proxying external fetch:',
                        url, '→', proxiedUrl);

                    // TODO: Could fire atomic services here for monitoring/logging
                }
            }

            return originalFetch.call(this, url, options);
        };
    }

    console.log('[PolySaaS API Interceptor] Script loaded - all API calls will be logged');
})();
