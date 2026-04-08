document.addEventListener('DOMContentLoaded', function() {
    var config = document.getElementById('polysniffer-config');
    if (!config) return;

    var endpointId = config.dataset.endpointId;
    var endpointUrl = config.dataset.endpointUrl;
    var endpointName = config.dataset.endpointName || 'Target';
    var polling = true;
    var lastId = 0;
    var captureCount = 0;
    var pollCount = 0;
    var pollTimer = null;
    var sniffingStopped = false;

    var countEl = document.getElementById('count');
    var updateEl = document.getElementById('last-update');
    var statusEl = document.getElementById('status');
    var pauseBtn = document.getElementById('pause-btn');
    var capturesEl = document.getElementById('captures');
    var doneBtn = document.getElementById('done-btn');
    var doneToast = document.getElementById('done-toast');

    capturesEl.innerHTML =
        '<div class="empty">' +
        '<p style="font-size:20px; color:#0f0;">PolySniffer ready.</p>' +
        '<p>Click the button below to open <strong>' + endpointName + '</strong>, then navigate it as you normally would.</p>' +
        '<p>Every request will be captured and displayed here in real-time.</p>' +
        '<p style="margin-top:20px;"><a href="' + endpointUrl + '" target="polysniffer_target_' + endpointId + '" ' +
        'style="display:inline-block; padding:10px 24px; background:#2196f3; color:white; text-decoration:none; border-radius:6px; font-size:15px; font-weight:bold;">' +
        'Open ' + endpointName + ' &rarr;</a></p></div>';

    function statusClass(code) {
        if (!code || code === 0) return 's0';
        if (code < 300) return 's2xx';
        if (code < 400) return 's3xx';
        if (code < 500) return 's4xx';
        return 's5xx';
    }

    function toggleDetail(el) {
        el.querySelector('.capture-detail').classList.toggle('open');
    }

    window.togglePoll = function() {
        if (sniffingStopped) return;
        polling = !polling;
        statusEl.className = 'status ' + (polling ? 'polling' : 'paused');
        statusEl.textContent = polling ? 'POLLING' : 'PAUSED';
        pauseBtn.textContent = polling ? 'Pause' : 'Resume';
    };

    function showDoneToast() {
        if (!doneToast) return;
        doneToast.classList.add('show');
        setTimeout(function() {
            doneToast.classList.remove('show');
        }, 4500);
    }

    function shutdownExtensionSniffer(reason) {
        if (sniffingStopped) return;
        sniffingStopped = true;
        polling = false;
        if (pollTimer != null) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
        statusEl.className = 'status paused';
        statusEl.textContent = 'STOPPED';
        if (pauseBtn) {
            pauseBtn.disabled = true;
            pauseBtn.textContent = 'Pause';
        }
        if (doneBtn) doneBtn.disabled = true;
        window.postMessage(
            { type: 'polysniffer-shutdown', source: 'live_capture', reason: reason || 'done' },
            '*'
        );
        showDoneToast();
    }

    if (doneBtn) {
        doneBtn.addEventListener('click', function() {
            shutdownExtensionSniffer('done_button');
        });
    }

    window.addEventListener('pagehide', function() {
        shutdownExtensionSniffer('pagehide');
    });
    window.addEventListener('beforeunload', function() {
        shutdownExtensionSniffer('beforeunload');
    });

    window.clearAll = function() {
        capturesEl.innerHTML = '<div class="empty"><p>Cleared. Browse <strong>' + endpointName + '</strong> in the other tab to capture traffic.</p></div>';
        captureCount = 0;
        countEl.textContent = '0';
    };

    function poll() {
        if (!polling || sniffingStopped) return;
        pollCount++;
        updateEl.textContent = 'Poll #' + pollCount + ' @ ' + new Date().toLocaleTimeString();

        fetch('/admin/polysniffer/get-captures/' + endpointId + '/?since_id=' + lastId)
            .then(function(resp) { return resp.json(); })
            .then(function(data) {
                if (data.captures && data.captures.length > 0) {
                    if (capturesEl.querySelector('.empty')) capturesEl.innerHTML = '';

                    data.captures.forEach(function(c) {
                        if (c.id > lastId) lastId = c.id;
                        captureCount++;
                        var method = (c.method || 'GET').toUpperCase();
                        var div = document.createElement('div');
                        div.className = 'capture-item new';
                        div.onclick = function() { toggleDetail(this); };
                        div.innerHTML =
                            '<div class="capture-row">' +
                            '<span class="capture-method ' + method + '">' + method + '</span>' +
                            '<span class="capture-path">' + (c.path || c.url || '-') + '</span>' +
                            '<span class="capture-status ' + statusClass(c.status_code) + '">' + (c.status_code || '-') + '</span>' +
                            '<span class="capture-time">' + (c.captured_at || '') + '</span>' +
                            '</div>' +
                            '<div class="capture-detail">' +
                            '<h4>URL</h4><pre>' + (c.url || '-') + '</pre>' +
                            (c.headers && Object.keys(c.headers).length ? '<h4>Headers</h4><pre>' + JSON.stringify(c.headers, null, 2) + '</pre>' : '') +
                            (c.cookies && Object.keys(c.cookies).length ? '<h4>Cookies</h4><pre>' + JSON.stringify(c.cookies, null, 2) + '</pre>' : '') +
                            (c.body ? '<h4>Body</h4><pre>' + c.body + '</pre>' : '') +
                            '</div>';
                        capturesEl.prepend(div);
                    });

                    countEl.textContent = captureCount;
                    updateEl.textContent = new Date().toLocaleTimeString();
                }
            })
            .catch(function(e) { console.error('Poll error:', e); });
    }

    pollTimer = setInterval(poll, 2000);
    poll();
});
