-- ===================================
-- MySQL DDL
-- 외래키 의존성 순서대로 작성
-- ===================================
-- 1. file_objects
CREATE TABLE file_objects (
    file_id BIGINT AUTO_INCREMENT,
    storage_provider VARCHAR(20) NOT NULL,
    bucket VARCHAR(100) NULL,
    object_key VARCHAR(500) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    content_type VARCHAR(100) NULL,
    size_bytes BIGINT NOT NULL,
    checksum VARCHAR(128) NULL,
    created_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (file_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 2. users
CREATE TABLE users (
    user_id BIGINT AUTO_INCREMENT,
    profile_image_file_id BIGINT NULL,
    role VARCHAR(20) NOT NULL,
    nickname VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (user_id),
    UNIQUE KEY uk_users_nickname (nickname),
    KEY idx_users_profile_image (profile_image_file_id),
    CONSTRAINT fk_users_profile_image FOREIGN KEY (profile_image_file_id) REFERENCES file_objects (file_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 3. user_oauth_accounts
CREATE TABLE user_oauth_accounts (
    oauth_account_id BIGINT AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    email VARCHAR(100) NOT NULL,
    provider VARCHAR(20) NOT NULL,
    provider_user_id VARCHAR(100) NOT NULL,
    provider_email VARCHAR(255) NULL,
    connected_at DATETIME (6) NOT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (oauth_account_id),
    UNIQUE KEY uk_oauth_accounts_provider_user (provider, provider_user_id),
    KEY idx_oauth_accounts_user (user_id),
    CONSTRAINT fk_oauth_accounts_user FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 4. auth_refresh_tokens
CREATE TABLE auth_refresh_tokens (
    token_id BIGINT AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    token_value VARCHAR(64) NOT NULL,
    expires_at DATETIME (6) NOT NULL,
    created_at DATETIME (6) NOT NULL,
    revoked_at DATETIME (6) NULL,
    PRIMARY KEY (token_id),
    UNIQUE KEY uk_refresh_tokens_value (token_value),
    KEY idx_refresh_tokens_user (user_id),
    KEY idx_refresh_tokens_expires (expires_at),
    CONSTRAINT fk_refresh_tokens_user FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 5. user_withdrawals
CREATE TABLE user_withdrawals (
    withdrawal_id BIGINT AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    reason TEXT NULL,
    created_at DATETIME (6) NOT NULL,
    PRIMARY KEY (withdrawal_id),
    UNIQUE KEY uk_withdrawals_user (user_id),
    CONSTRAINT fk_withdrawals_user FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 6. companies
CREATE TABLE companies (
    company_id BIGINT AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    domain VARCHAR(100) NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (company_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 7. company_aliases
CREATE TABLE company_aliases (
    alias_id BIGINT AUTO_INCREMENT,
    company_id BIGINT NOT NULL,
    source VARCHAR(30) NOT NULL,
    alias_name VARCHAR(150) NOT NULL,
    alias_normalized VARCHAR(150) NOT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (alias_id),
    KEY idx_company_aliases_company (company_id),
    UNIQUE KEY uk_company_aliases_company_norm (company_id, alias_normalized),
    CONSTRAINT fk_company_aliases_company FOREIGN KEY (company_id) REFERENCES companies (company_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 8. skills
CREATE TABLE skills (
    skill_id BIGINT AUTO_INCREMENT,
    skill_name VARCHAR(50) NOT NULL,
    category VARCHAR(50) NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (skill_id),
    UNIQUE KEY uk_skills_name (skill_name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 9. skill_aliases
CREATE TABLE skill_aliases (
    alias_id BIGINT AUTO_INCREMENT,
    skill_id BIGINT NOT NULL,
    alias_name VARCHAR(100) NOT NULL,
    alias_normalized VARCHAR(100) NOT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (alias_id),
    KEY idx_skill_aliases_skill (skill_id),
    UNIQUE KEY uk_skill_aliases_skill_norm (skill_id, alias_normalized),
    CONSTRAINT fk_skill_aliases_skill FOREIGN KEY (skill_id) REFERENCES skills (skill_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 10. job_masters
CREATE TABLE job_masters (
    job_master_id BIGINT AUTO_INCREMENT,
    company_id BIGINT NOT NULL,
    job_title VARCHAR(150) NOT NULL,
    main_tasks JSON NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    ai_summary TEXT NULL,
    evaluation_criteria JSON NULL,
    status VARCHAR(20) NOT NULL,
    last_seen_at DATETIME (6) NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (job_master_id),
    KEY idx_job_masters_company (company_id),
    KEY idx_job_masters_open_enddate (
        status,
        end_date,
        job_master_id,
        company_id,
        job_title,
        start_date
    ),
    KEY idx_job_masters_company_open_enddate (
        company_id,
        status,
        end_date,
        job_master_id,
        job_title,
        start_date
    ),
    CONSTRAINT fk_job_masters_company FOREIGN KEY (company_id) REFERENCES companies (company_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 11. job_posts
CREATE TABLE job_posts (
    job_post_id BIGINT AUTO_INCREMENT,
    job_master_id BIGINT NOT NULL,
    ai_job_id BIGINT NOT NULL,
    company_id BIGINT NOT NULL,
    created_by BIGINT NULL,
    source_type VARCHAR(20) NOT NULL,
    source_url VARCHAR(500) NOT NULL,
    source_url_hash CHAR(64) NOT NULL,
    raw_company_name VARCHAR(100) NULL,
    raw_job_title VARCHAR(150) NULL,
    main_tasks JSON NULL,
    recruitment_status VARCHAR(20) NOT NULL,
    registration_status VARCHAR(20) NOT NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    fingerprint_hash CHAR(64) NOT NULL,
    PRIMARY KEY (job_post_id),
    UNIQUE KEY uk_job_posts_source_url (source_url),
    KEY idx_job_posts_master (job_master_id),
    KEY idx_job_posts_company (company_id),
    KEY idx_job_posts_created_by (created_by),
    KEY idx_job_posts_fingerprint (fingerprint_hash),
    CONSTRAINT fk_job_posts_master FOREIGN KEY (job_master_id) REFERENCES job_masters (job_master_id),
    CONSTRAINT fk_job_posts_company FOREIGN KEY (company_id) REFERENCES companies (company_id),
    CONSTRAINT fk_job_posts_created_by FOREIGN KEY (created_by) REFERENCES users (user_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 12. job_master_skills
CREATE TABLE job_master_skills (
    job_master_id BIGINT NOT NULL,
    skill_id BIGINT NOT NULL,
    created_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (job_master_id, skill_id),
    KEY idx_job_master_skills_skill (skill_id),
    CONSTRAINT fk_job_master_skills_master FOREIGN KEY (job_master_id) REFERENCES job_masters (job_master_id),
    CONSTRAINT fk_job_master_skills_skill FOREIGN KEY (skill_id) REFERENCES skills (skill_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 13. job_applications
CREATE TABLE job_applications (
    job_application_id BIGINT AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    job_master_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (job_application_id),
    KEY idx_job_applications_user (user_id),
    KEY idx_job_applications_master (job_master_id),
    UNIQUE KEY uk_job_applications_user_master (user_id, job_master_id),
    CONSTRAINT fk_job_applications_user FOREIGN KEY (user_id) REFERENCES users (user_id),
    CONSTRAINT fk_job_applications_master FOREIGN KEY (job_master_id) REFERENCES job_masters (job_master_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 14. application_documents
CREATE TABLE application_documents (
    application_document_id BIGINT AUTO_INCREMENT,
    job_application_id BIGINT NOT NULL,
    file_id BIGINT NOT NULL,
    doc_type VARCHAR(20) NOT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (application_document_id),
    KEY idx_application_documents_application (job_application_id),
    KEY idx_application_documents_file (file_id),
    UNIQUE KEY uk_application_documents_application_type (job_application_id, doc_type),
    CONSTRAINT fk_application_documents_application FOREIGN KEY (job_application_id) REFERENCES job_applications (job_application_id),
    CONSTRAINT fk_application_documents_file FOREIGN KEY (file_id) REFERENCES file_objects (file_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 15. application_document_parsed
CREATE TABLE application_document_parsed (
    parsed_content_id BIGINT AUTO_INCREMENT,
    application_document_id BIGINT NOT NULL,
    raw_text TEXT NOT NULL,
    structured_data JSON NULL,
    summary TEXT NULL,
    parsing_status VARCHAR(20) NOT NULL,
    model_info VARCHAR(50) NULL,
    token_count INT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    PRIMARY KEY (parsed_content_id),
    UNIQUE KEY uk_parsed_content_document (application_document_id),
    CONSTRAINT fk_parsed_content_document FOREIGN KEY (application_document_id) REFERENCES application_documents (application_document_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 16. ai_eval_jobs
CREATE TABLE ai_eval_jobs (
    eval_job_id BIGINT AUTO_INCREMENT,
    job_application_id BIGINT NOT NULL,
    requested_by BIGINT NOT NULL,
    eval_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT NULL,
    created_at DATETIME (6) NOT NULL,
    PRIMARY KEY (eval_job_id),
    KEY idx_ai_eval_jobs_application (job_application_id),
    KEY idx_ai_eval_jobs_requested_by (requested_by),
    CONSTRAINT fk_ai_eval_jobs_application FOREIGN KEY (job_application_id) REFERENCES job_applications (job_application_id),
    CONSTRAINT fk_ai_eval_jobs_requested_by FOREIGN KEY (requested_by) REFERENCES users (user_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 17. ai_resume_analysis
CREATE TABLE ai_resume_analysis (
    resume_analysis_id BIGINT AUTO_INCREMENT,
    job_application_id BIGINT NOT NULL,
    ai_analysis_report TEXT NOT NULL,
    job_fit_score TEXT NOT NULL,
    experience_clarity_score TEXT NOT NULL,
    readability_score TEXT NOT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (resume_analysis_id),
    UNIQUE KEY uk_resume_analysis_application (job_application_id),
    CONSTRAINT fk_resume_analysis_application FOREIGN KEY (job_application_id) REFERENCES job_applications (job_application_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 18. ai_portfolio_analysis
CREATE TABLE ai_portfolio_analysis (
    portfolio_analysis_id BIGINT AUTO_INCREMENT,
    job_application_id BIGINT NOT NULL,
    ai_analysis_report TEXT NOT NULL,
    problem_solving_score TEXT NOT NULL,
    contribution_clarity_score TEXT NOT NULL,
    technical_depth_score TEXT NOT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (portfolio_analysis_id),
    UNIQUE KEY uk_portfolio_analysis_application (job_application_id),
    CONSTRAINT fk_portfolio_analysis_application FOREIGN KEY (job_application_id) REFERENCES job_applications (job_application_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 19. ai_applicant_evaluation
CREATE TABLE ai_applicant_evaluation (
    evaluation_id BIGINT AUTO_INCREMENT,
    job_application_id BIGINT NOT NULL,
    overall_score INT NOT NULL,
    one_line_review TEXT NOT NULL,
    feedback_detail TEXT NOT NULL,
    comparison_scores JSON NOT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (evaluation_id),
    UNIQUE KEY uk_applicant_evaluation_application (job_application_id),
    CONSTRAINT fk_applicant_evaluation_application FOREIGN KEY (job_application_id) REFERENCES job_applications (job_application_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 20. ai_applicant_comparison
CREATE TABLE ai_applicant_comparison (
    comparison_id BIGINT AUTO_INCREMENT,
    job_master_id BIGINT NOT NULL,
    my_application_id BIGINT NOT NULL,
    competitor_application_id BIGINT NOT NULL,
    comparison_metrics JSON NOT NULL,
    strengths_report TEXT NOT NULL,
    weaknesses_report TEXT NOT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (comparison_id),
    KEY idx_applicant_comparison_master (job_master_id),
    KEY idx_applicant_comparison_my (my_application_id),
    KEY idx_applicant_comparison_competitor (competitor_application_id),
    CONSTRAINT fk_applicant_comparison_master FOREIGN KEY (job_master_id) REFERENCES job_masters (job_master_id),
    CONSTRAINT fk_applicant_comparison_my FOREIGN KEY (my_application_id) REFERENCES job_applications (job_application_id),
    CONSTRAINT fk_applicant_comparison_competitor FOREIGN KEY (competitor_application_id) REFERENCES job_applications (job_application_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 21. chat_rooms
CREATE TABLE chat_rooms (
    chat_room_id BIGINT AUTO_INCREMENT,
    job_master_id BIGINT NOT NULL,
    created_by BIGINT NOT NULL,
    room_name VARCHAR(50) NOT NULL,
    max_participants INT NOT NULL,
    room_goal VARCHAR(20) NOT NULL,
    cutline_score INT NOT NULL,
    preferred_conditions VARCHAR(100) NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME (6) NOT NULL,
    updated_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (chat_room_id),
    KEY idx_chat_rooms_master (job_master_id),
    KEY idx_chat_rooms_created_by (created_by),
    KEY idx_chat_rooms_job_master_status (job_master_id, status),
    CONSTRAINT fk_chat_rooms_master FOREIGN KEY (job_master_id) REFERENCES job_masters (job_master_id),
    CONSTRAINT fk_chat_rooms_created_by FOREIGN KEY (created_by) REFERENCES users (user_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 22. chat_room_members
CREATE TABLE chat_room_members (
    chat_room_member_id BIGINT AUTO_INCREMENT,
    chat_room_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    job_application_id BIGINT NOT NULL,
    role VARCHAR(20) NOT NULL,
    joined_at DATETIME (6) NOT NULL,
    kicked_at DATETIME (6) NULL,
    PRIMARY KEY (chat_room_member_id),
    KEY idx_chat_members_room (chat_room_id, kicked_at, joined_at DESC),
    KEY idx_chat_members_user (user_id, kicked_at, joined_at DESC),
    UNIQUE KEY uk_chat_members_application (job_application_id),
    CONSTRAINT fk_chat_members_room FOREIGN KEY (chat_room_id) REFERENCES chat_rooms (chat_room_id),
    CONSTRAINT fk_chat_members_user FOREIGN KEY (user_id) REFERENCES users (user_id),
    CONSTRAINT fk_chat_members_application FOREIGN KEY (job_application_id) REFERENCES job_applications (job_application_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 23. chat_messages
CREATE TABLE chat_messages (
    message_id BIGINT AUTO_INCREMENT,
    chat_room_id BIGINT NOT NULL,
    sender_id BIGINT NULL,
    file_id BIGINT NULL,
    message_type VARCHAR(20) NOT NULL,
    content VARCHAR(1000) NOT NULL,
    sent_at DATETIME (6) NOT NULL,
    deleted_at DATETIME (6) NULL,
    PRIMARY KEY (message_id),
    KEY idx_chat_messages_room_sent (chat_room_id, sent_at DESC),
    KEY idx_chat_messages_room_cursor (chat_room_id, message_id DESC),
    KEY idx_chat_messages_sender (sender_id),
    KEY idx_chat_messages_file (file_id),
    CONSTRAINT fk_chat_messages_room FOREIGN KEY (chat_room_id) REFERENCES chat_rooms (chat_room_id),
    CONSTRAINT fk_chat_messages_sender FOREIGN KEY (sender_id) REFERENCES users (user_id),
    CONSTRAINT fk_chat_messages_file FOREIGN KEY (file_id) REFERENCES file_objects (file_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- 24. notifications
CREATE TABLE notifications (
    notification_id BIGINT AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(25) NOT NULL,
    body VARCHAR(80) NOT NULL,
    type VARCHAR(30) NOT NULL,
    ref_type VARCHAR(30) NULL,
    ref_id BIGINT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME (6) NOT NULL,
    read_at DATETIME (6) NULL,
    PRIMARY KEY (notification_id),
    KEY idx_notifications_user_created (
        user_id,
        created_at DESC,
        notification_id,
        title,
        body,
        type,
        is_read
    ),
    KEY idx_notifications_user_read (user_id, is_read, notification_id),
    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users (user_id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;