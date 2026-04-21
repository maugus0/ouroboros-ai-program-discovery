-- 002_create_institution_rankings.sql
-- Junction table allowing one institution to appear in multiple ranking sources/years.

CREATE TABLE IF NOT EXISTS institution_rankings (
    id CHAR(36) PRIMARY KEY,
    institution_id CHAR(36) NOT NULL,
    ranking_source ENUM('qs_world', 'times_higher', 'arwu', 'us_news', 'webometrics', 'cwur', 'other') NOT NULL,
    ranking_year INT NOT NULL,
    rank_display VARCHAR(32) NOT NULL,
    rank_position INT NOT NULL,
    previous_rank_display VARCHAR(32),
    overall_score DECIMAL(5, 2),
    source_url VARCHAR(512),
    raw_metadata JSON,
    crawled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_institution_ranking (institution_id, ranking_source, ranking_year),
    FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE,
    INDEX idx_rankings_source_year (ranking_source, ranking_year),
    INDEX idx_rankings_rank_position (rank_position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
