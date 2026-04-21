-- Fix admin log foreign key constraint
-- This script removes invalid constraints and cleans up admin log entries

-- First, delete any admin log entries that reference non-existent users
DELETE FROM django_admin_log 
WHERE user_id NOT IN (SELECT id FROM auth_user);

-- Check for constraints referencing tenantuser
SELECT conname, conrelid::regclass, confrelid::regclass 
FROM pg_constraint 
WHERE confrelid::regclass::text LIKE '%tenantuser%';

-- If any constraints exist, they will need to be dropped
-- DROP CONSTRAINT commands will be shown but not executed here
