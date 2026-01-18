<?php
// Enqueue parent and child styles
add_action('wp_enqueue_scripts', 'polysaas_pro_enqueue_styles');
function polysaas_pro_enqueue_styles() {
    // Parent theme stylesheet
    wp_enqueue_style('parent-style', get_template_directory_uri() . '/style.css');

    // Child theme stylesheet (loads after parent)
    wp_enqueue_style('polysaas-pro-style', get_stylesheet_uri(), array('parent-style'), '1.0.0');
}

// Future custom functions go here
?>