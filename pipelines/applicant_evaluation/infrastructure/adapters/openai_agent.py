from typing import List
import json
from openai import OpenAI
from shared.config import settings
from ...domain.interface.adapter_interfaces import AnalystAgent
from ...domain.models.job import JobInfo, EvaluationCriteria
from ...domain.models.report import CompetencyResult, OverallFeedback

class OpenAiAnalyst(AnalystAgent):
    """
    OpenAI API를 사용하여 지원자를 분석하는 AI 에이전트 구현체
    """
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4-turbo-preview" # or settings.MODEL_NAME

    def evaluate_competency(
        self, 
        job_info: JobInfo,
        criteria: EvaluationCriteria, 
        resume_text: str, 
        portfolio_text: str
    ) -> CompetencyResult:
        """
        단일 평가 기준에 대해 점수와 이유를 생성
        """
        system_prompt = f"""
        당신은 전문적인 채용 담당관입니다. 
        지원자가 '{job_info.company_name}' 회사의 다음 직무에 지원했습니다.
        
        [직무 정보]
        - 주요 업무: {', '.join(job_info.main_tasks)}
        - 기술 스택: {', '.join(job_info.tech_stacks)}
        
        당신의 임무는 지원자의 서류(이력서, 포트폴리오)를 분석하여 
        다음 평가 기준: '{criteria.name}' ({criteria.description})
        에 대해 0~100점 사이의 점수를 매기고 구체적인 근거를 서술하는 것입니다.
        """
        
        user_prompt = f"""
        [이력서 내용]
        {resume_text[:10000]} # 토큰 제한 고려하여 잘라냄

        [포트폴리오 내용]
        {portfolio_text[:10000]}
        
        결과를 반드시 다음 JSON 형식으로만 응답해주세요:
        {{
            "score": <0~100 사이 숫자>,
            "reason": "<평가 근거 및 상세 사유>"
        }}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        raw_content = response.choices[0].message.content
        data = json.loads(raw_content)
        
        return CompetencyResult(
            name=criteria.name,
            score=float(data.get("score", 0.0)),
            description=data.get("reason", "No reason provided.")
        )

    def synthesize_report(
        self, 
        job_info: JobInfo,
        competency_results: List[CompetencyResult]
    ) -> OverallFeedback:
        """
        개별 평가 결과를 종합하여 최종 리포트 생성
        """
        # 평가 결과 요약 텍스트 생성
        results_summary = "\n".join([
            f"- {r.name}: {r.score}점. {r.description}" 
            for r in competency_results
        ])
        
        system_prompt = f"""
        당신은 채용 결정권자입니다. 
        '{job_info.company_name}' 회사의 채용 공고에 대한 지원자 평가 결과가 다음과 같이 취합되었습니다.

        [직무 요약]
        {job_info.summary[:500]}

        [평가 결과 요약]
        {results_summary}
        """
        
        user_prompt = """
        위 정보를 바탕으로 채용 담당자 관점에서 다음 두 가지를 작성해주세요.
        1. 한 줄 평가 (one_line_review): 지원자의 핵심 역량과 회사 적합도를 한 문장으로 요약
        2. 상세 피드백 (feedback_detail): 직무 기술서(JD)와 지원자 역량을 비교하여, 강점과 보완점을 구체적으로 서술

        결과를 반드시 다음 JSON 형식으로만 응답해주세요:
        {
            "one_line_review": "...",
            "feedback_detail": "..."
        }
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        data = json.loads(response.choices[0].message.content)

        return OverallFeedback(
            one_line_review=data.get("one_line_review", ""),
            feedback_detail=data.get("feedback_detail", "")
        )
