from pydantic import BaseModel, Field


# 3.4 이력서 분석
class ResumeAnalyzeRequest(BaseModel):
    user_id: str = Field(..., description="분석할 사용자 ID")
    job_posting_id: str = Field(..., description="관련 채용 공고 ID")


class ResumeAnalyzeResponse(BaseModel):
    ai_analysis_report: str = Field(..., description="AI 이력서 종합 분석 결과")
    job_fit_score: str = Field(..., description="직무 적합도 평가")
    experience_clarity_score: str = Field(..., description="경력 및 성과 명확성 평가")
    readability_score: str = Field(..., description="이력서 가독성 및 신뢰도 평가")


# 3.5 포트폴리오 분석
class PortfolioAnalyzeRequest(BaseModel):
    user_id: str = Field(..., description="분석할 사용자 ID")
    job_posting_id: str = Field(..., description="관련 채용 공고 ID")


class PortfolioAnalyzeResponse(BaseModel):
    ai_analysis_report: str = Field(..., description="AI 포트폴리오 종합 분석 결과")
    problem_solving_score: str = Field(..., description="문제 해결 능력 평가")
    contribution_clarity_score: str = Field(..., description="기여도 및 역할 명확성 평가")
    technical_depth_score: str = Field(..., description="기술 깊이 및 실무성 평가")
