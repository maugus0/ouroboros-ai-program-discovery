-- 001_create_institutions.sql
-- Canonical institution table; each university appears once regardless of how many rankings it has.

CREATE TABLE IF NOT EXISTS institutions (
    id CHAR(36) PRIMARY KEY,
    name VARCHAR(512) NOT NULL,
    slug VARCHAR(512) NOT NULL UNIQUE,
    country VARCHAR(128) NOT NULL,
    city VARCHAR(128),
    region VARCHAR(128),
    website_url VARCHAR(512),
    logo_url VARCHAR(512),
    institution_type ENUM('public', 'private', 'private_not_for_profit', 'unknown') DEFAULT 'unknown',
    size ENUM('small', 'medium', 'large', 'extra_large', 'unknown') DEFAULT 'unknown',
    focus ENUM('full_comprehensive', 'focused', 'specialist', 'unknown') DEFAULT 'unknown',
    research_output ENUM('very_high', 'high', 'medium', 'low', 'very_low', 'unknown') DEFAULT 'unknown',
    status ENUM('verified', 'pending', 'rejected') DEFAULT 'pending',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_institutions_country (country),
    INDEX idx_institutions_status (status),
    INDEX idx_institutions_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
