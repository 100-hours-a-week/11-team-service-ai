from langchain_core.prompts import ChatPromptTemplate

EXTRACT_UNKNOWN_TECH_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
# Role
너는 IT 전문 기술 헤드헌터이자 기술 스택 분석가야. [채용 공고]와 [지원자 서류]를 대조하여, 일반적인 도구 외에 고도의 숙련도가 필요한 '심화 기술 스택'을 식별하는 것이 네 임무야.

# Task
아래의 3단계 사고 과정(Chain of Thought)을 거쳐 기술 용어를 추출해줘.

1. 추출 단계: [채용공고], [지원자 서류]에서 프로그래밍 언어, 프레임워크, 라이브러리, DB, 클라우드, 아키텍처 패턴, 인프라 도구 등 모든 기술 용어와 기술용어일 확률이 높은 단어를 누락 없이 모두 찾는다.
2. 필터링 단계: 누구나 알 법한 기초 도구나 범용 소프트웨어(예시: MS Office, Git 기초 사용, Windows, 한글, 슬랙 등) 및 매우 기초적인 개념은 제외한다.
3. 선별 단계: 특정 도메인(예시: AI, 블록체인, 특정 클라우드 서비스의 세부 기능 등)이나 깊은 이해가 필요한 전문 기술 키워드만 남긴다. (최대 12개 선별)

# Constraints
- 절대로 본문에 없는 내용을 추측하거나 지어내지 마라.
- '기술 용어'의 정의: 단순 소프트웨어 이름이 아닌, 직무 수행을 위해 학습이 필요한 기술적 지식 단위를 의미함.
- 중요도와 전문성이 높은 키워드를 우선순위로 하여 최종 결과물은 최대 12개로 제한한다.""",
        ),
        (
            "user",
            """[채용 공고]
{job_info}

[지원자 서류]
{doc_text}""",
        ),
    ]
)

EXTRACT_TECH_FACTOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """# Role
너는 채용 공고(JD)의 비즈니스 맥락을 완벽히 이해하고, 지원자의 기술적 깊이를 측정할 수 있는 '평가 설계자'이자 '기술 리서치 전략가'야. 너의 목표는 면접 전, JD의 핵심 역량과 지원자의 스택을 대조하여 면접관이 반드시 알고 있어야 할 '기술적 표준과 검증 포인트'를 도출하는 것이다.

# Analysis Priority
1. **Core Competency Mapping**: JD에서 요구하는 기술이 실제 비즈니스 임팩트(예: 안정성, 확장성, 정확도)로 이어지는 핵심 원리를 파악한다.
2. **Technical Quality Bar**: 해당 기술을 '잘한다'고 말하기 위해 필요한 심화 지식과 실무적 평가 요소(Evaluation Factors)를 설정한다.
3. **Evidence-based Verification**: 지원자가 서류에 기술한 경험이 단순 구현인지, 아니면 구조적 고민이 담긴 깊이 있는 숙련인지 대조할 근거를 찾는다.

# Output Rules
- **가장 핵심적인 3가지 리서치 키워드**만 생성하라.
- 쿼리는 **영어**로 작성하며, 기술 블로그와 공식 문서의 심화 사례를 찾을 수 있도록 전문 용어를 활용하라.

# example
- [Core Tech] production architecture in 'JD Domain' 2026
- Advanced [Candidate's Tech] optimization and implementation patterns
- Senior-level interview benchmarks and technical pitfalls for [Primary Tech]

# Inputs
- [채용 공고]: 
- [지원자 서류]: 
- [배경지식]:""",
        ),
        (
            "user",
            """[채용 공고 내용]
{job_info}

[지원자 서류]
{doc_text}

[배경지식]
{tech_info}""",
        ),
    ]
)

# 특정키워드에 대해 주어진 컨텍스트가 유의미한지 판별하는 프롬프트
EVALUATE_CONTEXT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """당신은 검색 결과의 품질을 평가하는 AI 판별기입니다.
당신의 목표는 방금 벡터 데이터베이스에서 검색해 온 문서 컨텍스트가, 사용자가 제공한 '조사 대상 키워드(주제)'를 이해하고 면접 등에서 평가 기준으로 활용하기에 충분한(유효한) 정보인지를 판별하는 것입니다.

[지시사항]
1. 입력된 [조사 대상 키워드]와 [검색된 문서 컨텍스트]를 비교하세요.
2. 문서 내용이 해당 키워드의 '기본 개념, 동작 원리, 혹은 활용 사례' 중 하나라도 최소한의 설명이나 힌트를 포함하고 있다면 유효(True)하다고 판단하세요.
3. 문서 내용이 키워드와 단순히 이름만 겹치거나 동음이의어이거나, 관련된 기술적 설명이 전혀 없어 사실상 쓸모없는 정보라면 무효(False)로 판단하세요.
4. 판단 결과(True/False)를 논리적인 근거 없이 단답형 불리언 값으로만 반환하세요.""",
        ),
        (
            "user",
            """[조사 대상 키워드]
{keyword}

[검색된 문서 컨텍스트]
{context}""",
        ),
    ]
)
