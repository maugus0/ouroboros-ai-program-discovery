-- 003_create_programs.sql
-- Programs linked to institutions with comprehensive academic program details.

CREATE TABLE IF NOT EXISTS programs (
    id CHAR(36) PRIMARY KEY,
    institution_id CHAR(36) NOT NULL,
    program_name VARCHAR(512) NOT NULL,
    degree_type ENUM('bachelors', 'masters', 'phd', 'diploma', 'certificate', 'other') NOT NULL,
    field VARCHAR(256) NOT NULL,
    field_category VARCHAR(128),
    description TEXT,
    requirements JSON,
    deadline DATE,
    tuition_usd DECIMAL(12, 2),
    tuition_currency VARCHAR(8),
    tuition_local DECIMAL(12, 2),
    duration_months INT,
    language VARCHAR(64) DEFAULT 'English',
    mode ENUM('on_campus', 'online', 'hybrid', 'unknown') DEFAULT 'unknown',
    intake VARCHAR(64),
    source_url VARCHAR(512),
    crawled_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE,
    INDEX idx_programs_institution (institution_id),
    INDEX idx_programs_degree_type (degree_type),
    INDEX idx_programs_field (field),
    INDEX idx_programs_field_category (field_category),
    INDEX idx_programs_deadline (deadline),
    INDEX idx_programs_is_active (is_active),
    FULLTEXT INDEX ft_programs_name_desc (program_name, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
