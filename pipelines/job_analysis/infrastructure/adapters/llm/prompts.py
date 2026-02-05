from langchain_core.prompts import ChatPromptTemplate


def get_job_extraction_prompt() -> ChatPromptTemplate:
    """
    채용 공고 데이터 추출을 위한 프롬프트 템플릿 반환

    Required Variables:
    - raw_text: 채용 공고 원본 텍스트
    """
    system_prompt = """
    당신은 채용 공고 분석 전문가입니다. 주어진 채용 공고 텍스트에서 핵심 정보를 추출하여 JSON 형식으로 출력하세요.

    추출해야 할 정보:
    1. company_name: 회사명 (텍스트에 없으면 'Unknown')
    2. job_title: 공고 제목 또는 직무명
    3. main_tasks: 주요 업무 (리스트)
    4. tech_stacks: 기술 스택 (리스트, 예: Python, AWS, React)
    5. start_date: 공고 시작일 (YYYY-MM-DD, 없으면 null)
    6. end_date: 공고 마감일 (YYYY-MM-DD, 상시채용은 null)
    7. ai_summary: 공고 전체 내용과 우선시되는 핵심 역량을 포함하여 3~5줄로 요약
    8. evaluation_criteria: 다음 4가지 기준에 맞추어 평가 기준 추출 (리스트)
       - 직무 적합성
       - 문화 적합성
       - 성장 가능성
       - 문제 해결 능력
       각 항목은 {{"name": "기준명", "description": "상세 설명"}} 형태여야 함.

    반드시 아래와 같은 JSON 형식으로만 응답해주세요 (MarkDown Code Block 없이, 스키마 정의 없이, 순수 JSON 데이터만):
    {{
        "company_name": "회사명",
        "job_title": "직무명",
        "main_tasks": ["업무1", "업무2"],
        "tech_stacks": ["기술1", "기술2"],
        "start_date": "2024-01-01",
        "end_date": null,
        "ai_summary": "요약 내용...",
        "evaluation_criteria": [
            {{"name": "직무 적합성", "description": "..."}},
            {{"name": "문화 적합성", "description": "..."}}
        ]
    }}
    """

    user_prompt = "{raw_text}"

    return ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", user_prompt)]
    )
