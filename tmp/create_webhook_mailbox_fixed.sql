-- Set schema to public (where cross-tenant tables live)
SET search_path TO public;

-- Drop existing table if it has issues
DROP TABLE IF EXISTS webhook_mailbox CASCADE;

-- Create webhook_mailbox table with proper foreign key
CREATE TABLE webhook_mailbox (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(100) NOT NULL REFERENCES dose_tenant(schema_name) ON DELETE CASCADE,
    event_id VARCHAR(64) NOT NULL,
    correlation_id UUID NOT NULL,
    envelope JSONB NOT NULL,
    action_path VARCHAR(500) NOT NULL,
    source VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL CHECK (status IN ('pending', 'claimed', 'processed', 'failed', 'expired')),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    claimed_at TIMESTAMP,
    processed_at TIMESTAMP,
    error TEXT DEFAULT '',
    result JSONB,
    CONSTRAINT webhook_mailbox_unique_event UNIQUE(tenant_id, event_id)
);

-- Create indexes for efficient consumer queries
CREATE INDEX mailbox_consumer_idx ON webhook_mailbox(tenant_id, status, expires_at);
CREATE INDEX mailbox_status_idx ON webhook_mailbox(status, created_at);
CREATE INDEX mailbox_tenant_idx ON webhook_mailbox(tenant_id);

-- Confirm success
SELECT 'webhook_mailbox table created successfully in public schema' AS status;
