<?php
// SuiteCRM Configuration Override for Docker
$sugar_config = array(
    'dbconfig' => array(
        'db_host_name' => getenv('MYSQL_HOST') ?: 'suitecrm-db',
        'db_user_name' => getenv('MYSQL_USER') ?: 'suitecrm',
        'db_password' => getenv('MYSQL_PASSWORD') ?: 'suitecrm_password',
        'db_name' => getenv('MYSQL_DATABASE') ?: 'suitecrm',
        'db_type' => 'mysql',
        'db_port' => getenv('MYSQL_PORT') ?: 3306,
    ),
    'site_url' => getenv('SUITE_URL') ?: 'http://localhost:8081',
    'default_language' => 'en_us',
    'default_theme' => 'SuiteP',
    'cache_dir' => 'cache/',
    'tmp_dir' => 'cache/xml/',
    'upload_dir' => 'upload/',
    'create_default_user' => false,
    'installer_locked' => false,
);

// Multi-tenant configuration
$sugar_config['tenant_id'] = getenv('TENANT_ID') ?: 'default';
$sugar_config['tenant_schema'] = getenv('TENANT_SCHEMA') ?: 'public';

// Security settings
$sugar_config['session_dir'] = 'cache/sessions/';
$sugar_config['verify_client_ip'] = false;

// Email configuration (will be overridden by tenant-specific settings)
$sugar_config['email_default_client'] = 'smtp';
$sugar_config['email_smtp_server'] = 'smtp.gmail.com';
$sugar_config['email_smtp_port'] = 587;
$sugar_config['email_smtp_user'] = '';
$sugar_config['email_smtp_pass'] = '';
$sugar_config['email_smtp_auth_req'] = true;
$sugar_config['email_smtp_ssl'] = 1;