SET
    FOREIGN_KEY_CHECKS = 0;

DELETE FROM ai_applicant_evaluation
WHERE
    evaluation_id IN (9901, 9902);

DELETE FROM application_document_parsed
WHERE
    application_document_id IN (9901, 9902, 9903, 9904);

DELETE FROM application_documents
WHERE
    application_document_id IN (9901, 9902, 9903, 9904);

DELETE FROM file_objects
WHERE
    file_id IN (9901, 9902, 9903, 9904);

DELETE FROM job_applications
WHERE
    job_application_id IN (9901, 9902);

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
    user_id IN (991, 992);

SET
    FOREIGN_KEY_CHECKS = 1;

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
    (991, 'USER', '황파이', 'ACTIVE', NOW (), NOW ());

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
    (992, 'USER', '김자바', 'ACTIVE', NOW (), NOW ());

-- 2. 회사 생성 (companies)
INSERT INTO
    companies (company_id, name, created_at, updated_at)
VALUES
    (991, 'TestComapny Inc', NOW (), NOW ());

-- 3. 스킬 데이터 생성 (skills)
INSERT INTO
    skills (skill_id, skill_name, created_at, updated_at)
VALUES
    (9901, '[Java]', NOW (), NOW ()),
    (9902, '[Spring Boot]', NOW (), NOW ()),
    (9903, '[MySQL]', NOW (), NOW ()),
    (9904, '[Docker]', NOW (), NOW ());

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
    (9901, 991, 9901, 'ACTIVE', NOW (), NOW ());

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
    (9902, 992, 9901, 'ACTIVE', NOW (), NOW ());

-- 7. 파일 오브젝트 생성 (Resume)
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
        'test_uploads/Resum.pdf',
        'Backend_Resume.pdf',
        1024,
        NOW ()
    );

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
    (9902, 9902, 9902, 'RESUME', NOW (), NOW ());

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
        9903,
        'S3',
        'test_uploads/Portfolio.pdf',
        'Backend_Portfolio.pdf',
        2048,
        NOW ()
    );

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
        9904,
        'S3',
        'test_uploads/Portfolio.pdf',
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
    (9903, 9901, 9903, 'PORTFOLIO', NOW (), NOW ());

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
    (9904, 9902, 9904, 'PORTFOLIO', NOW (), NOW ());

-- ---------------------------------------------------------
-- 10. 평가 결과 생성
INSERT INTO
    ai_applicant_evaluation (
        evaluation_id,
        job_application_id,
        overall_score,
        one_line_review,
        feedback_detail,
        comparison_scores,
        created_at,
        updated_at
    )
VALUES
    (
        9901,
        9901,
        85,
        '직무에 대한 이해도가 높고 기본기가 탄탄한 지원자입니다.',
        '제출한 포트폴리오를 통해 실무에 바로 투입 가능한 수준의 능력을 보여주었습니다. 특히 문제 해결 능력이 돋보입니다.',
        '[
        {"name": "직무 적합성 (Job Fit)", "score": 85, "description": "지원자는 다양한 프로그래밍 언어와 개발 스택을 보유하고 있으며, 실무에 즉시 투입 가능한 수준입니다."},
        {"name": "문화 적합성 (Culture Fit)", "score": 90, "description": "팀 프로젝트 경험이 풍부하여 원활한 협업이 기대됩니다."},
        {"name": "성장 가능성 (Growth Potential)", "score": 85, "description": "새로운 기술 습득에 대한 열정이 높습니다."},
        {"name": "문제 해결 능력 (Problem Solving)", "score": 90, "description": "복잡한 알고리즘 문제를 주도적으로 해결한 경험이 돋보입니다."}
    ]',
        NOW (),
        NOW ()
    ),
    (
        9902,
        9902,
        72,
        '잠재력은 있으나, 실무 경험이 다소 부족합니다.',
        '이론적인 지식은 갖추고 있으나 프로젝트 경험이 상대적으로 부족합니다. 멘토링을 통해 성장할 여지가 있습니다.',
        '[
        {"name": "직무 적합성 (Job Fit)", "score": 70, "description": "기본적인 지식은 있으나 실무 경험이 다소 부족합니다."},
        {"name": "문화 적합성 (Culture Fit)", "score": 80, "description": "의사소통 능력이 무난하며, 팀에 잘 적응할 것으로 보입니다."},
        {"name": "성장 가능성 (Growth Potential)", "score": 75, "description": "학습 의지가 돋보이나 지속적인 멘토링이 필요합니다."},
        {"name": "문제 해결 능력 (Problem Solving)", "score": 70, "description": "문제 상황에 대한 분석 경험이 추가적으로 필요합니다."}
    ]',
        NOW (),
        NOW ()
    );