// THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
// BINGO: PolySaaS AI Context-Aware Chat — commit PENDING
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

        try {
            return JSON.stringify(ctx).slice(0, 1800);
        } catch (e) {
            return (pathname + search).slice(0, 500);
        }
    }

    global.PolySaaSAiPageContext = {
        collect: collectPageContext,
    };
})(window);
