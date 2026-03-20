import logging

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from langchain_core.messages import AIMessage

from .....domain.models.job import JobInfo
from .....domain.models.candidate import Candidate

from .configuration import CandidateContext, Configuration
from .state import CandidateState

from pydantic import BaseModel, Field

from .prompts import (
    DEBATE_AGENT_PROMPT,
    OPENING_STATEMENT_PROMPT,
    FINAL_DECISION_PROMPT,
)
from shared.utils import load_chat_model, AiResponse
from typing import cast

logger = logging.getLogger(__name__)


class FinalDecisionOutput(BaseModel):
    strengths: str = Field(description="내 지원자의 핵심 강점 요약")
    weaknesses: str = Field(description="내 지원자의 주요 약점 요약")


async def agent_me_attack(
    state: CandidateState, config: RunnableConfig, runtime: Runtime[CandidateContext]
):
    """내 지원자(My Candidate) 입장에서 방어 및 공격"""
    logger.info("🤖 Agent Me: Defending & Attacking...")

    # 1. Config & Context 로드
    cfg = Configuration.from_runnable_config(config)
    rtx = runtime.context  # CandidateContext (job_info, candidates)

    # 2. LLM 로드 (AiResponse structured output 사용)
    llm = load_chat_model(cfg.model_name, cfg.model_provider).with_structured_output(
        AiResponse, method="json_mode"
    )

    # 3. 정보 포맷팅
    job_info_text = _format_job_info(rtx.job_info)
    my_info = _format_candidate_info(rtx.my_candidate)
    comp_info = _format_candidate_info(rtx.competitor_candidate)

    # 4. 첫 턴이면 Opening Statement 사용, 이후는 Debate 프롬프트 사용
    if len(state.messages) == 0:
        prompt = OPENING_STATEMENT_PROMPT
        logger.info("📢 Agent_Me: Opening Statement")
    else:
        prompt = DEBATE_AGENT_PROMPT
        logger.info("💬 Agent_Me: Responding to competitor")

    # 5. 체인 실행
    chain = prompt | llm

    ai_response = cast(
        AiResponse,
        await chain.ainvoke(
            {
                "me": "Agent_Me",
                "other": "Agent_Competitor",
                "job_info": job_info_text,
                "my_candidate_info": my_info,
                "competitor_info": comp_info,
                "chat_history": state.messages,
            }
        ),
    )

    # AIMessage 생성 (structured output의 response 필드 사용)
    message = AIMessage(content=f"[Agent_Me]\n{ai_response.response}", name="Agent_Me")
    logger.info(f"\n[Agent_Me Response]:\n{message.content}\n")
    return {"messages": [message]}


async def agent_competitor_attack(
    state: CandidateState, config: RunnableConfig, runtime: Runtime[CandidateContext]
):
    """경쟁 지원자(Competitor) 입장에서 방어 및 공격"""
    logger.info("🤖 Agent Competitor: Defending & Attacking...")

    cfg = Configuration.from_runnable_config(config)
    rtx = runtime.context

    # AiResponse structured output 사용
    llm = load_chat_model(cfg.model_name, cfg.model_provider).with_structured_output(
        AiResponse, method="json_mode"
    )

    job_info_text = _format_job_info(rtx.job_info)
    my_info = _format_candidate_info(rtx.competitor_candidate)
    comp_info = _format_candidate_info(rtx.my_candidate)

    # Competitor는 항상 두 번째 발언자이므로 DEBATE_AGENT_PROMPT 사용
    chain = DEBATE_AGENT_PROMPT | llm
    logger.info("💬 Agent_Competitor: Responding to Agent_Me")

    # 역할 반전 (who <-> other)
    ai_response = cast(
        AiResponse,
        await chain.ainvoke(
            {
                "me": "Agent_Competitor",
                "other": "Agent_Me",
                "job_info": job_info_text,
                "my_candidate_info": my_info,
                "competitor_info": comp_info,
                "chat_history": state.messages,
            }
        ),
    )

    # AIMessage 생성 (structured output의 response 필드 사용)
    message = AIMessage(
        content=f"[Agent_Competitor]\n{ai_response.response}", name="Agent_Competitor"
    )
    logger.info(f"\n[Agent_Competitor Response]:\n{message.content}\n")

    # 턴 카운트 증가
    return {"turn_count": state.turn_count + 1, "messages": [message]}


async def check_turn(state: CandidateState):
    turn_count = state.turn_count
    logger.info(f"🔄 Current Turn: {turn_count}")

    # 3턴(왕복 1.5회) 정도 진행 후 종료
    if turn_count < 3:
        return "continue"
    else:
        return "end"


async def finalize_evaluation(
    state: CandidateState, config: RunnableConfig, runtime: Runtime[CandidateContext]
):
    """최종 판정 및 리포트 생성"""
    logger.info("⚖️ Finalizing Evaluation...")

    cfg = Configuration.from_runnable_config(config)
    rtx = runtime.context

    # Structured Output 사용 (FinalDecisionOutput)
    llm = load_chat_model(cfg.model_name, cfg.model_provider).with_structured_output(
        FinalDecisionOutput, method="json_mode"
    )

    job_info_text = _format_job_info(rtx.job_info)
    my_info = _format_candidate_info(rtx.my_candidate)
    comp_info = _format_candidate_info(rtx.competitor_candidate)

    chain = FINAL_DECISION_PROMPT | llm

    try:
        result = cast(
            FinalDecisionOutput,
            await chain.ainvoke(
                {
                    "job_info": job_info_text,
                    "my_candidate_info": my_info,
                    "competitor_info": comp_info,
                    "chat_history": state.messages,
                }
            ),
        )

        return {"strengths": result.strengths, "weaknesses": result.weaknesses}

    except Exception as e:
        logger.error(f"Failed to generate structured report: {e}")
        return {
            "strengths": "분석 실패 (오류 발생)",
            "weaknesses": "분석 실패 (오류 발생)",
        }


def _format_job_info(job: JobInfo) -> str:
    return f"""
    - 직무: {job.job_title}
    - 주요 업무: {", ".join(job.main_tasks)}
    - 기술 스택: {", ".join(job.tech_stacks)}
    - 자격 요건: {", ".join(getattr(job, "qualifications", []))}
    - 우대 사항: {", ".join(getattr(job, "preferred_points", []))}
    """


def _format_candidate_info(candidate: Candidate) -> str:
    return f"""
    [Evaluation Summary]
    - 한줄평: {candidate.evaluation.one_line_review}
    - 상세 피드백: {candidate.evaluation.feedback_detail}
    
    [Documents Summary]
    - 이력서 요약: {candidate.documents.parsed_resume}
    - 포트폴리오 요약: {candidate.documents.parsed_portfolio}
    """
