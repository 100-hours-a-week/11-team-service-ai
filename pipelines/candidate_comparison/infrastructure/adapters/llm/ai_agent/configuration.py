from dataclasses import dataclass
from typing import Optional
from langchain_core.runnables import RunnableConfig
from .....domain.models.job import JobInfo
from .....domain.models.candidate import Candidate


# 1. 고정된 입력값 (Runtime Context) - 데이터 클래스 권장
@dataclass
class CandidateContext:
    job_info: JobInfo  # 공고 내용
    my_candidate : Candidate
    competitor_candidate : Candidate



# 2. 실행 설정 (Configuration)
@dataclass(frozen=True)
class Configuration:
    """에이전트 실행 설정을 관리합니다."""

    model_name: str = "gpt-4o"
    model_provider: str = "openai"

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """config의 configurable 필드에서 데이터를 안전하게 추출합니다."""
        configurable = (config or {}).get("configurable", {})

        # 클래스의 필드 목록을 기반으로 안전하게 추출
        return cls(
            model_name=configurable.get("model_name", "gpt-4o"),
            model_provider=configurable.get("model_provider", "openai"),
        )
