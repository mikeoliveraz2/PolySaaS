<?php
/**
 * Plugin Name: PolySaaS Passthrough Auth
 * Description: Auto-login WordPress users via REMOTE_USER header from PolySaaS proxy.
 * Version: 1.0
 * Author: PolySaaS Team
 *
 * Must-use plugin — loads automatically, no activation needed.
 * Works with dose/middleware/passthrough_auth.py which injects:
 *   REMOTE_USER      = user.email
 *   X-User-Email     = user.email
 *   X-User-ID        = user.id
 *   X-User-Name      = full name or username
 *   X-User-Is-Staff  = 'true' | 'false'
 *   X-Tenant-Slug    = tenant slug (when available)
 */

add_action('init', function () {
    if (is_user_logged_in()) {
        return;
    }

    $email = '';

    if (!empty($_SERVER['HTTP_REMOTE_USER'])) {
        $email = sanitize_email($_SERVER['HTTP_REMOTE_USER']);
    } elseif (!empty($_SERVER['REMOTE_USER'])) {
        $email = sanitize_email($_SERVER['REMOTE_USER']);
    } elseif (!empty($_SERVER['HTTP_X_USER_EMAIL'])) {
        $email = sanitize_email($_SERVER['HTTP_X_USER_EMAIL']);
    }

    if (!is_email($email)) {
        return;
    }

    // Optional: validate request came through PolySaaS proxy
    $expected_tenant = defined('POLYSAAS_TENANT_SLUG') ? POLYSAAS_TENANT_SLUG : '';
    if ($expected_tenant) {
        $tenant_slug = isset($_SERVER['HTTP_X_TENANT_SLUG']) ? $_SERVER['HTTP_X_TENANT_SLUG'] : '';
        if ($tenant_slug !== $expected_tenant) {
            error_log('PolySaaS passthrough: tenant mismatch — expected ' . $expected_tenant . ', got ' . $tenant_slug);
            return;
        }
    }

    $user = get_user_by('email', $email);

    if (!$user) {
        // Auto-provision: derive display name from header or email prefix
        $display_name = isset($_SERVER['HTTP_X_USER_NAME']) ? sanitize_text_field($_SERVER['HTTP_X_USER_NAME']) : '';
        $username     = sanitize_user(explode('@', $email)[0], true);
        $password     = wp_generate_password(24, true, true);

        if (username_exists($username)) {
            $username = $username . '_' . wp_rand(100, 999);
        }

        $user_id = wp_create_user($username, $password, $email);

        if (is_wp_error($user_id)) {
            error_log('PolySaaS passthrough: failed to create user ' . $email . ' — ' . $user_id->get_error_message());
            return;
        }

        if ($display_name) {
            wp_update_user([
                'ID'           => $user_id,
                'display_name' => $display_name,
                'first_name'   => explode(' ', $display_name)[0],
            ]);
        }

        // Map PolySaaS staff to WP editor, everyone else to subscriber
        $is_staff = isset($_SERVER['HTTP_X_USER_IS_STAFF']) && $_SERVER['HTTP_X_USER_IS_STAFF'] === 'true';
        $role     = $is_staff ? 'editor' : 'subscriber';
        (new WP_User($user_id))->set_role($role);

        $user = get_user_by('id', $user_id);
        error_log('PolySaaS passthrough: auto-provisioned ' . $email . ' as ' . $role);
    }

    wp_set_current_user($user->ID);
    wp_set_auth_cookie($user->ID, true);
    do_action('wp_login', $user->user_login, $user);
}, 5);
