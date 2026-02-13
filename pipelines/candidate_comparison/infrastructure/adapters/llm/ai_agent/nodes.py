from langchain_core.language_models.chat_models import BaseChatModel
import logging
from typing import List, Union

from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from .....domain.interface.adapter_interfaces import ComparisonAnalyzer
from .....domain.models.job import JobInfo
from .....domain.models.report import ComparisonReport
from .....domain.models.candidate import Candidate

from .configuration import CandidateContext
from .state import CandidateState

from .prompts import get_analysis_prompt, get_final_report_prompt
from .utils import load_chat_model, AiResponse

logger = logging.getLogger(__name__)


async def agent_me_attack(state: CandidateState, config: RunnableConfig, runtime: Runtime[CandidateContext]):

    logger.info(f"agent_me_attack")

    return {"messages" : [AIMessage("내가 공격했습니다.")]}

async def agent_competitor_attack(state: CandidateState, config: RunnableConfig, runtime: Runtime[CandidateContext]):

    logger.info(f"agent_competitor_attack")

    return {"turn_count":state.turn_count+1, "messages" : [AIMessage("상대방이 공격했습니다.")]}

async def check_turn(state: CandidateState):

    turn_count = state.turn_count
    logger.info(f"토론 종료 판단 중....{turn_count}")

    # turn_count를 증가시키면서 라우팅
    if turn_count < 3:
        return "continue"
    else:
        return "end"

async def finalize_evaluation(state: CandidateState, config: RunnableConfig, runtime: Runtime[CandidateContext]):

    logger.info(f"agent_me_attack")

    return {"strengths": "나의 강점입니다.", "weaknesses": "나의 약점입니다."}
