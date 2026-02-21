let activeTabId = null;
let networkCaptures = [];
let isCapturing = false;

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'startNetworkCapture') {
    activeTabId = msg.tabId;
    networkCaptures = [];
    isCapturing = true;
    sendResponse({ ok: true });
  }

  if (msg.action === 'stopNetworkCapture') {
    isCapturing = false;
    sendResponse({ captures: networkCaptures });
  }

  if (msg.action === 'contentCaptureData') {
    chrome.storage.local.get(['captureData'], (data) => {
      const cd = data.captureData || { requests: [], forms: [], cookies: {} };

      if (msg.data.forms) cd.forms = msg.data.forms;
      if (msg.data.cookies) cd.cookies = { ...cd.cookies, ...msg.data.cookies };
      if (msg.data.pageUrl) cd.pageUrl = msg.data.pageUrl;
      if (msg.data.pageTitle) cd.pageTitle = msg.data.pageTitle;

      if (msg.data.request) {
        cd.requests.push(msg.data.request);
      }

      chrome.storage.local.set({ captureData: cd });
    });
    sendResponse({ ok: true });
  }

  return true;
});

chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    if (!isCapturing || !activeTabId) return;
    if (details.tabId !== activeTabId) return;

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
          const raw = details.requestBody.raw.map(r => decoder.decode(r.bytes)).join('');
          capture.requestBody = raw;
        } catch {}
      }
    }

    networkCaptures.push(capture);

    chrome.storage.local.get(['captureData'], (data) => {
      const cd = data.captureData || { requests: [], forms: [], cookies: {} };
      cd.requests.push(capture);
      chrome.storage.local.set({ captureData: cd });
    });
  },
  { urls: ['<all_urls>'] },
  ['requestBody']
);

chrome.webRequest.onCompleted.addListener(
  (details) => {
    if (!isCapturing || !activeTabId) return;
    if (details.tabId !== activeTabId) return;

    const existing = networkCaptures.find(
      c => c.url === details.url && c.method === details.method && !c.status
    );
    if (existing) {
      existing.status = details.statusCode;
      existing.responseHeaders = details.responseHeaders;
    }
  },
  { urls: ['<all_urls>'] },
  ['responseHeaders']
);
