from langchain_core.prompts import ChatPromptTemplate

# --- Candidate Comparison Analysis Prompts ---

CANDIDATE_COMPARISON_PROMPT = ChatPromptTemplate.from_template("""
    당신은 채용 전문가입니다.
    두 명의 지원자를 비교 분석하여, 강점과 약점을 파악해주세요.

    [채용 공고 정보]
    - 직무: {job_title}
    - 주요 업무: {main_tasks}
    - 기술 스택: {tech_stacks}

    [내 지원자 정보]
    {my_candidate_info}

    [경쟁 지원자 정보]
    {competitor_info}

    ---
    [분석 기준]
    1. 기술 역량 비교
    2. 경험 및 프로젝트 비교
    3. 직무 적합도 비교

    [출력 형식]
    - 반드시 한국어로 작성하세요.
    - 강점과 약점을 명확히 구분하여 작성하세요.
    - 구체적인 근거를 제시하세요.
    """)

STRENGTHS_REPORT_PROMPT = ChatPromptTemplate.from_template("""
    두 지원자를 비교하여 내 지원자의 강점을 작성해주세요.

    [내 지원자 정보]
    {my_candidate_info}

    [경쟁 지원자 정보]
    {competitor_info}

    [출력 형식]
    - 한국어로 작성하세요.
    - 구체적인 강점을 나열하세요.
    """)


def get_analysis_prompt() -> ChatPromptTemplate:
    """지원자 비교 분석 프롬프트 반환"""
    return CANDIDATE_COMPARISON_PROMPT


def get_final_report_prompt() -> ChatPromptTemplate:
    """최종 리포트 프롬프트 반환"""
    return STRENGTHS_REPORT_PROMPT
