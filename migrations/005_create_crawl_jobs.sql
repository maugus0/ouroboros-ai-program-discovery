-- 005_create_crawl_jobs.sql
-- Tracks crawling operations for institutions and programs.

CREATE TABLE IF NOT EXISTS crawl_jobs (
    id CHAR(36) PRIMARY KEY,
    job_type ENUM('institution_ranking', 'program_list', 'program_detail', 'full_sync') NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    target_url VARCHAR(512),
    items_found INT DEFAULT 0,
    items_stored INT DEFAULT 0,
    error_message TEXT,
    metadata JSON,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_crawl_jobs_status (status),
    INDEX idx_crawl_jobs_job_type (job_type),
    INDEX idx_crawl_jobs_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
