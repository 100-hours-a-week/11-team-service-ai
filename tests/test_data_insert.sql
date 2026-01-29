-- ==========================================
-- 통합 테스트용 데이터 삽입 쿼리 (test_data.sql)
-- 기존 테스트 데이터를 초기화하고 다시 삽입합니다.
-- ==========================================
-- 외래키 체크 해제 (삭제 및 순서 문제 방지)
SET
    FOREIGN_KEY_CHECKS = 0;

-- 0. 초기화 (기존 테스트 데이터 삭제)
DELETE FROM application_document_parsed;

DELETE FROM application_documents
WHERE
    application_document_id IN (9901, 9902);

DELETE FROM file_objects
WHERE
    file_id IN (9901, 9902);

DELETE FROM job_applications
WHERE
    job_application_id = 9901;

DELETE FROM job_master_skills
WHERE
    job_master_id = 9901;

DELETE FROM job_masters
WHERE
    job_master_id = 9901;

DELETE FROM skills
WHERE
    skill_id IN (9901, 9902, 9903, 9904);

DELETE FROM companies
WHERE
    company_id = 991;

DELETE FROM users
WHERE
    user_id = 991;

-- 외래키 체크 복구
SET
    FOREIGN_KEY_CHECKS = 1;

-- ==========================================
-- 데이터 삽입 (반드시 순서대로 실행하세요)
-- ==========================================
-- 1. 사용자 생성 (users)
INSERT INTO
    users (
        user_id,
        role,
        nickname,
        status,
        created_at,
        updated_at
    )
VALUES
    (
        991,
        'APPLICANT',
        'Backend_Applicant_991',
        'ACTIVE',
        NOW (),
        NOW ()
    );

-- 2. 회사 생성 (companies)
INSERT INTO
    companies (company_id, name, created_at, updated_at)
VALUES
    (991, 'TechCorp Inc.', NOW (), NOW ());

-- 3. 스킬 데이터 생성 (skills)
INSERT INTO
    skills (
        skill_id,
        skill_name,
        category,
        created_at,
        updated_at
    )
VALUES
    (9901, 'Java', 'Language', NOW (), NOW ()),
    (9902, 'Spring Boot', 'Framework', NOW (), NOW ()),
    (9903, 'MySQL', 'Database', NOW (), NOW ()),
    (9904, 'Docker', 'Infrastructure', NOW (), NOW ());

-- 4. 채용 공고 마스터 생성 (job_masters)
INSERT INTO
    job_masters (
        job_master_id,
        company_id,
        job_title,
        status,
        main_tasks,
        ai_summary,
        evaluation_criteria,
        created_at,
        updated_at
    )
VALUES
    (
        9901,
        991,
        'Senior Backend Engineer',
        'OPEN',
        '["RESTful API 설계 및 구현", "대용량 트래픽 처리를 위한 DB 쿼리 최적화", "AWS 인프라 아키텍처 설계 및 운영"]',
        'Java, Spring Boot 및 AWS 활용 능력에 능숙한 시니어 백엔드 엔지니어를 찾습니다. 대규모 트래픽 처리 경험과 마이크로서비스 아키텍처 설계 역량을 중요하게 평가합니다.',
        '[{"name": "직무 적합성", "description": "Java/Spring 기반의 백엔드 개발 경험 및 아키텍처 이해도"}, {"name": "문제 해결 능력", "description": "복잡한 기술적 문제를 분석하고 효율적인 솔루션을 도출하는 능력"}, {"name": "성장 가능성", "description": "새로운 기술에 대한 학습 의지와 지속적인 자기 개발 태도"}, {"name": "조직 융화력", "description": "팀원과의 원활한 소통 및 협업 능력"}]',
        NOW (),
        NOW ()
    );

-- 5. 공고-스킬 연결 (job_master_skills)
INSERT INTO
    job_master_skills (job_master_id, skill_id, created_at)
VALUES
    (9901, 9901, NOW ()), -- Java
    (9901, 9902, NOW ()), -- Spring Boot
    (9901, 9903, NOW ()), -- MySQL
    (9901, 9904, NOW ());

-- Docker
-- 6. 지원 내역 생성 (job_applications)
INSERT INTO
    job_applications (
        job_application_id,
        user_id,
        job_master_id,
        status,
        created_at,
        updated_at
    )
VALUES
    (9901, 991, 9901, 'APPLIED', NOW (), NOW ());

-- 7. 파일 오브젝트 생성 (Resume - ID: 9901)
-- 주의: 사용자가 지정한 S3 Path 반영
INSERT INTO
    file_objects (
        file_id,
        storage_provider,
        object_key,
        original_name,
        size_bytes,
        created_at
    )
VALUES
    (
        9901,
        'S3',
        'test_uploads/Portfolio.pdf',
        'Backend_Resume.pdf',
        1024,
        NOW ()
    );

-- 8. 지원 문서 연결 (Resume)
INSERT INTO
    application_documents (
        application_document_id,
        job_application_id,
        file_id,
        doc_type,
        created_at,
        updated_at
    )
VALUES
    (9901, 9901, 9901, 'RESUME', NOW (), NOW ());

-- ---------------------------------------------------------
-- 9. 파일 오브젝트 생성 (Portfolio - ID: 9902)
-- 주의: 사용자가 지정한 S3 Path 반영
INSERT INTO
    file_objects (
        file_id,
        storage_provider,
        object_key,
        original_name,
        size_bytes,
        created_at
    )
VALUES
    (
        9902,
        'S3',
        'test_uploads/Resum.pdf',
        'Backend_Portfolio.pdf',
        2048,
        NOW ()
    );

-- 10. 지원 문서 연결 (Portfolio)
INSERT INTO
    application_documents (
        application_document_id,
        job_application_id,
        file_id,
        doc_type,
        created_at,
        updated_at
    )
VALUES
    (9902, 9901, 9902, 'PORTFOLIO', NOW (), NOW ());