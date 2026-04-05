  function getWidth() {
    var scope = document.querySelector('.polysaas-passthrough-scope');
    if (scope) return scope.offsetWidth;
    var content = document.querySelector('.content-wrapper') || document.querySelector('.content');
    return content ? content.offsetWidth : window.innerWidth;
  }

  function getHeight() {
    var scope = document.querySelector('.polysaas-passthrough-scope');
    if (scope) return scope.offsetHeight;
    return window.innerHeight;
  }

  try {
    Object.defineProperty(window, 'innerWidth', {
      get: function() { return getWidth(); },
      configurable: true
    });
    Object.defineProperty(window, 'innerHeight', {
      get: function() { return getHeight(); },
      configurable: true
    });
    
    var _matchMedia = window.matchMedia;
    window.matchMedia = function(query) {
      if (query.indexOf('max-width') !== -1 || query.indexOf('min-width') !== -1 || 
          query.indexOf('max-height') !== -1 || query.indexOf('min-height') !== -1) {
        var width = getWidth();
        var height = getHeight();
        
        var wMatch = query.match(/(min|max)-width:\s*(\d+)px/);
        if (wMatch) {
          var type = wMatch[1];
          var val = parseInt(wMatch[2], 10);
          var res = (type === 'min') ? (width >= val) : (width <= val);
          return { matches: res, media: query, onchange: null, addListener: function(){}, removeListener: function(){}, addEventListener: function(){}, removeEventListener: function(){}, dispatchEvent: function(){ return false; } };
        }
        
        var hMatch = query.match(/(min|max)-height:\s*(\d+)px/);
        if (hMatch) {
          var type = hMatch[1];
          var val = parseInt(hMatch[2], 10);
          var res = (type === 'min') ? (height >= val) : (height <= val);
          return { matches: res, media: query, onchange: null, addListener: function(){}, removeListener: function(){}, addEventListener: function(){}, removeEventListener: function(){}, dispatchEvent: function(){ return false; } };
        }
      }
      return _matchMedia.call(window, query);
    };
    console.log('[PolySaaS] Adaptive UI shim active (innerWidth/Height proxied)');
  } catch(e) {
    console.warn('[PolySaaS] Failed to proxy innerWidth/Height:', e);
  }
