from typing import Protocol, Optional
from ..models.job_data import ExtractedJobData


class JobDataExtractor(Protocol):
    """데이터 추출기 인터페이스 (LLM)"""

    async def extract(self, raw_text: str) -> Optional[ExtractedJobData]:
        """텍스트에서 구조화된 채용 공고 데이터를 추출합니다."""
        ...
