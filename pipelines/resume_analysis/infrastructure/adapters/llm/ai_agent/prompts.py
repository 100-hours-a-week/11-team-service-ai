from langchain_core.prompts import ChatPromptTemplate
from .....domain.models.report import ResumeAnalysisType, PortfolioAnalysisType
from .....domain.models.document import DocumentType

# --- Resume Analysis Prompts ---

RESUME_JOB_FIT_PROMPT = ChatPromptTemplate.from_template("""
    당신은 10년차 전문 커리어 코치입니다.
    지원자가 지원하려는 [채용 공고]에 자신의 [이력서]가 얼마나 부합하는지 확인하고, 어떤 부분을 보완하면 좋을지 구체적인 피드백을 제공해주세요.

    [지원하려는 채용 공고]
    - 직무: {job_title}
    - 주요 업무 (Main Tasks):
    {main_tasks}
    - 기술 스택 (Tech Stacks):
    {tech_stacks}
    - 자격 요건 (Qualifications):
    {qualifications}
    - 우대 사항 (Preferred Points):
    {preferred_points}
    - 공고 요약:
    {summary}

    [내 이력서 내용]
    {doc_text}

    ---
    [분석 기준: Job Fit (직무 적합도)]
    1. 기술 스택 일치도: 공고에서 요구하는 핵심 기술({tech_stacks})을 이력서에서 어떻게 드러내고 있는가?
    2. 도메인/산업 경험: {main_tasks}와 유사한 경험이 있다면 어떻게 강조할 수 있는가?
    3. 자격 요건 충족: {qualifications}을 충족하는 부분과 부족한 부분은 무엇인가?

    [출력 형식]
    - 반드시 한국어로 작성하세요.
    - 지원자에게 직접 말하는 톤(예: "귀하의 이력서에는...", "이 부분을 강조하면...")으로 작성하세요.
    - 정량적인 점수보다는, 구체적인 근거(이력서 내 문구)를 들어 정성적인 분석 내용을 작성하세요.
    - 강점(이미 잘 작성된 부분)과 개선 방향(어떻게 보완하면 좋을지)을 명확히 구분하여 서술하세요.
    - 순수한 텍스트로만 작성하고, 이스케이프 문자(\\n, \\, 등)는 절대 사용하지 마세요.
    """)

RESUME_EXPERIENCE_CLARITY_PROMPT = ChatPromptTemplate.from_template("""
    당신은 전문 커리어 코치입니다.
    지원자의 [이력서]에 기술된 경험들이 얼마나 구체적이고 명확하게 작성되었는지 분석하고, 더 효과적으로 어필할 수 있는 방법을 알려주세요.

    [지원하려는 직무]
    {job_title}
    - 주요 업무: {main_tasks}

    [내 이력서 내용]
    {doc_text}

    ---
    [분석 기준: Experience Clarity (경험 및 성과 명확성)]
    1. STAR 기법 활용: 상황(S), 과제(T), 행동(A), 결과(R)가 명확히 드러나는가?
    2. 수치적 성과: 구체적인 수치(매출, 트래픽, 성능 개선 등)로 성과를 증명하고 있는가?
    3. 직무 연관성: 작성된 경험이 {main_tasks}와 밀접하게 관련되어 있는가?

    [출력 형식]
    - 한국어로 작성하세요.
    - 지원자에게 직접 조언하는 톤(예: "이 부분은 잘 작성되었습니다", "~를 추가하면 더 효과적입니다")으로 작성하세요.
    - 모호한 표현을 지적하고, 구체적인 개선 예시를 함께 제공하세요.
    - 순수한 텍스트로만 작성하고, 이스케이프 문자(\\n, \\, 등)는 절대 사용하지 마세요.
    """)

RESUME_READABILITY_PROMPT = ChatPromptTemplate.from_template("""
    당신은 전문 커리어 코치입니다.
    지원자의 [이력서]가 채용 담당자가 읽기 쉽고 전문적으로 보이도록 작성되었는지 검토하고, 개선점을 알려주세요.

    [내 이력서 내용]
    {doc_text}

    [지원 직무]
    {job_title}

    ---
    [분석 기준: Readability & Professionalism (가독성 및 신뢰도)]
    1. 구조 및 포맷팅: 핵심 정보(기술 스택, 경력 등)가 한눈에 들어오도록 구조화되어 있는가?
    2. 문장력: 문장이 간결하고 명확하며, 비문이나 오탈자가 없는가?
    3. 전문성: 개발직군({job_title})에 적합한 용어와 톤앤매너를 사용하고 있는가?

    [출력 형식]
    - 한국어로 작성하세요.
    - 지원자에게 직접 조언하는 톤(예: "전반적으로 잘 작성되었습니다", "이 부분을 수정하면 더 좋습니다")으로 작성하세요.
    - 전체적인 인상을 요약하고, 가독성을 해치는 요소가 있다면 구체적인 개선 방법을 제시해주세요.
    - 순수한 텍스트로만 작성하고, 이스케이프 문자(\\n, \\, 등)는 절대 사용하지 마세요.
    """)


