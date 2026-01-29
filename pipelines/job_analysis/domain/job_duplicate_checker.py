import logging
from typing import Optional, List
from job_analysis.data.repository.job_post_repository import JobPostRepository
from job_analysis.data.vector_repository.job_vector_repo import JobVectorRepository
from job_analysis.data.repository.job_posting_query_repository import JobPostingQueryRepository
from job_analysis.data.repository.skill_repository import SkillRepository
from job_analysis.data.repository.dto import JobPostingWithRelations
from job_analysis.utils.ai_agent import get_ai_agent

logger = logging.getLogger(__name__)

class JobDuplicateChecker:
    """
    채용 공고의 중복 여부를 판단하는 도메인 서비스입니다.
    URL, 본문 Fingerprint(Hash), 그리고 의미적 유사도(Vector)를 종합적으로 검사합니다.
    """

    def __init__(
        self, 
        job_post_repo: JobPostRepository,
        job_vector_repo: JobVectorRepository,
        query_repo: JobPostingQueryRepository,
        skill_repo: SkillRepository
    ):
        self.job_post_repo = job_post_repo
        self.job_vector_repo = job_vector_repo
        self.query_repo = query_repo
        self.skill_repo = skill_repo

    # --- Phase 1: 가벼운 사전 검사 (실행 시점: 크롤링 직후) ---

    async def check_existing_post_by_url(self, url: str) -> Optional[JobPostingWithRelations]:
        """URL 기반으로 이미 등록된 공고인지 확인 (Relations 포함)"""
        return await self.query_repo.find_with_relations_by_url(url)

    async def check_existing_post_by_fingerprint(self, fingerprint: str) -> Optional[JobPostingWithRelations]:
        """본문 해시(Fingerprint) 기반으로 중복 내용인지 확인 (Relations 포함)"""
        return await self.query_repo.find_with_relations_by_fingerprint(fingerprint)

    # --- Phase 2: 정밀한 의미 검사 (실행 시점: 데이터 추출 및 회사 식별 후) ---



    async def check_semantic_duplicate(
        self, 
        company_id: int, 
        job_text: str
    ) -> Optional[int]:
        """
        AI 추출 데이터(JSON 직렬화)와 Vector DB를 이용하여 의미적 중복(같은 회사, 같은 직무)을 판단.
        텍스트 유사도(Vector Score)만을 기준으로 판단합니다.
        """
        # 1. 신규 회사는 중복될 수 없음
        if not company_id:
            return None

        # 2. Vector DB 검색
        # job_text는 이미 JSON으로 직렬화된 전체 데이터임
        candidates = await self.job_vector_repo.search_similar_jobs(company_id, job_text)

        if not candidates:
            return None

        # 3. 상세 비교 (Text Similarity Only)
        # 가장 유사한 후보 하나만 비교
        top_match = candidates[0]
        similarity = top_match['similarity']
        
        logger.info(f"🔎 Sim Check [ID:{top_match['job_master_id']}]")
        logger.info(f"   -> Vector Similarity: {similarity:.4f}")

        # 4. 종합 점수 산출 (Vector Score 기준)
        if similarity >= 0.85:
            # 상: 확실한 중복 -> 기존 ID 반환
            logger.info("✅ High confidence match: Auto-linked.")
            return top_match['job_master_id']
        
        elif similarity >= 0.75:
            # 중: 애매함 -> AI Agent 확인
            logger.info("🤖 Medium confidence: Asking AI Agent...")

            # 1. 새 공고 내용 (job_text는 JSON 형태이므로 주요 내용만 추출하거나 그대로 사용)
            # 여기서는 편의상 job_text 전체를 사용
            new_content = job_text

            # 2. 기존 공고 내용 (Vector DB의 'content' 필드 활용)
            existing_content = top_match.get('content')
            if not existing_content:
                # content가 반환되지 않았다면(Vector Repo에서 return_properties에 추가되지 않았을 경우)
                # 별도로 조회하거나, 여기서는 '정보 부족'으로 판단하고 중복 아님 처리할 수 있음.
                logger.warning("⚠️ Existing content not found in vector result. Skipping AI check.")
                return None
            
            # AI Agent에게 내용만 전달하여 비교
            # is_same_job_posting의 인자를 (str, str) 형태로 가정하고 호출 (또는 dict)
            ai_agent = get_ai_agent()
            is_same = await ai_agent.is_same_job_posting(
                {"content_summary": new_content}, 
                {"content_summary": existing_content}
            )

            if is_same:
                logger.info("✅ AI Agent confirmed match.")
                return top_match['job_master_id']
            else:
                 logger.info("❌ AI Agent denied match.")
                 return None

        else:
            # 하: 중복 아님 -> None
            logger.info("🆕 Low confidence: Treating as new job.")
            return None
