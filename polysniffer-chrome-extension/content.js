const configEl = document.getElementById('polysniffer-config');
if (configEl) {
  const djangoUrl = configEl.dataset.djangoUrl;
  const endpointId = configEl.dataset.endpointId;
  const endpointUrl = configEl.dataset.endpointUrl;

  if (djangoUrl && endpointId && endpointUrl) {
    chrome.runtime.sendMessage({
      action: 'autoConfig',
      djangoUrl,
      endpointId,
      endpointUrl
    }, (resp) => {
      if (resp && resp.ok) {
        window.postMessage({ type: 'polysniffer-ext-ready' }, '*');
      }
    });
  }
}

let isCapturing = false;
let originalFetch = null;
let originalXHROpen = null;
let originalXHRSend = null;

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'startCapture') {
    isCapturing = true;
    capturePageState();
    interceptNetworkCalls();
    observeFormSubmissions();
    sendResponse({ ok: true });
  }

  if (msg.action === 'stopCapture') {
    isCapturing = false;
    restoreInterceptors();
    sendResponse({ ok: true });
  }

  return true;
});

function capturePageState() {
  const forms = [];
  document.querySelectorAll('form').forEach((form, idx) => {
    const fields = [];
    form.querySelectorAll('input, select, textarea').forEach(el => {
      fields.push({
        tag: el.tagName.toLowerCase(),
        type: el.type || 'text',
        name: el.name || null,
        id: el.id || null,
        value: el.type === 'password' ? '[REDACTED]' : (el.value || ''),
        required: el.required,
        placeholder: el.placeholder || null
      });
    });

    forms.push({
      index: idx,
      action: form.action || window.location.href,
      method: (form.method || 'GET').toUpperCase(),
      id: form.id || null,
      fields,
      hasCSRF: fields.some(f =>
        (f.name && /csrf|token/i.test(f.name)) ||
        (f.type === 'hidden' && /csrf|token/i.test(f.name || ''))
      )
    });
  });

  const cookies = {};
  document.cookie.split(';').forEach(c => {
    const parts = c.trim().split('=');
    if (parts[0]) cookies[parts[0]] = parts.slice(1).join('=');
  });

  const metaTags = {};
  document.querySelectorAll('meta[name], meta[property]').forEach(m => {
    const key = m.getAttribute('name') || m.getAttribute('property');
    metaTags[key] = m.getAttribute('content');
  });

  chrome.runtime.sendMessage({
    action: 'contentCaptureData',
    data: {
      forms,
      cookies,
      pageUrl: window.location.href,
      pageTitle: document.title,
      metaTags
    }
  });
}

function interceptNetworkCalls() {
  originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const [resource, init] = args;
    const url = typeof resource === 'string' ? resource : resource.url;
    const method = init?.method || 'GET';

    const response = await originalFetch.apply(this, args);

    if (isCapturing) {
      let responseData = null;
      try {
        const clone = response.clone();
        const ct = clone.headers.get('content-type') || '';
        if (ct.includes('json')) {
          responseData = await clone.json();
        } else if (ct.includes('text') || ct.includes('html')) {
          const text = await clone.text();
          responseData = text.substring(0, 5000);
        }
      } catch {}

      chrome.runtime.sendMessage({
        action: 'contentCaptureData',
        data: {
          request: {
            url,
            method: method.toUpperCase(),
            requestHeaders: init?.headers || {},
            requestBody: init?.body || '',
            status: response.status,
            responseData,
            timestamp: new Date().toISOString(),
            source: 'fetch'
          }
        }
      });
    }

    return response;
  };

  originalXHROpen = XMLHttpRequest.prototype.open;
  originalXHRSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    this._polyMethod = method;
    this._polyUrl = url;
    return originalXHROpen.call(this, method, url, ...rest);
  };

  XMLHttpRequest.prototype.send = function(body) {
    if (isCapturing) {
      this.addEventListener('load', function() {
        let responseData = null;
        try {
          const ct = this.getResponseHeader('content-type') || '';
          if (ct.includes('json')) {
            responseData = JSON.parse(this.responseText);
          } else {
            responseData = this.responseText?.substring(0, 5000);
          }
        } catch {}

        chrome.runtime.sendMessage({
          action: 'contentCaptureData',
          data: {
            request: {
              url: this._polyUrl,
              method: (this._polyMethod || 'GET').toUpperCase(),
              requestBody: body || '',
              status: this.status,
              responseData,
              timestamp: new Date().toISOString(),
              source: 'xhr'
            }
          }
        });
      });
    }
    return originalXHRSend.call(this, body);
  };
}

function observeFormSubmissions() {
  document.addEventListener('submit', (e) => {
    if (!isCapturing) return;

    const form = e.target;
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => {
      if (/password|passwd|pass/i.test(key)) {
        data[key] = '[REDACTED]';
      } else {
        data[key] = value;
      }
    });

    chrome.runtime.sendMessage({
      action: 'contentCaptureData',
      data: {
        request: {
          url: form.action || window.location.href,
          method: (form.method || 'POST').toUpperCase(),
          requestBody: JSON.stringify(data),
          timestamp: new Date().toISOString(),
          source: 'form_submit'
        }
      }
    });
  }, true);
}

function restoreInterceptors() {
  if (originalFetch) {
    window.fetch = originalFetch;
    originalFetch = null;
  }
  if (originalXHROpen) {
    XMLHttpRequest.prototype.open = originalXHROpen;
    originalXHROpen = null;
  }
  if (originalXHRSend) {
    XMLHttpRequest.prototype.send = originalXHRSend;
    originalXHRSend = null;
  }
}
