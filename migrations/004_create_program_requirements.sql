-- 004_create_program_requirements.sql
-- Granular program requirements for structured filtering and matching.

CREATE TABLE IF NOT EXISTS program_requirements (
    id CHAR(36) PRIMARY KEY,
    program_id CHAR(36) NOT NULL,
    requirement_type ENUM(
        'gpa', 'gre', 'gmat', 'toefl', 'ielts', 'duolingo',
        'sat', 'act', 'work_experience', 'degree', 'portfolio',
        'interview', 'essay', 'recommendation', 'other'
    ) NOT NULL,
    requirement_name VARCHAR(256) NOT NULL,
    requirement_value VARCHAR(256),
    is_mandatory BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE,
    INDEX idx_requirements_program (program_id),
    INDEX idx_requirements_type (requirement_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
