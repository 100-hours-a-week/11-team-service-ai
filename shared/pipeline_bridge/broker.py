from aio_pika import ExchangeType
from taskiq_aio_pika import AioPikaBroker
from taskiq_redis import RedisAsyncResultBackend

from shared.config import settings
from .constants import (
    EXCHANGE_NAME,
    QUEUE_JOB_ANALYSIS,
    QUEUE_RESUME_ANALYSIS,
    QUEUE_PORTFOLIO_ANALYSIS,
    QUEUE_APPLICANT_EVALUATION,
    QUEUE_CANDIDATE_COMPARISON,
    TASK_JOB_ANALYZE,
    TASK_RESUME_ANALYZE,
    TASK_PORTFOLIO_ANALYZE,
    TASK_APPLICANT_EVALUATE,
    TASK_CANDIDATE_COMPARE,
)
from typing import Optional

from .formatter import RawJsonFormatter

# --- Taskiq Result Backend Configuration ---
result_backend: RedisAsyncResultBackend = RedisAsyncResultBackend(
    redis_url=settings.REDIS_URL
)


# 브로커 팩토리 함수: 파이프라인(도메인)별로 독립된 큐를 가진 브로커를 생성
def create_broker(
    queue_name: str, default_task_name: Optional[str] = None
) -> AioPikaBroker:
    broker = AioPikaBroker(
        url=settings.RABBITMQ_URL,
        queue_name=queue_name,  # 기본으로 바라볼 RabbitMQ Queue 이름 지정
        exchange_name=EXCHANGE_NAME,  # 여러 브로커가 속할 허브 이름 통일
        routing_key=queue_name,  # 정확히 해당 큐 이름으로 라우팅되도록 보장
        exchange_type=ExchangeType.DIRECT,  # Direct 타입이어야만 라우팅 키 기반 일대일 매칭이 정확히 수행됨
        declare_exchange_kwargs={
            "durable": True
        },  # Spring 백엔드와 설정 일치 (서버 재시작 시 exchange 유지)
        declare_queues_kwargs={
            "durable": True,
            "arguments": {"x-message-ttl": 300000},
        },  # Spring 백엔드와 설정 일치 (서버 재시작 시 queue 유지)
    ).with_result_backend(result_backend)

    if default_task_name:
        broker = broker.with_formatter(
            RawJsonFormatter(default_task_name=default_task_name)
        )

    return broker


# --- Domains Brokers ---

# 1. 채용 공고 분석 전담 브로커
broker_job = create_broker(QUEUE_JOB_ANALYSIS, TASK_JOB_ANALYZE)

# 2. 이력서 및 포트폴리오 분석 전담 브로커
broker_resume = create_broker(QUEUE_RESUME_ANALYSIS, TASK_RESUME_ANALYZE)
broker_portfolio = create_broker(QUEUE_PORTFOLIO_ANALYSIS, TASK_PORTFOLIO_ANALYZE)

# 3. 지원자 역량 평가 전담 브로커
broker_evaluate = create_broker(QUEUE_APPLICANT_EVALUATION, TASK_APPLICANT_EVALUATE)

# 4. 지원자 비교 전담 브로커
broker_compare = create_broker(QUEUE_CANDIDATE_COMPARISON, TASK_CANDIDATE_COMPARE)

# 모든 브로커를 모듈에서 참조하기 쉽게 묶어줌
brokers = [broker_job, broker_resume, broker_portfolio, broker_evaluate, broker_compare]
