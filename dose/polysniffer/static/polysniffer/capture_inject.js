/**
 * PolySniffer Browser-Side Network Capture Injector
 * 
 * Intercepts fetch(), XMLHttpRequest, and WebSocket to capture network traffic
 * and send it to the PolySniffer backend for analysis.
 * 
 * Auto-starts on page load. Use window.PolySniffer.stop() to pause capture.
 */

(function() {
    'use strict';
    
    // Configuration
    const CAPTURE_ENDPOINT = '/admin/polysniffer/api/capture/';
    const MAX_BODY_PREVIEW = 1000; // Truncate body previews to prevent memory bloat
    const BATCH_SIZE = 10; // Send in batches to reduce network overhead
    const BATCH_INTERVAL = 2000; // Send batch every 2 seconds
    
    // State
    let captureId = null;
    let isCapturing = false;
    let captureQueue = [];
    let batchTimer = null;
    let stats = {
        total: 0,
        fetch: 0,
        xhr: 0,
        websocket: 0,
        navigation: 0,
        errors: 0
    };
    
    // Generate or retrieve capture ID
    function getCaptureId() {
        if (captureId) return captureId;
        
        // Try to get from sessionStorage
        captureId = sessionStorage.getItem('polysniffer_capture_id');
        
        if (!captureId) {
            // Generate new UUID
            captureId = 'capture-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('polysniffer_capture_id', captureId);
        }
        
        console.log('[PolySniffer] Capture ID:', captureId);
        return captureId;
    }
    
    // Truncate string to max length
    function truncate(str, maxLength) {
        if (!str) return '';
        const s = String(str);
        return s.length > maxLength ? s.substring(0, maxLength) + '...[truncated]' : s;
    }
    
    // Convert Headers object to plain object
    function headersToObject(headers) {
        const obj = {};
        if (headers instanceof Headers) {
            headers.forEach((value, key) => {
                obj[key] = value;
            });
        } else if (typeof headers === 'object') {
            Object.assign(obj, headers);
        }
        return obj;
    }
    
    // Send captured entry to backend
    function sendCapture(entry) {
        if (!isCapturing) return;
        
        captureQueue.push(entry);
        
        // Start batch timer if not already running
        if (!batchTimer) {
            batchTimer = setTimeout(flushQueue, BATCH_INTERVAL);
        }
        
        // Flush immediately if queue is full
        if (captureQueue.length >= BATCH_SIZE) {
            flushQueue();
        }
    }
    
    // Flush capture queue to backend
    function flushQueue() {
        if (batchTimer) {
            clearTimeout(batchTimer);
            batchTimer = null;
        }
        
        if (captureQueue.length === 0) return;
        
        const batch = captureQueue.splice(0, captureQueue.length);
        
        // Send each entry (could be optimized to send as batch in future)
        batch.forEach(entry => {
            fetch(CAPTURE_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(entry)
            }).catch(err => {
                console.error('[PolySniffer] Failed to send capture:', err);
                stats.errors++;
            });
        });
    }
    
    // Patch fetch()
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const startTime = performance.now();
        const url = args[0] instanceof Request ? args[0].url : args[0];
        const init = args[0] instanceof Request ? args[0] : (args[1] || {});
        const method = init.method || 'GET';
        
        console.log('[PolySniffer] Intercepted fetch:', method, url);
        
        return originalFetch.apply(this, args).then(response => {
            const endTime = performance.now();
            const duration = endTime - startTime;
            
            // Clone response to read body without consuming it
            const clonedResponse = response.clone();
            
            // Capture entry
            const entry = {
                capture_id: getCaptureId(),
                entry_type: 'fetch',
                url: url,
                method: method,
                status_code: response.status,
                duration_ms: duration,
                request_headers: headersToObject(init.headers || {}),
                response_headers: headersToObject(response.headers),
                request_body: '',
                response_body_preview: '',
                raw_entry: {
                    timestamp: new Date().toISOString(),
                    initiator: 'fetch',
                    url: url,
                    method: method
                }
            };
            
            // Try to capture request body
            if (init.body) {
                try {
                    entry.request_body = truncate(init.body, MAX_BODY_PREVIEW);
                } catch (e) {
                    entry.request_body = '[Unable to capture request body]';
                }
            }
            
            // Try to capture response body preview
            clonedResponse.text().then(text => {
                entry.response_body_preview = truncate(text, MAX_BODY_PREVIEW);
                sendCapture(entry);
                stats.total++;
                stats.fetch++;
            }).catch(err => {
                entry.response_body_preview = '[Unable to capture response body]';
                sendCapture(entry);
                stats.total++;
                stats.fetch++;
            });
            
            return response;
        }).catch(error => {
            const endTime = performance.now();
            const duration = endTime - startTime;
            
            // Capture failed request
            const entry = {
                capture_id: getCaptureId(),
                entry_type: 'fetch',
                url: url,
                method: method,
                status_code: 0,
                duration_ms: duration,
                request_headers: headersToObject(init.headers || {}),
                response_headers: {},
                request_body: init.body ? truncate(init.body, MAX_BODY_PREVIEW) : '',
                response_body_preview: `[Error: ${error.message}]`,
                raw_entry: {
                    timestamp: new Date().toISOString(),
                    initiator: 'fetch',
                    error: error.message
                }
            };
            
            sendCapture(entry);
            stats.total++;
            stats.fetch++;
            stats.errors++;
            
            throw error;
        });
    };
    
    // Patch XMLHttpRequest
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;
    const originalXHRSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;
    
    XMLHttpRequest.prototype.open = function(method, url, ...args) {
        this._polysnifferMethod = method;
        this._polysnifferUrl = url;
        this._polysnifferRequestHeaders = {};
        this._polysnifferStartTime = performance.now();
        
        console.log('[PolySniffer] Intercepted XHR open:', method, url);
        
        return originalXHROpen.apply(this, [method, url, ...args]);
    };
    
    XMLHttpRequest.prototype.setRequestHeader = function(header, value) {
        if (this._polysnifferRequestHeaders) {
            this._polysnifferRequestHeaders[header] = value;
        }
        return originalXHRSetRequestHeader.apply(this, arguments);
    };
    
    XMLHttpRequest.prototype.send = function(body) {
        const xhr = this;
        const startTime = xhr._polysnifferStartTime || performance.now();
        
        xhr.addEventListener('loadend', function() {
            const endTime = performance.now();
            const duration = endTime - startTime;
            
            const entry = {
                capture_id: getCaptureId(),
                entry_type: 'xhr',
                url: xhr._polysnifferUrl || xhr.responseURL,
                method: xhr._polysnifferMethod || 'GET',
                status_code: xhr.status,
                duration_ms: duration,
                request_headers: xhr._polysnifferRequestHeaders || {},
                response_headers: {},
                request_body: body ? truncate(body, MAX_BODY_PREVIEW) : '',
                response_body_preview: truncate(xhr.responseText, MAX_BODY_PREVIEW),
                raw_entry: {
                    timestamp: new Date().toISOString(),
                    initiator: 'xhr',
                    readyState: xhr.readyState,
                    statusText: xhr.statusText
                }
            };
            
            // Parse response headers
            const responseHeaders = xhr.getAllResponseHeaders();
            if (responseHeaders) {
                responseHeaders.split('\r\n').forEach(line => {
                    const parts = line.split(': ');
                    if (parts.length === 2) {
                        entry.response_headers[parts[0]] = parts[1];
                    }
                });
            }
            
            sendCapture(entry);
            stats.total++;
            stats.xhr++;
        });
        
        return originalXHRSend.apply(this, arguments);
    };
    
    // Patch WebSocket
    const originalWebSocket = window.WebSocket;
    window.WebSocket = function(url, protocols) {
        const startTime = performance.now();
        console.log('[PolySniffer] Intercepted WebSocket:', url);
        
        const ws = new originalWebSocket(url, protocols);
        
        // Capture WebSocket connection
        ws.addEventListener('open', function() {
            const endTime = performance.now();
            const duration = endTime - startTime;
            
            const entry = {
                capture_id: getCaptureId(),
                entry_type: 'websocket',
                url: url,
                method: 'CONNECT',
                status_code: 101, // Switching Protocols
                duration_ms: duration,
                request_headers: {},
                response_headers: {},
                request_body: '',
                response_body_preview: '[WebSocket connection established]',
                raw_entry: {
                    timestamp: new Date().toISOString(),
                    initiator: 'websocket',
                    event: 'open',
                    protocols: protocols
                }
            };
            
            sendCapture(entry);
            stats.total++;
            stats.websocket++;
        });
        
        // Capture WebSocket errors
        ws.addEventListener('error', function(event) {
            const entry = {
                capture_id: getCaptureId(),
                entry_type: 'websocket',
                url: url,
                method: 'CONNECT',
                status_code: 0,
                duration_ms: 0,
                request_headers: {},
                response_headers: {},
                request_body: '',
                response_body_preview: '[WebSocket error]',
                raw_entry: {
                    timestamp: new Date().toISOString(),
                    initiator: 'websocket',
                    event: 'error'
                }
            };
            
            sendCapture(entry);
            stats.total++;
            stats.websocket++;
            stats.errors++;
        });
        
        return ws;
    };
    
    // Capture navigation events
    function captureNavigation(type) {
        const entry = {
            capture_id: getCaptureId(),
            entry_type: 'navigation',
            url: window.location.href,
            method: 'GET',
            status_code: 200,
            duration_ms: 0,
            request_headers: {},
            response_headers: {},
            request_body: '',
            response_body_preview: '',
            raw_entry: {
                timestamp: new Date().toISOString(),
                initiator: 'navigation',
                type: type,
                referrer: document.referrer
            }
        };
        
        sendCapture(entry);
        stats.total++;
        stats.navigation++;
    }
    
    // Public API
    window.PolySniffer = {
        start: function() {
            if (isCapturing) {
                console.log('[PolySniffer] Already capturing');
                return;
            }
            isCapturing = true;
            getCaptureId();
            console.log('[PolySniffer] Capture started');
            captureNavigation('start');
        },
        
        stop: function() {
            if (!isCapturing) {
                console.log('[PolySniffer] Not currently capturing');
                return;
            }
            isCapturing = false;
            flushQueue();
            console.log('[PolySniffer] Capture stopped');
        },
        
        getStats: function() {
            return { ...stats, captureId: captureId, isCapturing: isCapturing };
        },
        
        getCaptureId: function() {
            return getCaptureId();
        },
        
        flush: function() {
            flushQueue();
        }
    };
    
    // Auto-start on page load
    console.log('[PolySniffer] Network capture injector loaded');
    window.PolySniffer.start();
    
    // Flush queue before page unload
    window.addEventListener('beforeunload', function() {
        flushQueue();
    });
    
})();
