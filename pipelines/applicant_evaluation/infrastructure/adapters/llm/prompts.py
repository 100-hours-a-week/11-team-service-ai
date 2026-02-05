from langchain_core.prompts import ChatPromptTemplate


def get_competency_evaluation_prompt() -> ChatPromptTemplate:
    """
    개별 역량 평가를 위한 프롬프트 템플릿 반환

    Required Variables:
    - company_name, main_tasks, tech_stacks (JobInfo)
    - criteria_name, criteria_desc (EvaluationCriteria)
    - resume_text, portfolio_text (Documents)
    """
    system_prompt = """
    당신은 전문적인 채용 담당관입니다. 
    지원자가 '{company_name}' 회사의 다음 직무에 지원했습니다.

    [직무 정보]
    - 주요 업무: {main_tasks}
    - 기술 스택: {tech_stacks}

    당신의 임무는 지원자의 서류(이력서, 포트폴리오)를 분석하여 
    다음 평가 기준: '{criteria_name}' ({criteria_desc})
    에 대해 0~100점 사이의 점수를 매기고 구체적인 근거를 서술하는 것입니다.

    [평가 지침]
    1. 점수는 반드시 근거에 기반하여 냉정하게 산출하세요. 관대하게 평가하지 마세요.
    2. 서류에 해당 역량에 대한 증거가 전혀 없다면 0~20점을 부여하세요.
    3. 점수 기준:
       - 0~20: 역량 증거 부족 또는 부적합
       - 21~40: 기초적인 이해는 있으나 실무 적용 경험 부족
       - 41~60: 일반적인 수준의 역량 (평범함)
       - 61~80: 실무에 즉시 투입 가능한 우수한 역량
       - 81~100: 해당 분야의 전문가 수준 또는 탁월한 성과 보유

    반드시 아래와 같은 JSON 형식으로만 응답해주세요 (MarkDown Code Block 없이, 스키마 정의 없이, 순수 JSON 데이터만):
    {{
        "name": "{criteria_name}",
        "score": 85.0, 
        "description": "평가 근거 및 상세 사유..."
    }}
    """

    user_prompt = """
    [이력서 내용]
    {resume_text}

    [포트폴리오 내용]
    {portfolio_text}
    """

    return ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", user_prompt)]
    )


def get_report_synthesis_prompt() -> ChatPromptTemplate:
    """
    종합 리포트 생성을 위한 프롬프트 템플릿 반환

    Required Variables:
    - company_name
    - job_summary
    - results_summary (Evaluated Competency Results)
    """
    system_prompt = """
    당신은 채용 결정권자입니다. 
    '{company_name}' 회사의 채용 공고에 대한 지원자 평가 결과가 다음과 같이 취합되었습니다.

    [직무 요약]
    {job_summary}

    [평가 결과 요약]
    {results_summary}

    위 정보를 바탕으로 채용 담당자 관점에서 다음 두 가지를 작성해주세요.
    단, 평가는 사실에 기반하여 매우 객관적이고 비판적으로 수행해야 하며, 막연한 칭찬은 지양하세요.

    1. 한 줄 평가 (one_line_review): 지원자의 핵심 역량과 회사 적합도를 한 문장으로 요약
    2. 상세 피드백 (feedback_detail): 직무 기술서(JD)와 지원자 역량을 비교하여, 강점과 보완점을 구체적으로 서술

    반드시 아래와 같은 JSON 형식으로만 응답해주세요 (MarkDown Code Block 없이, 스키마 정의 없이, 순수 JSON 데이터만):
    {{
        "one_line_review": "지원자의 한 줄 평가...",
        "feedback_detail": "상세 피드백 내용..."
    }}
    """

    user_prompt = "종합적인 채용 리포트를 작성해주세요."

    return ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", user_prompt)]
    )
