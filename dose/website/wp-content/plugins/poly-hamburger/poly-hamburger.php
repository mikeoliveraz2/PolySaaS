<?php
/**
 * Plugin Name: Poly Hamburger Snippet
 * Description: Injects a small responsive hamburger + features mobile menu for PolySaaS staging.
 * Version: 0.1
 * Author: Automated Assistant
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit; // Exit if accessed directly
}

function poly_hamburger_head() {
    ?>
    <style>
    /* Ensure inline writes can't push layout offscreen */
    body[style]{margin-left:0!important;margin-right:0!important}

    /* Breakpoint and menu layout */
    @media (min-width:820px){
      .polysaas-nav .hamburger{display:none}
      .polysaas-nav .mobile-menu{display:none!important}
      .polysaas-nav .desktop-menu{display:flex!important}
    }
    @media (max-width:819px){
      .polysaas-nav .desktop-menu{display:none!important}
      .polysaas-nav .nav-container{justify-content:space-between;padding:10px 16px}
      .polysaas-nav .hamburger{display:block}
      .polysaas-nav .mobile-menu.open{display:block!important}
    }

    /* Animations + scroll lock */
    .polysaas-nav .mobile-menu{transition:transform .26s ease,opacity .2s ease;transform-origin:top center;opacity:0;transform:translateY(-6px)}
    .polysaas-nav .mobile-menu.open{opacity:1;transform:translateY(0)}
    .polysaas-nav .features-list-mobile{max-height:0;overflow:hidden;transition:max-height .26s ease,opacity .2s ease;opacity:0}
    .polysaas-nav .features-list-mobile.open{max-height:640px;opacity:1}
    body.no-scroll{overflow:hidden;touch-action:none}
    </style>
    <?php
}
add_action( 'wp_head', 'poly_hamburger_head', 999 );

function poly_hamburger_footer() {
    ?>
    <script>
    (function(){
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
add_action( 'wp_footer', 'poly_hamburger_footer', 999 );

// End of poly-hamburger.php
