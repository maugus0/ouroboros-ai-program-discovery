CREATE TABLE IF NOT EXISTS universities (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    country VARCHAR(100) NOT NULL,
    ranking INT NULL,
    website VARCHAR(500) NOT NULL,
    programs_page_url VARCHAR(500) NULL,
    last_crawled TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_country (country),
    INDEX idx_ranking (ranking),
    INDEX idx_last_crawled (last_crawled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
