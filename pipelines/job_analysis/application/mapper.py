from ..domain.models.job_data import ExtractedJobData
from datetime import datetime
from shared.schema.job_posting import (
    JobPostingAnalyzeResponse,
    RecruitmentPeriod,
    JobEvaluationCriteriaItem,
)


class JobDataMapper:
    """
    Job Analysis 도메인 모델을 외부 통신용 DTO(Schema)로 변환하는 매퍼
    Application Layer에 위치하여 도메인과 외부 스키마 간의 결합을 끊어줌.
    """

    @staticmethod
    def to_analyze_response(data: ExtractedJobData) -> JobPostingAnalyzeResponse:
        recruitment_period = None
        if data.start_date or data.end_date:
            start_d = (
                datetime.strptime(data.start_date, "%Y-%m-%d").date()
                if data.start_date
                else None
            )
            end_d = (
                datetime.strptime(data.end_date, "%Y-%m-%d").date()
                if data.end_date
                else None
            )
            recruitment_period = RecruitmentPeriod(start_date=start_d, end_date=end_d)

        return JobPostingAnalyzeResponse(
            job_posting_id=0,
            is_existing=False,
            company_name=data.company_name,
            job_title=data.job_title,
            main_responsibilities=data.main_tasks,
            required_skills=data.tech_stacks,
            recruitment_status="OPEN",
            recruitment_period=recruitment_period,
            ai_summary=data.ai_summary or "",
            evaluation_criteria=[
                JobEvaluationCriteriaItem(name=item.name, description=item.description)
                for item in data.evaluation_criteria
            ],
        )
