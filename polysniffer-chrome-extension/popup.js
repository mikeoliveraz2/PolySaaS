const $ = (sel) => document.querySelector(sel);
const show = (el) => el.classList.remove('hidden');
const hide = (el) => el.classList.add('hidden');

let djangoUrl = '';
let endpointId = null;
let capturing = false;

document.addEventListener('DOMContentLoaded', async () => {
  const saved = await chrome.storage.local.get(['djangoUrl', 'endpointId']);
  if (saved.djangoUrl) {
    $('#django-url').value = saved.djangoUrl;
    await connect(saved.djangoUrl);
  }
  if (saved.endpointId) {
    endpointId = saved.endpointId;
  }

  $('#btn-connect').addEventListener('click', () => {
    connect($('#django-url').value.replace(/\/+$/, ''));
  });

  $('#endpoint-select').addEventListener('change', (e) => {
    endpointId = e.target.value || null;
    chrome.storage.local.set({ endpointId });
    if (endpointId) {
      show($('#capture-section'));
    } else {
      hide($('#capture-section'));
    }
  });

  $('#btn-start').addEventListener('click', startCapture);
  $('#btn-stop').addEventListener('click', stopCapture);
  $('#btn-send').addEventListener('click', sendCaptures);
  $('#btn-generate').addEventListener('click', generateHandler);
});

async function connect(url) {
  djangoUrl = url;
  chrome.storage.local.set({ djangoUrl });
  const statusBar = $('#connection-status');
  const connText = $('#conn-text');

  try {
    const resp = await fetch(`${djangoUrl}/admin/polysniffer/api/endpoints/`, {
      credentials: 'include'
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();

    if (!data.success) throw new Error(data.error || 'API error');

    statusBar.className = 'status-bar ok';
    connText.textContent = `Connected — ${data.endpoints.length} endpoint(s)`;
    show(statusBar);
    $('#status-dot').className = 'dot dot-connected';

    const select = $('#endpoint-select');
    select.innerHTML = '<option value="">-- select endpoint --</option>';
    data.endpoints.forEach(ep => {
      const opt = document.createElement('option');
      opt.value = ep.id;
      opt.textContent = `${ep.trigger_path || ep.name} — ${ep.url}`;
      if (String(ep.id) === String(endpointId)) opt.selected = true;
      select.appendChild(opt);
    });

    show($('#endpoint-section'));
    if (endpointId) show($('#capture-section'));

    $('#link-dashboard').href = `${djangoUrl}/admin/polysniffer/dashboard/`;
    show($('#link-dashboard'));

  } catch (err) {
    statusBar.className = 'status-bar err';
    connText.textContent = `Failed: ${err.message}`;
    show(statusBar);
    $('#status-dot').className = 'dot dot-idle';
    hide($('#endpoint-section'));
    hide($('#capture-section'));
  }
}

async function startCapture() {
  if (!endpointId) return;
  capturing = true;

  hide($('#btn-start'));
  show($('#btn-stop'));
  show($('#capture-stats'));
  hide($('#btn-send'));
  hide($('#btn-generate'));
  hide($('#result-section'));
  $('#status-dot').className = 'dot dot-capturing';

  $('#stat-requests').textContent = '0';
  $('#stat-forms').textContent = '0';
  $('#stat-cookies').textContent = '0';

  chrome.storage.local.set({ capturing: true, endpointId });

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab) {
    chrome.tabs.sendMessage(tab.id, { action: 'startCapture', endpointId });
  }

  chrome.runtime.sendMessage({ action: 'startNetworkCapture', tabId: tab?.id, endpointId });

  pollStats();
}

async function stopCapture() {
  capturing = false;
  chrome.storage.local.set({ capturing: false });

  show($('#btn-start'));
  hide($('#btn-stop'));
  show($('#btn-send'));
  show($('#btn-generate'));
  $('#status-dot').className = 'dot dot-connected';

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab) {
    chrome.tabs.sendMessage(tab.id, { action: 'stopCapture' });
  }
  chrome.runtime.sendMessage({ action: 'stopNetworkCapture' });
}

async function pollStats() {
  if (!capturing) return;
  try {
    const data = await chrome.storage.local.get(['captureData']);
    const cd = data.captureData || {};
    $('#stat-requests').textContent = (cd.requests || []).length;
    $('#stat-forms').textContent = (cd.forms || []).length;
    $('#stat-cookies').textContent = Object.keys(cd.cookies || {}).length;
  } catch {}
  setTimeout(pollStats, 1000);
}

async function sendCaptures() {
  const resultSection = $('#result-section');
  const resultText = $('#result-text');

  try {
    const data = await chrome.storage.local.get(['captureData']);
    const cd = data.captureData || {};

    if (!(cd.requests || []).length && !(cd.forms || []).length) {
      resultText.className = 'result-box error';
      resultText.textContent = 'No captures to send. Start a capture first.';
      show(resultSection);
      return;
    }

    const captures = (cd.requests || []).map(r => ({
      method: r.method || 'GET',
      url: r.url || '',
      status: r.status || 0,
      headers: r.requestHeaders || {},
      body: r.requestBody || '',
      data: r.responseData || {},
      cookies: cd.cookies || {},
      forms: cd.forms || [],
      page_url: cd.pageUrl || '',
      page_title: cd.pageTitle || '',
      timestamp: r.timestamp || new Date().toISOString()
    }));

    const csrfResp = await fetch(`${djangoUrl}/admin/polysniffer/api/csrf-token/`, {
      credentials: 'include'
    });
    const csrfData = await csrfResp.json();

    const resp = await fetch(`${djangoUrl}/admin/polysniffer/save-capture/${endpointId}/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfData.token
      },
      body: JSON.stringify({ captures, source: 'chrome_extension' })
    });

    const result = await resp.json();
    if (result.success) {
      resultText.className = 'result-box success';
      resultText.textContent = `Sent ${captures.length} capture(s) to Django.\n${result.message || ''}`;
    } else {
      resultText.className = 'result-box error';
      resultText.textContent = `Error: ${result.error}`;
    }
  } catch (err) {
    resultText.className = 'result-box error';
    resultText.textContent = `Send failed: ${err.message}`;
  }
  show(resultSection);
}

async function generateHandler() {
  const resultSection = $('#result-section');
  const resultText = $('#result-text');

  resultText.className = 'result-box';
  resultText.textContent = 'Generating handler from captures...';
  show(resultSection);

  try {
    const csrfResp = await fetch(`${djangoUrl}/admin/polysniffer/api/csrf-token/`, {
      credentials: 'include'
    });
    const csrfData = await csrfResp.json();

    const resp = await fetch(`${djangoUrl}/admin/polysniffer/ai-generate-handler/${endpointId}/`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfData.token
      }
    });

    const result = await resp.json();
    if (result.success) {
      resultText.className = 'result-box success';
      resultText.textContent = `Handler generated!\n\nAuth: ${result.analysis_summary?.auth_method || 'unknown'}\nSession: ${result.analysis_summary?.session_cookie || 'none'}\nCSRF: ${result.analysis_summary?.csrf_token_field || 'none'}`;
    } else {
      resultText.className = 'result-box error';
      resultText.textContent = `Error: ${result.error}`;
    }
  } catch (err) {
    resultText.className = 'result-box error';
    resultText.textContent = `Generation failed: ${err.message}`;
  }
}
