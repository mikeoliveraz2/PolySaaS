let djangoUrl = '';
let endpointId = null;
let endpointUrl = '';

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

function shouldCapture(url) {
  if (!djangoUrl || !endpointId || !endpointUrl) return false;
  if (url.includes('/admin/polysniffer/')) return false;
  if (url.startsWith(djangoUrl)) return false;
  try {
    const target = new URL(endpointUrl);
    const req = new URL(url);
    return req.hostname === target.hostname && req.port === target.port;
  } catch {
    return false;
  }
}

function sendToDjango(capture) {
  if (!djangoUrl || !endpointId) return;
  fetch(`${djangoUrl}/admin/polysniffer/silent-capture/${endpointId}/`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(capture)
  }).catch(() => {});
}

chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    if (!shouldCapture(details.url)) return;

    const capture = {
      url: details.url,
      method: details.method,
      type: details.type,
      timestamp: new Date().toISOString(),
      requestBody: null
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

    sendToDjango(capture);

    chrome.storage.local.get(['captureData'], (data) => {
      const cd = data.captureData || { requests: [], forms: [], cookies: {} };
      cd.requests.push(capture);
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
    chrome.storage.local.set({ djangoUrl, endpointId, endpointUrl });
    console.log(`[PolySniffer] Auto-configured: endpoint=${endpointId}, url=${endpointUrl}`);
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
