-- 006_create_llm_call_logs.sql
-- Tracks LLM API usage for cost monitoring and debugging.

CREATE TABLE IF NOT EXISTS llm_call_logs (
    id CHAR(36) PRIMARY KEY,
    provider ENUM('openai', 'anthropic', 'other') NOT NULL,
    model VARCHAR(64) NOT NULL,
    purpose VARCHAR(128) NOT NULL,
    input_tokens INT NOT NULL DEFAULT 0,
    output_tokens INT NOT NULL DEFAULT 0,
    latency_ms INT,
    status ENUM('success', 'error', 'timeout') NOT NULL,
    error_message TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_llm_logs_provider (provider),
    INDEX idx_llm_logs_status (status),
    INDEX idx_llm_logs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
