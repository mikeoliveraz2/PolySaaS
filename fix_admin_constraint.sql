-- Fix Django admin log foreign key constraint
-- This script removes the incorrect foreign key constraint and creates the correct one

BEGIN;

-- First, check if the constraint exists and drop it
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'django_admin_log_user_id_c564eba6_fk_dose_tenantuser_id'
    ) THEN
        ALTER TABLE django_admin_log 
        DROP CONSTRAINT django_admin_log_user_id_c564eba6_fk_dose_tenantuser_id;
        
        RAISE NOTICE 'Dropped old constraint django_admin_log_user_id_c564eba6_fk_dose_tenantuser_id';
    END IF;
END $$;

-- Create the correct foreign key constraint to auth_user
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'django_admin_log_user_id_c564eba6_fk_auth_user_id'
    ) THEN
        ALTER TABLE django_admin_log 
        ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id 
        FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;
        
        RAISE NOTICE 'Created correct constraint django_admin_log_user_id_c564eba6_fk_auth_user_id';
    END IF;
END $$;

-- Clean up any orphaned admin log entries that reference non-existent users
DELETE FROM django_admin_log 
WHERE user_id NOT IN (SELECT id FROM auth_user);

COMMIT;
