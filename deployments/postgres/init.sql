-- Agentic Workflow Framework PostgreSQL Schema

-- Create tables for workflow checkpointing and state persistence

-- Workflow executions table
CREATE TABLE IF NOT EXISTS workflow_executions (
    id SERIAL PRIMARY KEY,
    workflow_name VARCHAR(255) NOT NULL,
    workflow_type VARCHAR(255) NOT NULL,
    execution_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    input_state JSONB NOT NULL,
    output_state JSONB,
    execution_log JSONB,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds FLOAT,
    error_message TEXT,
    created_by VARCHAR(255),
    metadata JSONB
);

CREATE INDEX idx_workflow_executions_name ON workflow_executions(workflow_name);
CREATE INDEX idx_workflow_executions_type ON workflow_executions(workflow_type);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_created ON workflow_executions(started_at);

-- Workflow tasks table
CREATE TABLE IF NOT EXISTS workflow_tasks (
    id SERIAL PRIMARY KEY,
    execution_id UUID REFERENCES workflow_executions(execution_id),
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds FLOAT,
    sequence_order INT,
    retry_count INT DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workflow_tasks_execution ON workflow_tasks(execution_id);
CREATE INDEX idx_workflow_tasks_status ON workflow_tasks(status);
CREATE INDEX idx_workflow_tasks_name ON workflow_tasks(task_name);

-- Workflow artifacts table
CREATE TABLE IF NOT EXISTS workflow_artifacts (
    id SERIAL PRIMARY KEY,
    execution_id UUID REFERENCES workflow_executions(execution_id),
    artifact_name VARCHAR(255) NOT NULL,
    artifact_type VARCHAR(100),
    file_path TEXT,
    content BYTEA,
    file_size BIGINT,
    checksum VARCHAR(64),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workflow_artifacts_execution ON workflow_artifacts(execution_id);
CREATE INDEX idx_workflow_artifacts_type ON workflow_artifacts(artifact_type);

-- Workflow metrics table
CREATE TABLE IF NOT EXISTS workflow_metrics (
    id SERIAL PRIMARY KEY,
    execution_id UUID REFERENCES workflow_executions(execution_id),
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT,
    metric_unit VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE INDEX idx_workflow_metrics_execution ON workflow_metrics(execution_id);
CREATE INDEX idx_workflow_metrics_name ON workflow_metrics(metric_name);
CREATE INDEX idx_workflow_metrics_timestamp ON workflow_metrics(timestamp);

-- Workflow cache table
CREATE TABLE IF NOT EXISTS workflow_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_value JSONB,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_workflow_cache_key ON workflow_cache(cache_key);
CREATE INDEX idx_workflow_cache_expires ON workflow_cache(expires_at);

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM workflow_cache WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO agentic_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO agentic_user;
