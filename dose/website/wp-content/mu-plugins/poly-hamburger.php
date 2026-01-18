will it replace the top menulets see if there is a problems<?php
/**
 * MU-Plugin: Poly Hamburger Snippet
 * Purpose: Auto-load a small responsive hamburger + features mobile menu for PolySaaS staging.
 * Version: 0.1
 * Author: Automated Assistant
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit; // Exit if accessed directly
}

function poly_hamburger_head_mu() {
  // Only run on the site front page/home to avoid injecting globally
  if ( ! function_exists( 'is_front_page' ) ) {
    <?php
    /**
     * PolySaaS Simple Nav mu-plugin
     * Outputs a single, simple menu on the front page with a vertical "Features" submenu
     * and lightweight popups for each feature. No hamburger, no complex bundles.
     */

    if (!defined('WPINC')) {
        die;
    }

    // Only run on the front page / blog home
    function polysaas_simple_nav_should_run() {
        return (function_exists('is_front_page') && (is_front_page() || is_home()));
    }

    add_action('wp_head', function () {
        if (!polysaas_simple_nav_should_run()) {
            return;
        }
        ?>
        <style>
        /* Simple header nav */
        .polysaas-nav{font-family:inherit;background:#000;color:#fff;padding:12px 18px;display:block}
        .polysaas-nav .ps-inner{max-width:1200px;margin:0 auto;display:flex;align-items:center;gap:24px}
        .polysaas-nav a{color:#fff;text-decoration:none}
        .polysaas-nav .ps-left{flex:1}
        .polysaas-nav .ps-right{display:flex;gap:18px;align-items:center}

        /* Features submenu */
        .ps-features{position:relative}
        .ps-features .features-sub{display:none;position:absolute;left:0;top:100%;background:#111;border:1px solid #222;padding:12px;box-shadow:0 6px 18px rgba(0,0,0,.5);z-index:1200}
        .ps-features .features-sub li{list-style:none;margin:6px 0}
        .ps-features .features-sub a{display:block;padding:6px 10px;color:#eee}
        .ps-features:hover .features-sub{display:block}

        /* Modal (popup) */
        .ps-modal{display:none;position:fixed;left:0;top:0;width:100%;height:100%;background:rgba(0,0,0,.6);align-items:center;justify-content:center;z-index:1300}
        .ps-modal.open{display:flex}
        .ps-modal .ps-modal-inner{background:#fff;color:#111;max-width:900px;width:92%;padding:20px;border-radius:6px;box-shadow:0 10px 40px rgba(0,0,0,.4);position:relative}
        .ps-modal .ps-close{position:absolute;right:12px;top:12px;background:#222;color:#fff;border:none;padding:6px 10px;cursor:pointer}

        @media (max-width:800px){
            .polysaas-nav .ps-inner{padding:0 10px;gap:12px}
            .ps-features:hover .features-sub{position:static;box-shadow:none;border:none;padding:6px;background:transparent}
            .ps-features .features-sub a{color:#fff;padding:6px 0}
        }
        </style>
        <?php
    });

    add_action('wp_body_open', function () {
        if (!polysaas_simple_nav_should_run()) {
            return;
        }

        // Only output modal container; submenu will be injected into existing nav via JS
        echo <<<'HTML'
        <div id="polysaas-modals">
          <!-- Modals will be toggled open/closed by the injected submenu script -->
          <div class="ps-modal" id="modal-f1" role="dialog" aria-hidden="true">
            <div class="ps-modal-inner"><button class="ps-close" aria-label="Close">×</button><h2>Architecture</h2><p>Details about Architecture.</p></div>
          </div>
          <div class="ps-modal" id="modal-f2" role="dialog" aria-hidden="true">
            <div class="ps-modal-inner"><button class="ps-close">×</button><h2>PolySaaS Architecture</h2><p>Details about PolySaaS Architecture.</p></div>
          </div>
          <div class="ps-modal" id="modal-f3" role="dialog" aria-hidden="true">
            <div class="ps-modal-inner"><button class="ps-close">×</button><h2>Portal</h2><p>Details about the Portal.</p></div>
          </div>
          <div class="ps-modal" id="modal-f4" role="dialog" aria-hidden="true">
            <div class="ps-modal-inner"><button class="ps-close">×</button><h2>Dynamic Orchestration</h2><p>Details about Dynamic Orchestration.</p></div>
          </div>
          <div class="ps-modal" id="modal-f5" role="dialog" aria-hidden="true">
            <div class="ps-modal-inner"><button class="ps-close">×</button><h2>Data Driven Orchestration</h2><p>Details about Data Driven Orchestration.</p></div>
          </div>
          <div class="ps-modal" id="modal-f6" role="dialog" aria-hidden="true">
            <div class="ps-modal-inner"><button class="ps-close">×</button><h2>Atomic Services</h2><p>Details about Atomic Services.</p></div>
          </div>
          <div class="ps-modal" id="modal-f7" role="dialog" aria-hidden="true">
            <div class="ps-modal-inner"><button class="ps-close">×</button><h2>Integrations</h2><p>Integrations and connectors.</p></div>
          </div>
          <div class="ps-modal" id="modal-f8" role="dialog" aria-hidden="true">
            <div class="ps-modal-inner"><button class="ps-close">×</button><h2>Security & Compliance</h2><p>Security & Compliance details.</p></div>
          </div>
          <div class="ps-modal" id="modal-f9" role="dialog" aria-hidden="true">
            <div class="ps-modal-inner"><button class="ps-close">×</button><h2>Admin & Roles</h2><p>Admin interface and role management.</p></div>
          </div>
          <div class="ps-modal" id="modal-f10" role="dialog" aria-hidden="true">
            <div class="ps-modal-inner"><button class="ps-close">×</button><h2>Developer Tools</h2><p>Developer APIs and tools.</p></div>
          </div>
        </div>
        HTML;
    });

    add_action('wp_footer', function () {
        if (!polysaas_simple_nav_should_run()) {
            return;
        }
        ?>
        <script>
        (function(){
          // Features data
          var features = [
            {id:'f1',label:'Architecture'},
            {id:'f2',label:'PolySaaS Architecture'},
            {id:'f3',label:'Portal'},
            {id:'f4',label:'Dynamic Orchestration'},
            {id:'f5',label:'Data Driven Orchestration'},
            {id:'f6',label:'Atomic Services'},
            {id:'f7',label:'Integrations'},
            {id:'f8',label:'Security & Compliance'},
            {id:'f9',label:'Admin & Roles'},
            {id:'f10',label:'Developer Tools'}
          ];

          function createFeaturesNode(){
            var wrapper = document.createElement('div');
            wrapper.className = 'ps-features';
            var toggle = document.createElement('a'); toggle.href='#'; toggle.textContent='Features ▾';
            wrapper.appendChild(toggle);
            var ul = document.createElement('ul'); ul.className='features-sub'; ul.setAttribute('role','menu');
            features.forEach(function(f){
              var li = document.createElement('li');
              var a = document.createElement('a'); a.href='#'; a.setAttribute('data-feature', f.id); a.textContent = f.label;
              li.appendChild(a); ul.appendChild(li);
            });
            wrapper.appendChild(ul);
            return wrapper;
          }

          function injectIntoNav(){
            if(document.querySelector('.ps-features')) return; // already injected

            var selectors = ['nav[aria-label="Main"]','nav.main-navigation','nav[role="navigation"]','.nav-menu','.primary-menu','header nav','.menu'];
            var nav = null;
            for(var i=0;i<selectors.length;i++){
              nav = document.querySelector(selectors[i]);
              if(nav) break;
            }
            if(!nav){
              // fallback: append to body start
              var target = document.body.querySelector('header') || document.body;
              if(target){ target.appendChild(createFeaturesNode()); }
              return;
            }

            // Prefer adding as last child inside nav
            try{ nav.appendChild(createFeaturesNode()); }catch(e){ nav.insertAdjacentElement('beforeend', createFeaturesNode()); }
          }

          function bindFeatureClicks(){
            document.addEventListener('click', function(ev){
              var a = ev.target.closest && ev.target.closest('[data-feature]');
              if(a){ ev.preventDefault(); var id = a.getAttribute('data-feature'); var modal = document.getElementById('modal-'+id); if(modal){ modal.classList.add('open'); modal.setAttribute('aria-hidden','false'); } }
              var closeBtn = ev.target.closest && ev.target.closest('.ps-close');
              if(closeBtn){ ev.preventDefault(); var m = closeBtn.closest('.ps-modal'); if(m){ m.classList.remove('open'); m.setAttribute('aria-hidden','true'); } }
            });

            document.getElementById('polysaas-modals').addEventListener('click', function(ev){ if(ev.target.classList.contains('ps-modal')){ ev.target.classList.remove('open'); ev.target.setAttribute('aria-hidden','true'); } });
            document.addEventListener('keydown', function(e){ if(e.key==='Escape'){ document.querySelectorAll('.ps-modal.open').forEach(function(m){ m.classList.remove('open'); m.setAttribute('aria-hidden','true'); }); } });
          }

          // Run on DOM ready
          if(document.readyState==='loading'){
            document.addEventListener('DOMContentLoaded', function(){ injectIntoNav(); bindFeatureClicks(); });
          } else { injectIntoNav(); bindFeatureClicks(); }
        })();
        </script>
        <?php
    });

    </style>
    <?php
}
add_action( 'wp_head', 'poly_hamburger_head_mu', 999 );

/**
 * Output the minimal nav server-side so it appears in View Source and editor previews.
 */
function poly_hamburger_body_mu(){
  if ( ! function_exists( 'is_front_page' ) ) {
    return;
  }
  if ( ! ( is_front_page() || is_home() ) ) {
    return;
  }

  // Server-side markup — keeps it visible to editors and in the page source.
  echo '<nav class="polysaas-nav" role="navigation" aria-label="Site">\n';
  echo '  <div class="nav-container">\n';
  echo '    <a class="brand" href="/">PolySaaS</a>\n';
  echo '    <button class="hamburger" aria-expanded="false" aria-controls="polysaas-mobile-menu">☰</button>\n';
  echo '    <div class="desktop-menu">\n';
  echo '      <a href="/">Home</a>\n';
  echo '      <div class="features">\n';
  echo '        <button class="features-toggle" aria-expanded="false">Features</button>\n';
  echo '        <div class="features-list">\n';
  echo '          <a href="#feature-a">Feature A</a>\n';
  echo '          <a href="#feature-b">Feature B</a>\n';
  echo '        </div>\n';
  echo '      </div>\n';
  echo '    </div>\n';
  echo '  </div>\n';
  echo '  <div id="polysaas-mobile-menu" class="mobile-menu" aria-hidden="true">\n';
  echo '    <nav>\n';
  echo '      <a href="/">Home</a>\n';
  echo '      <div class="features-list-mobile">\n';
  echo '        <a href="#feature-a">Feature A</a>\n';
  echo '        <a href="#feature-b">Feature B</a>\n';
  echo '      </div>\n';
  echo '    </nav>\n';
  echo '  </div>\n';
  echo '</nav>\n';
}
add_action( 'wp_body_open', 'poly_hamburger_body_mu', 5 );

function poly_hamburger_footer_mu() {
  // Only run on the site front page/home to avoid injecting globally
  if ( ! function_exists( 'is_front_page' ) ) {
    return;
  }
  if ( ! ( is_front_page() || is_home() ) ) {
    return;
  }

  ?>
    <script>
    (function(){
      // Auto-inject a minimal nav when none exists (keeps plugin resilient to missing header)
      if(!document.querySelector('.polysaas-nav')){
        const navHtml = `
        <nav class="polysaas-nav" role="navigation" aria-label="Site">
          <div class="nav-container">
            <a class="brand" href="/">PolySaaS</a>
            <button class="hamburger" aria-expanded="false" aria-controls="polysaas-mobile-menu">☰</button>
            <div class="desktop-menu">
              <a href="/">Home</a>
              <div class="features">
                <button class="features-toggle" aria-expanded="false">Features</button>
                <div class="features-list">
                  <a href="#">Feature A</a>
                  <a href="#">Feature B</a>
                </div>
              </div>
            </div>
          </div>
          <div id="polysaas-mobile-menu" class="mobile-menu" aria-hidden="true">
            <nav>
              <a href="/">Home</a>
              <div class="features-list-mobile">
                <a href="#">Feature A</a>
                <a href="#">Feature B</a>
              </div>
            </nav>
          </div>
        </nav>`;
        try{ document.body.insertAdjacentHTML('afterbegin', navHtml); }catch(e){}
      }

      const root=document;
      const ham=root.querySelector('.polysaas-nav .hamburger');
      const mobile=root.querySelector('.polysaas-nav .mobile-menu');
      const featuresToggle=root.querySelector('.polysaas-nav .features-toggle');
      const featuresList=root.querySelector('.polysaas-nav .features-list-mobile');

      function openMobile(){ if(!ham||!mobile) return; ham.setAttribute('aria-expanded','true'); mobile.classList.add('open'); mobile.setAttribute('aria-hidden','false'); document.body.classList.add('no-scroll'); }
      function closeMobile(){ if(!ham||!mobile) return; ham.setAttribute('aria-expanded','false'); mobile.classList.remove('open'); mobile.setAttribute('aria-hidden','true'); document.body.classList.remove('no-scroll'); }
      function toggleMobile(){ if(!ham||!mobile) return; (ham.getAttribute('aria-expanded')==='true')?closeMobile():openMobile(); if(ham.getAttribute('aria-expanded')!=='true'){ if(featuresList&&featuresToggle){ featuresList.classList.remove('open'); featuresToggle.setAttribute('aria-expanded','false'); } } }
      function toggleFeatures(){ if(!featuresList||!featuresToggle) return; const open=featuresList.classList.contains('open'); if(open){ featuresList.classList.remove('open'); featuresToggle.setAttribute('aria-expanded','false'); } else { featuresList.classList.add('open'); featuresToggle.setAttribute('aria-expanded','true'); } }
      function closeAll(){ closeMobile(); if(featuresList&&featuresToggle){ featuresList.classList.remove('open'); featuresToggle.setAttribute('aria-expanded','false'); } }

      if(ham) ham.addEventListener('click', function(e){ e.stopPropagation(); toggleMobile(); });
      if(featuresToggle) featuresToggle.addEventListener('click', function(e){ e.stopPropagation(); toggleFeatures(); });
      document.addEventListener('click', function(e){ if(mobile&&mobile.classList.contains('open')){ if(e.target!==ham&&!mobile.contains(e.target)){ closeAll(); } } });
      document.addEventListener('keydown', function(e){ if(e.key==='Escape'){ closeAll(); } });
      window.addEventListener('resize', function(){ if(window.innerWidth>=820){ closeAll(); } });
    })();
    </script>
    <?php
}
add_action( 'wp_footer', 'poly_hamburger_footer_mu', 999 );

// End of mu poly-hamburger
