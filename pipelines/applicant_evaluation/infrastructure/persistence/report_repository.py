from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from shared.db.model.models import AiApplicantEvaluation, JobApplication
from ...domain.interface.repository_interfaces import ReportRepository
from ...domain.models.report import AnalysisReport

class SqlAlchemyReportRepository(ReportRepository):
    """
    최종 분석 리포트를 DB에 저장하는 리포지토리 구현체
    """
    def __init__(self, session: Session):
        self.session = session

    def save_report(self, user_id: int, job_id: int, report: AnalysisReport) -> None:
        # 1. 대상 JobApplication ID 찾기
        job_app = (
            self.session.query(JobApplication)
            .filter(
                JobApplication.user_id == user_id,
                JobApplication.job_master_id == job_id
            )
            .one_or_none()
        )
        
        if not job_app:
            raise NoResultFound(f"Job application not found for user={user_id}, job={job_id}")

        # 2. 도메인 객체 -> DB 모델 변환
        # 리포트의 구조화된 데이터(JSON) 생성
        strengths = []
        weaknesses = []
        
        # 상세 피드백(feedback_detail)을 분석해서 강점/약점으로 나눌 수도 있지만, 
        # 현재는 통으로 저장하거나 별도 로직이 필요함.
        # 일단은 competency_scores의 내용을 strengths/weaknesses로 간단히 맵핑하거나 
        # DB 컬럼에 맞게 변환해야 함.
        # 여기서는 간단히 전체 피드백을 strengths 리스트의 하나로 넣는 등 임시 처리하거나,
        # Report 모델에 strengths/weaknesses 필드를 추가하는 것이 좋음.
        # (TODO: 도메인 모델과 DB 모델 간의 필드 불일치 해결 필요)
        
        # 현재 도메인 모델: one_line_review, feedback_detail, competency_scores
        # DB 모델: overall_strengths(JSON), overall_weaknesses(JSON), final_score, etc.
        
        # 임시 매핑 전략:
        # DB의 'improvement_suggestions' <- feedback_detail
        # DB의 'overall_strengths' <- one_line_review (임시)
        improvement = {"detail": report.feedback_detail}

        # 3. Upsert Logic (기존 평가 결과가 있으면 업데이트)
        existing_eval = (
            self.session.query(AiApplicantEvaluation)
            .filter(AiApplicantEvaluation.job_application_id == job_app.job_application_id)
            .one_or_none()
        )

        if existing_eval:
            existing_eval.final_score = int(report.overall_score)
            existing_eval.overall_strengths = {"summary": report.one_line_review}
            existing_eval.improvement_suggestions = improvement
            # TODO: rank_percentile 계산 로직은 별도 배치 작업 필요
        else:
            new_eval = AiApplicantEvaluation(
                job_application_id=job_app.job_application_id,
                eval_job_id=0, # TODO: 실제 작업을 추적하는 ID가 있다면 할당 (없으면 0 or NULL)
                final_score=int(report.overall_score),
                rank_percentile=None,
                overall_strengths={"summary": report.one_line_review},
                overall_weaknesses={},
                improvement_suggestions=improvement
            )
            self.session.add(new_eval)

        self.session.flush()