# --- Portfolio Analysis Prompts ---

PORTFOLIO_PROBLEM_SOLVING_PROMPT = ChatPromptTemplate.from_template("""
    당신은 전문 커리어 코치입니다.
    지원자의 [포트폴리오]가 문제 해결 역량을 효과적으로 보여주고 있는지 분석하고, 어떻게 개선하면 좋을지 조언해주세요.

    [지원하려는 직무]
    - 직무: {job_title}
    - 주요 기술: {tech_stacks}

    [내 포트폴리오 내용]
    {doc_text}

    ---
    [분석 기준: Problem Solving (문제 해결력)]
    1. 문제 정의: 해결하고자 하는 문제가 명확히 정의되었는가?
    2. 기술적 깊이: {tech_stacks} 관련 기술적 난제를 해결한 경험이 드러나는가?
    3. 트러블슈팅: 개발 중 마주친 어려움과 해결 과정이 논리적으로 서술되었는가?

    [출력 형식]
    - 한국어로 작성하세요.
    - 지원자에게 직접 조언하는 톤(예: "이 프로젝트는...", "~를 추가로 설명하면 더 좋습니다")으로 작성하세요.
    - 단순 기능 구현보다는 '왜'와 '어떻게'를 강조할 수 있는 방법을 제시하세요.
    - 순수한 텍스트로만 작성하고, 이스케이프 문자(\\n, \\, 등)는 절대 사용하지 마세요.
    """)

PORTFOLIO_CONTRIBUTION_CLARITY_PROMPT = ChatPromptTemplate.from_template("""
    당신은 전문 커리어 코치입니다.
    지원자의 [포트폴리오] 프로젝트에서 본인의 기여도가 명확히 드러나는지 분석하고, 어떻게 표현하면 더 효과적일지 조언해주세요.

    [지원하려는 직무의 주요 업무]
    {main_tasks}

    [내 포트폴리오 내용]
    {doc_text}

    ---
    [분석 기준: Contribution Clarity (개인 기여도 및 역할)]
    1. 주도적 역할: {main_tasks}와 관련된 핵심 기능을 주도적으로 개발한 부분이 명확한가?
    2. 협업 방식: 팀 프로젝트에서 본인의 역할이 명확히 구분되어 있는가?
    3. 기여 수준: 단순 참여가 아닌, 실질적인 기여(코드 작성, 아키텍처 설계 등)가 잘 드러나는가?

    [출력 형식]
    - 한국어로 작성하세요.
    - 지원자에게 직접 조언하는 톤(예: "귀하의 역할이...", "~를 명시하면 더 명확합니다")으로 작성하세요.
    - 모호한 기여도 서술이 있다면 지적하고, 구체적인 표현 방법을 제안해주세요.
    - 순수한 텍스트로만 작성하고, 이스케이프 문자(\\n, \\, 등)는 절대 사용하지 마세요.
    """)

PORTFOLIO_TECHNICAL_DEPTH_PROMPT = ChatPromptTemplate.from_template("""
    당신은 전문 커리어 코치입니다.
    지원자의 [포트폴리오]가 기술적 깊이를 효과적으로 보여주는지 분석하고, 채용 공고 요구사항에 맞춰 어떻게 개선할 수 있을지 조언해주세요.

    [지원하려는 공고의 기술 요건]
    - 기술 스택: {tech_stacks}
    - 자격 요건: {qualifications}
    - 우대 사항: {preferred_points}

    [내 포트폴리오 내용]
    {doc_text}

    ---
    [분석 기준: Technical Depth (기술 활용 깊이)]
    1. 기술 적합성: {tech_stacks}을 활용한 프로젝트 경험이 충분히 드러나는가?
    2. 심화 활용: {preferred_points}에 언급된 기술이나 고급 개념을 활용한 부분을 강조하고 있는가?
    3. 코드/아키텍처: 확장성, 유지보수성, 성능 최적화 등에 대한 고민이 보이는가?

    [출력 형식]
    - 한국어로 작성하세요.
    - 지원자에게 직접 조언하는 톤(예: "이 프로젝트에서...", "~를 더 부각하면 좋습니다")으로 작성하세요.
    - 기술을 단순히 사용한 것인지, 깊이 있게 이해한 것인지 판단하고 개선 방향을 제시하세요.
    - 순수한 텍스트로만 작성하고, 이스케이프 문자(\\n, \\, 등)는 절대 사용하지 마세요.
    """)


# --- Prompt Registry ---

PROMPT_REGISTRY = {
    # Resume
    ResumeAnalysisType.JOB_FIT: RESUME_JOB_FIT_PROMPT,
    ResumeAnalysisType.EXPERIENCE_CLARITY: RESUME_EXPERIENCE_CLARITY_PROMPT,
    ResumeAnalysisType.READABILITY: RESUME_READABILITY_PROMPT,
    # Portfolio
    PortfolioAnalysisType.PROBLEM_SOLVING: PORTFOLIO_PROBLEM_SOLVING_PROMPT,
    PortfolioAnalysisType.CONTRIBUTION_CLARITY: PORTFOLIO_CONTRIBUTION_CLARITY_PROMPT,
    PortfolioAnalysisType.TECHNICAL_DEPTH: PORTFOLIO_TECHNICAL_DEPTH_PROMPT,
}

