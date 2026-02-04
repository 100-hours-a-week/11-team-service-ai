"""AI Agent utilities for decision making in normalization and duplicate detection"""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from shared.config import settings

logger = logging.getLogger(__name__)


class AIAgent:
    """AI Agent for making intelligent decisions using LLM"""

    def __init__(self):
        if not settings.use_mock:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=(
                    SecretStr(settings.OPENAI_API_KEY)
                    if settings.OPENAI_API_KEY
                    else None
                ),
            )

    async def is_same_company(self, raw_name: str, normalized_name: str) -> bool:
        # Mock 모드: OpenAI 호출 없이 간단한 문자열 비교
        if settings.use_mock:
            is_same = raw_name.lower().replace(
                " ", ""
            ) == normalized_name.lower().replace(" ", "")
            logger.info(
                f"[Mock] is_same_company: '{raw_name}' vs '{normalized_name}' → {is_same}"
            )
            return is_same
        """
        두 회사명이 같은 회사를 가리키는지 LLM으로 판단합니다.

        Args:
            raw_name: 원본 회사명
            normalized_name: 정규화된 회사명 (후보)

        Returns:
            True if same company, False otherwise
        """
        prompt = f"""다음 두 회사명이 같은 회사를 가리키는지 판단하세요.

회사명 A: {raw_name}
회사명 B: {normalized_name}

같은 회사라면 "YES", 다른 회사라면 "NO"로만 답변하세요.
약어, 영문/한글 표기 차이, 법인 형태 차이는 같은 회사로 간주합니다.

예시:
- "카카오" vs "Kakao" → YES
- "네이버" vs "NAVER" → YES
- "삼성전자" vs "삼성SDI" → NO

답변:"""

        try:
            response = await self.llm.ainvoke(prompt)
            answer = str(response.content).strip().upper()
            is_same = answer == "YES"

            logger.info(
                f"🤖 AI Agent decision: '{raw_name}' vs '{normalized_name}' → {answer}"
            )
            return is_same

        except Exception as e:
            logger.error(f"❌ AI Agent error: {e}. Defaulting to False (conservative)")
            return False

    async def is_same_skill(self, raw_name: str, normalized_name: str) -> bool:
        """
        두 스킬명이 같은 기술을 가리키는지 LLM으로 판단합니다.

        Args:
            raw_name: 원본 스킬명
            normalized_name: 정규화된 스킬명 (후보)

        Returns:
            True if same skill, False otherwise
        """
        # Mock 모드: OpenAI 호출 없이 간단한 문자열 비교
        if settings.use_mock:
            is_same = raw_name.lower().replace(
                " ", ""
            ) == normalized_name.lower().replace(" ", "")
            logger.info(
                f"[Mock] is_same_skill: '{raw_name}' vs '{normalized_name}' → {is_same}"
            )
            return is_same

        prompt = f"""다음 두 기술/스킬명이 같은 기술을 가리키는지 판단하세요.

스킬 A: {raw_name}
스킬 B: {normalized_name}

같은 기술이라면 "YES", 다른 기술이라면 "NO"로만 답변하세요.
약어, 대소문자 차이, 버전 차이는 같은 기술로 간주합니다.

예시:
- "JavaScript" vs "Javascript" → YES
- "React.js" vs "React" → YES
- "Python3" vs "Python" → YES
- "Vue" vs "React" → NO
- "Docker" vs "Kubernetes" → NO

답변:"""

        try:
            response = await self.llm.ainvoke(prompt)
            answer = str(response.content).strip().upper()
            is_same = answer == "YES"

            logger.info(
                f"🤖 AI Agent decision: '{raw_name}' vs '{normalized_name}' → {answer}"
            )
            return is_same

        except Exception as e:
            logger.error(f"❌ AI Agent error: {e}. Defaulting to False (conservative)")
            return False

    async def is_same_job_posting(self, new_data: dict, existing_data: dict) -> bool:
        """
        두 채용 공고가 같은 공고인지 LLM으로 판단합니다.

        Args:
            new_data: 신규 공고 데이터 (job_title, company 등)
            existing_data: 기존 공고 데이터 (job_title, company 등)

        Returns:
            True if same job posting, False otherwise
        """
        # Mock 모드: OpenAI 호출 없이 간단한 비교
        if settings.use_mock:
            is_same = (
                new_data.get("company", "").lower()
                == existing_data.get("company", "").lower()
                and new_data.get("job_title", "").lower()
                == existing_data.get("job_title", "").lower()
            )
            logger.info(f"[Mock] is_same_job_posting → {is_same}")
            return is_same

        prompt = f"""다음 두 채용 공고가 같은 공고인지 판단하세요.

[공고 A]
- 회사: {new_data.get('company', 'N/A')}
- 직무: {new_data.get('job_title', 'N/A')}
- 주요 업무: {new_data.get('main_tasks', 'N/A')}

[공고 B]
- 회사: {existing_data.get('company', 'N/A')}
- 직무: {existing_data.get('job_title', 'N/A')}
- 주요 업무: {existing_data.get('main_tasks', 'N/A')}

같은 채용 공고라면 "YES", 다른 채용 공고라면 "NO"로만 답변하세요.
같은 회사의 같은 포지션이지만 표현이 약간 다른 경우 같은 공고로 간주합니다.

답변:"""

        try:
            response = await self.llm.ainvoke(prompt)
            answer = str(response.content).strip().upper()
            is_same = answer == "YES"

            logger.info(f"🤖 AI Agent decision for job posting → {answer}")
            return is_same

        except Exception as e:
            logger.error(f"❌ AI Agent error: {e}. Defaulting to False (conservative)")
            return False


# Singleton instance
_agent_instance: Optional[AIAgent] = None


def get_ai_agent() -> AIAgent:
    """AI Agent 싱글톤 인스턴스를 반환합니다."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AIAgent()
    return _agent_instance
