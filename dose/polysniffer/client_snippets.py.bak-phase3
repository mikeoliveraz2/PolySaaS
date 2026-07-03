"""
Client-side script snippet to capture HubSpot popup session cookies.

This script should be injected into the PolySniffer workspace shell.
It monitors the popup login window and captures cookies when it closes.
"""

POPUP_COOKIE_CAPTURE_SCRIPT = '''
<script data-ps-popup-cookie-capture="1">
(function() {
  var ENDPOINT_ID = window.__polysniffer_endpoint_id || 0;
  var SYNC_URL = '/pt/polysniff/' + ENDPOINT_ID + '/api/sync-session/';
  var popup = null;
  var originalOpen = window.open;
  
  // Intercept window.open to monitor popup lifecycle
  window.open = function(url, name, features) {
    console.log('[PSC] window.open intercepted:', url);
    popup = originalOpen.apply(this, arguments);
    
    if (popup && url && url.indexOf('hubspot.com') >= 0) {
      console.log('[PSC] HubSpot popup detected, monitoring for close...');
      
      var checkInterval = setInterval(function() {
        try {
          if (popup.closed) {
            clearInterval(checkInterval);
            console.log('[PSC] Popup closed, syncing session...');
            syncSession();
          }
        } catch (e) {}
      }, 500);
      
      // Also try to read cookies from popup when it finishes loading
      setTimeout(function() {
        if (!popup.closed && popup.location) {
          try {
            // This will fail if popup is on different domain (expected)
            var popupCookies = popup.document.cookie;
            if (popupCookies) {
              console.log('[PSC] Read cookies from popup directly');
              sendCookies(popupCookies);
            }
          } catch (e) {
            console.log('[PSC] Cannot read popup cookies (expected - different domain):', e.message);
          }
        }
      }, 3000);
    }
    
    return popup;
  };
  
  // Listen for postMessage from popup
  window.addEventListener('message', function(event) {
    try {
      if (event.data && event.data.type === 'hubspot-cookies') {
        console.log('[PSC] Received cookies via postMessage from popup');
        sendCookies(event.data.cookies);
      }
    } catch (e) {
      console.log('[PSC] postMessage handler error:', e);
    }
  });
  
  function parseCookies(cookieString) {
    var cookies = {};
    if (!cookieString) return cookies;
    try {
      var parts = (cookieString || '').split(';');
      for (var i = 0; i < parts.length; i++) {
        var part = parts[i].trim();
        if (!part) continue;
        var idx = part.indexOf('=');
        if (idx > 0) {
          var name = part.substring(0, idx).trim();
          var value = part.substring(idx + 1).trim();
          if (name && value) {
            cookies[name] = value;
          }
        }
      }
    } catch (e) {}
    return cookies;
  }
  
  function sendCookies(cookieString) {
    var cookies = typeof cookieString === 'string' ? parseCookies(cookieString) : (cookieString || {});
    if (Object.keys(cookies).length === 0) {
      console.log('[PSC] No cookies to send');
      return;
    }
    
    console.log('[PSC] Sending', Object.keys(cookies).length, 'cookies to', SYNC_URL);
    
    fetch(SYNC_URL, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({cookies: cookies})
    }).then(function(resp) {
      console.log('[PSC] Sync response:', resp.status);
      if (resp.ok) {
        // Reload the workspace to pick up the stored cookies
        console.log('[PSC] Reloading workspace to apply stored cookies');
        window.location.reload();
      }
    }).catch(function(err) {
      console.log('[PSC] Sync failed:', err);
    });
  }
  
  function syncSession() {
    // Attempt to detect when popup login succeeds and sync cookies
    // This runs after popup closes
    console.log('[PSC] Attempting to sync session after popup close...');
    
    // Make a request to a "detect auth" endpoint that can verify
    // if the user is now authenticated on hubspot
    fetch('/pt/polysniff/' + ENDPOINT_ID + '/home/v2/api/portal', {
      method: 'GET',
      credentials: 'same-origin'
    }).then(function(resp) {
      if (resp.ok) {
        resp.json().then(function(data) {
          if (data.portalId && data.portalId !== 0) {
            console.log('[PSC] Auth successful, portalId:', data.portalId);
            window.location.reload();
          }
        });
      }
    }).catch(function(e) {
      console.log('[PSC] Auth check failed:', e);
    });
  }
  
  // Make endpoint_id globally available if not already set
  if (!window.__polysniffer_endpoint_id && document.currentScript) {
    var src = document.currentScript.getAttribute('data-endpoint-id');
    if (src) {
      window.__polysniffer_endpoint_id = parseInt(src, 10);
    }
  }
})();
</script>
'''
