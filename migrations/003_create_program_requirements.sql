CREATE TABLE IF NOT EXISTS program_requirements (
    id VARCHAR(36) PRIMARY KEY,
    program_id VARCHAR(36) NOT NULL,
    requirement_type ENUM('min_gpa', 'prerequisite_course', 'language_test', 'work_experience', 'research_experience', 'other') NOT NULL,
    requirement_value TEXT NOT NULL,
    is_mandatory BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE,
    INDEX idx_program_id (program_id),
    INDEX idx_requirement_type (requirement_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
