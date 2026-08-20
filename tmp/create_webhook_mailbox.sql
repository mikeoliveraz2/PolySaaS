-- Create webhook_mailbox table for orchestration model
CREATE TABLE IF NOT EXISTS webhook_mailbox (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(100) NOT NULL,
    event_id VARCHAR(64) NOT NULL,
    correlation_id UUID NOT NULL,
    envelope JSONB NOT NULL,
    action_path VARCHAR(500) NOT NULL,
    source VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    claimed_at TIMESTAMP,
    processed_at TIMESTAMP,
    error TEXT DEFAULT '',
    result JSONB,
    UNIQUE(tenant_id, event_id)
);

CREATE INDEX IF NOT EXISTS mailbox_consumer_idx ON webhook_mailbox(tenant_id, status, expires_at);
CREATE INDEX IF NOT EXISTS mailbox_status_idx ON webhook_mailbox(status, created_at);
