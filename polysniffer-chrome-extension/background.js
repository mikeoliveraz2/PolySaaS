let djangoUrl = '';
let endpointId = null;
let endpointUrl = '';
/** Live Capture tab: MV3 worker fetch often omits session cookies; relay POSTs through this tab. */
let pollerTabId = null;

chrome.storage.local.get(['djangoUrl', 'endpointId', 'endpointUrl'], (data) => {
  if (data.djangoUrl) djangoUrl = data.djangoUrl;
  if (data.endpointId) endpointId = data.endpointId;
  if (data.endpointUrl) endpointUrl = data.endpointUrl;
});

chrome.storage.onChanged.addListener((changes) => {
  if (changes.djangoUrl) djangoUrl = changes.djangoUrl.newValue || '';
  if (changes.endpointId) endpointId = changes.endpointId.newValue || null;
  if (changes.endpointUrl) endpointUrl = changes.endpointUrl.newValue || '';
});

function effectivePort(u) {
  if (u.port) return u.port;
  return u.protocol === 'https:' ? '443' : '80';
}

function loopbackHost(h) {
  return h === 'localhost' || h === '127.0.0.1' || h === '[::1]';
}

function hostsMatch(h1, h2) {
  if (loopbackHost(h1) && loopbackHost(h2)) return true;
  return h1 === h2;
}

/** Same browser session may use http://localhost:8000 vs http://127.0.0.1:8000 */
function isDjangoSelf(urlStr) {
  if (!djangoUrl || !urlStr) return false;
  if (urlStr.includes('/admin/polysniffer/')) return true;
  try {
    const d = new URL(djangoUrl);
    const u = new URL(urlStr);
    if (!hostsMatch(u.hostname, d.hostname)) return false;
    return effectivePort(u) === effectivePort(d);
  } catch {
    return urlStr.startsWith(djangoUrl);
  }
}

function shouldCapture(url) {
  if (!djangoUrl || !endpointId || !endpointUrl) return false;
  if (isDjangoSelf(url)) return false;
  try {
    const target = new URL(endpointUrl);
    const req = new URL(url);
    if (!hostsMatch(req.hostname, target.hostname)) return false;
    return effectivePort(req) === effectivePort(target);
  } catch {
    return false;
  }
}

const ODOO_RPC_PATHS = ['/web/dataset/call_kw', '/web/dataset/call_button',
  '/web/dataset/call', '/web/action/load', '/web/action/run'];

const RPC_EVENT_CATEGORIES = {
  create:           { icon: '🔴', label: 'CREATE',   priority: 1 },
  write:            { icon: '🔴', label: 'WRITE',    priority: 1 },
  unlink:           { icon: '🔴', label: 'DELETE',   priority: 1 },
  action_post:      { icon: '🟠', label: 'ACTION',   priority: 2 },
  action_confirm:   { icon: '🟠', label: 'ACTION',   priority: 2 },
  action_done:      { icon: '🟠', label: 'ACTION',   priority: 2 },
  action_cancel:    { icon: '🟠', label: 'ACTION',   priority: 2 },
  button_validate:  { icon: '⭐', label: 'WORKFLOW', priority: 2 },
  button_confirm:   { icon: '⭐', label: 'WORKFLOW', priority: 2 },
  button_approve:   { icon: '⭐', label: 'WORKFLOW', priority: 2 },
  search_read:      { icon: '⚪', label: 'READ',     priority: 4 },
  read:             { icon: '⚪', label: 'READ',     priority: 4 },
  name_get:         { icon: '⚪', label: 'READ',     priority: 4 },
  fields_get:       { icon: '⚪', label: 'READ',     priority: 4 },
  default_get:      { icon: '⚪', label: 'READ',     priority: 4 },
  onchange:         { icon: '🔵', label: 'FORM',     priority: 3 },
  name_search:      { icon: '⚪', label: 'READ',     priority: 4 },
};

function classifyOdooRpc(url, bodyStr) {
  try {
    const path = new URL(url).pathname;
    if (!ODOO_RPC_PATHS.some(p => path.startsWith(p))) return null;

    let parsed;
    if (typeof bodyStr === 'string') {
      parsed = JSON.parse(bodyStr);
    } else if (typeof bodyStr === 'object') {
      parsed = bodyStr;
    } else {
      return null;
    }

    const params = parsed.params || parsed;
    const model = params.model || params.args?.[0] || '';
    const method = params.method || '';

    if (!model || !method) return null;

    let cat = RPC_EVENT_CATEGORIES[method];
    if (!cat) {
      if (method.startsWith('action_')) cat = { icon: '🟠', label: 'ACTION', priority: 2 };
      else if (method.startsWith('button_')) cat = { icon: '⭐', label: 'WORKFLOW', priority: 2 };
      else cat = { icon: '🔹', label: 'RPC', priority: 3 };
    }

    return {
      model,
      method,
      eventTag: `odoo:${model}.${method}`,
      category: cat.label,
      icon: cat.icon,
      priority: cat.priority,
      isBusinessEvent: cat.priority <= 2
    };
  } catch {
    return null;
  }
}

