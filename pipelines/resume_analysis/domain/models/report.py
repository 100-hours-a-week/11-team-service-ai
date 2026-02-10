from typing import List, Union
from pydantic import BaseModel, Field
from enum import Enum


# 임시 예외 클래스 정의 (또는 별도 예외 파일 import)
class AnalysisReportError(Exception):
    pass

class ResumeAnalysisType(str, Enum):
    """이력서 분석의 3대 핵심 영역"""
    JOB_FIT = "JOB_FIT"                         # 직무 적합도
    EXPERIENCE_CLARITY = "EXPERIENCE_CLARITY"   # 경험 및 성과 명확성
    READABILITY = "READABILITY"                 # 가독성 및 신뢰도

class PortfolioAnalysisType(str, Enum):
    """포트폴리오 분석의 3대 핵심 영역"""
    PROBLEM_SOLVING = "PROBLEM_SOLVING"         # 문제 해결력
    CONTRIBUTION_CLARITY = "CONTRIBUTION_CLARITY" # 개인 기여도 및 역할
    TECHNICAL_DEPTH = "TECHNICAL_DEPTH"         # 기술 활용 깊이 및 실무성


class SectionAnalysis(BaseModel):
    """개별 영역(직무, 경험, 가독성 등)에 대한 심층 분석 결과"""
    
    # 두 타입 모두 포괄하기 위해 Union 사용 또는 str로 완화 후 validation 검사
    type: Union[ResumeAnalysisType, PortfolioAnalysisType] = Field(description="분석 영역")
    
    # 분석 결과
    analyse_result: str = Field(description="해당 영역에 대한 종합 진단 요약")

class AnalysisReport(BaseModel):
    """
    최종 분석 리포트 (Aggregate Root)
    """

    section_analyses: List[SectionAnalysis] = Field(
        description="상세 분석 결과 리스트 (이력서 또는 포트폴리오)"
    )
    overall_review: str = Field(description="종합 분석 결과")

    @classmethod
    def create(
        cls,
        results: List[SectionAnalysis],
        overall_review: str,
    ) -> "AnalysisReport":
        """
        팩토리 메서드: 도메인 규칙(검증)을 통과한 유효한 리포트 객체만 생성
        """
        if not results:
             raise AnalysisReportError("분석 결과가 비어있습니다.")

        # 1. 정합성 검증 (필수 영역 포함 여부 판단 -> 타입 추론)
        cls._validate_completeness(results)

        # 2. 필수 데이터 검증
        if not overall_review:
            raise AnalysisReportError("종합 분석 데이터(overall_review)가 누락되었습니다.")

        # 3. 객체 생성
        return cls(
            section_analyses=results,
            overall_review=overall_review,
        )

    @staticmethod
    def _validate_completeness(results: List[SectionAnalysis]):
        """
        필수 분석 영역이 모두 포함되었는지 검사 (Resume/Portfolio 자동 판별)
        """
        # 결과에 포함된 타입들을 집합으로 추출
        present_types = {r.type for r in results}
        
        # Resume 타입 검사
        resume_required = {
            ResumeAnalysisType.JOB_FIT,
            ResumeAnalysisType.EXPERIENCE_CLARITY,
            ResumeAnalysisType.READABILITY,
        }
        
        # Portfolio 타입 검사
        portfolio_required = {
            PortfolioAnalysisType.PROBLEM_SOLVING,
            PortfolioAnalysisType.CONTRIBUTION_CLARITY,
            PortfolioAnalysisType.TECHNICAL_DEPTH,
        }
        
        is_resume = resume_required.issubset(present_types)
        is_portfolio = portfolio_required.issubset(present_types)
        
        if not (is_resume or is_portfolio):
            # 두 필수 조건 중 어느 것도 만족하지 못하면 에러
            raise AnalysisReportError(
                f"필수 분석 영역이 누락되었습니다. (현재 포함: {present_types})"
            )