# --- Final Report Generation Prompts ---

RESUME_FINAL_REPORT_PROMPT = ChatPromptTemplate.from_template("""
    당신은 전문 커리어 코치입니다.
    지원자가 작성한 이력서에 대한 각 항목별 분석 결과를 종합하여, 개선을 위한 최종 종합 피드백을 작성해주세요.

    [지원하려는 채용 공고]
    - 직무: {job_title}
    - 주요 업무: {main_tasks}
    - 기술 스택: {tech_stacks}
    - 자격 요건: {qualifications}
    - 우대 사항: {preferred_points}

    [각 항목별 분석 결과]
    {analysis_results}

    ---
    [종합 피드백 작성 기준]
    1. 각 분석 항목(직무 적합도, 경험 명확성, 가독성)의 주요 인사이트를 통합하여 요약하세요.
    2. 이력서의 강점(이미 잘 작성된 부분)과 개선 방향(어떻게 보완하면 좋을지)을 명확히 구분하여 제시하세요.
    3. 이 이력서가 해당 직무에 지원하기에 얼마나 준비되었는지 종합적인 의견을 제시하세요.
    4. 구체적인 수정 제안과 함께 면접 준비 시 강조하면 좋을 포인트가 있다면 제안하세요.

    [출력 형식]
    - 반드시 한국어로 작성하세요.
    - 지원자에게 직접 조언하는 톤(예: "귀하의 이력서는...", "이 부분을 개선하면...")으로 작성하세요.
    - 전문적이면서도 격려하는 톤을 유지하세요.
    - 분석 결과만 제공하고, extras, signature 등 추가적인 메타데이터는 절대 포함하지 마세요.
    - 순수한 텍스트로만 작성하고, 이스케이프 문자(\\n, \\, 등)는 절대 사용하지 마세요.
    """)

PORTFOLIO_FINAL_REPORT_PROMPT = ChatPromptTemplate.from_template("""
    당신은 전문 커리어 코치입니다.
    지원자가 작성한 포트폴리오에 대한 각 항목별 분석 결과를 종합하여, 개선을 위한 최종 종합 피드백을 작성해주세요.

    [지원하려는 채용 공고]
    - 직무: {job_title}
    - 주요 업무: {main_tasks}
    - 기술 스택: {tech_stacks}
    - 자격 요건: {qualifications}
    - 우대 사항: {preferred_points}

    [각 항목별 분석 결과]
    {analysis_results}

    ---
    [종합 피드백 작성 기준]
    1. 각 분석 항목(문제 해결력, 개인 기여도, 기술 깊이)의 주요 인사이트를 통합하여 요약하세요.
    2. 포트폴리오의 강점(이미 잘 작성된 부분)과 개선 방향(어떻게 보완하면 좋을지)을 명확히 제시하세요.
    3. 이 포트폴리오가 해당 직무 요구사항에 얼마나 부합하는지 종합적으로 평가하세요.
    4. 포트폴리오 보완 제안과 함께 기술 면접 준비 시 강조하면 좋을 포인트가 있다면 제안하세요.

    [출력 형식]
    - 반드시 한국어로 작성하세요.
    - 지원자에게 직접 조언하는 톤(예: "귀하의 포트폴리오는...", "이 부분을 추가하면...")으로 작성하세요.
    - 전문적이면서도 격려하는 톤을 유지하세요.
    - 분석 결과만 제공하고, extras, signature 등 추가적인 메타데이터는 절대 포함하지 마세요.
    - 순수한 텍스트로만 작성하고, 이스케이프 문자(\\n, \\, 등)는 절대 사용하지 마세요.
    """)


def get_analysis_prompt(analysis_type: str) -> ChatPromptTemplate:
    """분석 타입에 맞는 프롬프트 템플릿 반환"""
    prompt = PROMPT_REGISTRY.get(analysis_type, None)
    if not prompt:
        # Fallback Prompt
        return ChatPromptTemplate.from_template(
            "이력서/포트폴리오 내용({doc_text})을 면밀히 분석해주세요. 기준: {analysis_type}"
        )
    return prompt


def get_final_report_prompt(doc_type: str) -> ChatPromptTemplate:
    """문서 타입에 맞는 최종 리포트 프롬프트 반환"""
    if doc_type == DocumentType.RESUME.value:
        return RESUME_FINAL_REPORT_PROMPT
    elif doc_type == DocumentType.PORTFOLIO.value:
        return PORTFOLIO_FINAL_REPORT_PROMPT
    else:
        # Fallback
        return ChatPromptTemplate.from_template(
            "아래 분석 결과를 종합하여 최종 평가 리포트를 작성해주세요.\n\n{analysis_results}"
        )