let silentCaptureDisabled = false;

function sendToDjango(capture) {
  if (!djangoUrl || !endpointId || silentCaptureDisabled) return;
  fetch(`${djangoUrl}/admin/polysniffer/silent-capture/${endpointId}/`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(capture)
  }).then(response => {
    if (!response.ok) {
      console.log('[PolySniffer] Silent capture failed, disabling further attempts');
      silentCaptureDisabled = true;
    }
  }).catch(() => {
    console.log('[PolySniffer] Silent capture error, disabling further attempts');
    silentCaptureDisabled = true;
  });
}

chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    if (!shouldCapture(details.url)) return;

    const capture = {
      url: details.url,
      method: details.method,
      type: details.type,
      timestamp: new Date().toISOString(),
      requestBody: null,
      rpcEvent: null
    };

    if (details.requestBody) {
      if (details.requestBody.formData) {
        capture.requestBody = details.requestBody.formData;
      } else if (details.requestBody.raw) {
        try {
          const decoder = new TextDecoder('utf-8');
          capture.requestBody = details.requestBody.raw.map(r => decoder.decode(r.bytes)).join('');
        } catch {}
      }
    }

    if (details.method === 'POST' && capture.requestBody) {
      capture.rpcEvent = classifyOdooRpc(details.url, capture.requestBody);
    }

    sendToDjango(capture);

    chrome.storage.local.get(['captureData'], (data) => {
      const cd = data.captureData || { requests: [], forms: [], cookies: {}, rpcEvents: [] };
      cd.requests.push(capture);
      if (capture.rpcEvent) {
        if (!cd.rpcEvents) cd.rpcEvents = [];
        cd.rpcEvents.push({
          ...capture.rpcEvent,
          timestamp: capture.timestamp,
          url: capture.url
        });
        if (cd.rpcEvents.length > 200) cd.rpcEvents = cd.rpcEvents.slice(-200);
      }
      if (cd.requests.length > 500) cd.requests = cd.requests.slice(-500);
      chrome.storage.local.set({ captureData: cd });
    });
  },
  { urls: ['<all_urls>'] },
  ['requestBody']
);

chrome.webRequest.onCompleted.addListener(
  (details) => {
    if (!shouldCapture(details.url)) return;

    const statusCapture = {
      url: details.url,
      method: details.method,
      type: details.type,
      status: details.statusCode,
      responseHeaders: details.responseHeaders,
      timestamp: new Date().toISOString()
    };

    sendToDjango(statusCapture);
  },
  { urls: ['<all_urls>'] },
  ['responseHeaders']
);

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'autoConfig') {
    djangoUrl = msg.djangoUrl;
    endpointId = msg.endpointId;
    endpointUrl = msg.endpointUrl;
    if (sender.tab && sender.tab.id != null) {
      pollerTabId = sender.tab.id;
    }
    chrome.storage.local.set({ djangoUrl, endpointId, endpointUrl });
    console.log(`[PolySniffer] Auto-configured: endpoint=${endpointId}, target=${endpointUrl}, pollerTab=${pollerTabId}`);
    sendResponse({ ok: true });
    return true;
  }

  if (msg.action === 'registerPollerTab' && sender.tab && sender.tab.id != null) {
    pollerTabId = sender.tab.id;
    sendResponse({ ok: true });
    return true;
  }

  if (msg.action === 'contentCaptureData') {
    if (msg.data.request) {
      sendToDjango(msg.data.request);
    }

    chrome.storage.local.get(['captureData'], (data) => {
      const cd = data.captureData || { requests: [], forms: [], cookies: {} };
      if (msg.data.forms) cd.forms = msg.data.forms;
      if (msg.data.cookies) cd.cookies = { ...cd.cookies, ...msg.data.cookies };
      if (msg.data.pageUrl) cd.pageUrl = msg.data.pageUrl;
      if (msg.data.pageTitle) cd.pageTitle = msg.data.pageTitle;
      if (msg.data.request) cd.requests.push(msg.data.request);
      if (cd.requests.length > 500) cd.requests = cd.requests.slice(-500);
      chrome.storage.local.set({ captureData: cd });
    });
    sendResponse({ ok: true });
  }
  return true;
});
