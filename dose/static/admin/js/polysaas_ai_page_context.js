// THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
// BINGO: PolySaaS AI Context-Aware Chat — commit fd9febb8
// BINGO: Geronimo Chat Integration — 2026-09-02
/**
 * PolySaaS AI — collect rich page context for Geronimo (Gemini co-pilot).
 * Used by polysaas_ai_chat_dock.html and polysaas_ai_chat.html on each send.
 */
(function (global) {
    'use strict';

    function text(el) {
        if (!el) return '';
        return String(el.textContent || '').trim();
    }

    function detectSection(pathname) {
        if (!pathname) return '';
        if (pathname.indexOf('/pt/admin/') === 0) return 'Passthrough embed';
        if (pathname.indexOf('/admin/polysaas-ai') === 0) return 'PolySaaS AI';
        if (pathname.indexOf('/admin/') === 0) return 'Django admin';
        return '';
    }

    function detectPassthrough(pathname) {
        if (pathname.indexOf('/pt/admin/') !== 0) {
            return { embed: false, host: '', service: '' };
        }
        var parts = pathname.split('/').filter(Boolean);
        var host = parts.length >= 3 ? parts[2] : '';
        var service = '';
        if (host.indexOf('mattermost') !== -1) service = 'Mattermost';
        else if (host.indexOf('odoo') !== -1) service = 'Odoo';
        else if (host.indexOf('nextcloud') !== -1) service = 'Nextcloud';
        else if (host) service = host.split('.')[0];
        return { embed: true, host: host, service: service };
    }

    function parseMattermostActionPath(actionPath) {
        var out = { team: '', channel: '' };
        if (!actionPath) return out;
        var m = actionPath.match(/^\/([^/]+)\/channels\/([^/?#]+)/);
        if (m) {
            out.team = m[1];
            out.channel = m[2];
        }
        return out;
    }

    function tenantFromDock(dockEl) {
        if (!dockEl) return { name: '', slug: '' };
        return {
            name: dockEl.getAttribute('data-tenant-name') || '',
            slug: dockEl.getAttribute('data-tenant-slug') || '',
        };
    }

    function collectEndpointContext(dockEl) {
        // Endpoint home page context: extract data panel structure, action names, MQ state
        var endpointCtx = {};
        
        // Endpoint name (from page title or breadcrumb)
        var titleEl = document.querySelector('.polysaas-endpoint-home__title');
        if (titleEl) endpointCtx.endpoint_name = text(titleEl);
        
        // Data panel structure (columns and row count from endpoint_table.js context)
        var dataEls = document.querySelectorAll('[data-polysaas-panel]');
        if (dataEls.length > 0) {
            endpointCtx.data_panels = [];
            dataEls.forEach(function(el) {
                var panelKey = el.getAttribute('data-polysaas-panel');
                var table = el.querySelector('table');
                var columns = [];
                var rowCount = 0;
                if (table) {
                    var headerRow = table.querySelector('thead tr');
                    if (headerRow) {
                        var cells = headerRow.querySelectorAll('th');
                        cells.forEach(function(th) {
                            columns.push(text(th));
                        });
                    }
                    var bodyRows = table.querySelectorAll('tbody tr');
                    rowCount = bodyRows.length;
                }
                endpointCtx.data_panels.push({
                    key: panelKey,
                    columns: columns,
                    row_count: rowCount,
                });
            });
        }
        
        // Available actions (bookmarks and quick buttons)
        var bookmarkEls = document.querySelectorAll('[data-polysaas-bookmark]');
        if (bookmarkEls.length > 0) {
            endpointCtx.actions = [];
            bookmarkEls.forEach(function(el) {
                var key = el.getAttribute('data-polysaas-bookmark');
                var label = text(el.querySelector('[data-polysaas-bookmark-label]') || el);
                endpointCtx.actions.push({ key: key, label: label });
            });
        }
        
        // MQ orchestration state (producer/consumer status)
        var producersEl = document.querySelector('[data-polysaas-producers]');
        var consumersEl = document.querySelector('[data-polysaas-consumers]');
        if (producersEl || consumersEl) {
            endpointCtx.orchestration_context = {
                has_producers: !!producersEl,
                producer_count: producersEl ? producersEl.querySelectorAll('[data-producer]').length : 0,
                has_consumers: !!consumersEl,
                consumer_count: consumersEl ? consumersEl.querySelectorAll('[data-consumer]').length : 0,
            };
        }
        
        return endpointCtx;
    }

    function collectPageContext(dockEl) {
        var pathname = global.location.pathname || '';
        var search = global.location.search || '';
        var pt = detectPassthrough(pathname);
        var actionPathEl = document.getElementById('pss-action-path');
        var actionPath = text(actionPathEl);
        if (!actionPath || actionPath === 'loading…') {
            actionPath = pathname + search;
        }
        var mm = parseMattermostActionPath(actionPath);
        var tenant = tenantFromDock(dockEl);

        var ctx = {
            url: global.location.href,
            pathname: pathname + search,
            page_title: document.title || '',
            section: detectSection(pathname),
            tenant_name: tenant.name,
            tenant_slug: tenant.slug,
            action_path: actionPath,
            passthrough_embed: pt.embed,
            active_service: pt.service,
            passthrough_host: pt.host,
            mattermost_team: mm.team,
            mattermost_channel: mm.channel,
            orchestration: {
                status: text(document.getElementById('pss-orch-status')),
                menu_id: text(document.getElementById('pss-orch-menu')),
                event: text(document.getElementById('pss-orch-event')),
            },
            collected_at: new Date().toISOString(),
        };
        
        // Add endpoint-specific context if available (endpoint home page)
        var endpointCtx = collectEndpointContext(dockEl);
        if (Object.keys(endpointCtx).length > 0) {
            ctx.endpoint = endpointCtx;
        }

        try {
            return JSON.stringify(ctx).slice(0, 2000);
        } catch (e) {
            return (pathname + search).slice(0, 500);
        }
    }

    global.PolySaaSAiPageContext = {
        collect: collectPageContext,
    };
})(window);
