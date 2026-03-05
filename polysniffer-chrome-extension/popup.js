const $ = (sel) => document.querySelector(sel);
const show = (el) => el.classList.remove('hidden');
const hide = (el) => el.classList.add('hidden');

let djangoUrl = '';
let endpointId = null;
let endpoints = [];

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
    const ep = endpoints.find(ep => String(ep.id) === String(endpointId));
    chrome.storage.local.set({
      endpointId,
      endpointUrl: ep ? ep.url : ''
    });
    updateActiveState();
  });

  $('#btn-send').addEventListener('click', sendCaptures);
  $('#btn-generate').addEventListener('click', generateHandler);
  $('#btn-clear').addEventListener('click', () => {
    chrome.storage.local.set({ captureData: { requests: [], forms: [], cookies: {} } });
    updateStats();
  });

  pollStats();
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

    endpoints = data.endpoints || [];

    statusBar.className = 'status-bar ok';
    connText.textContent = `Connected — ${endpoints.length} endpoint(s)`;
    show(statusBar);

    const select = $('#endpoint-select');
    select.innerHTML = '<option value="">-- select endpoint --</option>';
    endpoints.forEach(ep => {
      const opt = document.createElement('option');
      opt.value = ep.id;
      opt.textContent = `${ep.name || ep.trigger_path} — ${ep.url}`;
      if (String(ep.id) === String(endpointId)) opt.selected = true;
      select.appendChild(opt);
    });

    show($('#endpoint-section'));
    updateActiveState();

    $('#link-dashboard').href = `${djangoUrl}/admin/polysniffer/dashboard/`;
    show($('#link-dashboard'));
  } catch (err) {
    statusBar.className = 'status-bar err';
    connText.textContent = `Failed: ${err.message}`;
    show(statusBar);
    $('#status-dot').className = 'dot dot-idle';
    hide($('#endpoint-section'));
    hide($('#active-section'));
  }
}

function updateActiveState() {
  if (endpointId) {
    const ep = endpoints.find(ep => String(ep.id) === String(endpointId));
    $('#active-endpoint-name').textContent = ep ? `${ep.name || ep.trigger_path} (${ep.url})` : `Endpoint #${endpointId}`;
    $('#status-dot').className = 'dot dot-capturing';
    show($('#active-section'));
  } else {
    $('#status-dot').className = 'dot dot-connected';
    hide($('#active-section'));
  }
}

async function updateStats() {
  try {
    const data = await chrome.storage.local.get(['captureData']);
    const cd = data.captureData || {};
    const requests = cd.requests || [];
    const rpcEvents = cd.rpcEvents || [];

    $('#stat-requests').textContent = requests.length;
    $('#stat-forms').textContent = (cd.forms || []).length;
    $('#stat-cookies').textContent = Object.keys(cd.cookies || {}).length;
    $('#stat-events').textContent = rpcEvents.length;

    const feedEl = $('#event-feed');
    if (rpcEvents.length > 0) {
      const recent = rpcEvents.slice(-15).reverse();
      feedEl.innerHTML = '<div class="event-feed-title">RPC Event Feed</div>' +
        recent.map(ev => {
          const time = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '';
          const cls = ev.isBusinessEvent ? 'event-row event-biz' : 'event-row';
          return `<div class="${cls}"><span class="ev-icon">${ev.icon}</span><span class="ev-tag">${ev.eventTag}</span><span class="ev-cat">${ev.category}</span><span class="ev-time">${time}</span></div>`;
        }).join('');
      show(feedEl);
    } else {
      hide(feedEl);
    }
  } catch {}
}

function pollStats() {
  updateStats();
  setTimeout(pollStats, 1500);
}

async function sendCaptures() {
  const resultSection = $('#result-section');
  const resultText = $('#result-text');

  try {
    const data = await chrome.storage.local.get(['captureData']);
    const cd = data.captureData || {};

    if (!(cd.requests || []).length && !(cd.forms || []).length) {
      resultText.className = 'result-box error';
      resultText.textContent = 'No captures to send. Browse the target site first.';
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
      timestamp: r.timestamp || new Date().toISOString(),
      rpc_event: r.rpcEvent || null
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
