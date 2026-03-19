ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash -m appuser && \
    chown -R appuser:appgroup /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

#================================
# 의존성 설치 스테이지
#================================
FROM base AS deps

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --frozen --no-dev --no-install-project

#================================
# 개발 스테이지 (Hot Reload)
#================================
FROM base AS development

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --frozen --no-install-project

COPY --chown=appuser:appgroup shared/ ./shared/
COPY --chown=appuser:appgroup pipelines/resume_analysis/ ./pipelines/resume_analysis/
COPY --chown=appuser:appgroup README.md .

RUN chown -R appuser:appgroup /app/.venv

ENV PYTHONPATH="/app:/app/pipelines"
ENV TIKTOKEN_CACHE_DIR=/app/pipelines/resume_analysis/utils/tiktoken_cache

USER appuser

CMD ["bash", "-c", "uv run taskiq worker shared.pipeline_bridge.interface:broker_resume resume_analysis.main & uv run taskiq worker shared.pipeline_bridge.interface:broker_portfolio resume_analysis.main & wait -n"]

#================================
# 프로덕션 스테이지
#================================
FROM base AS production

COPY --from=deps /app/.venv /app/.venv

COPY --chown=appuser:appgroup shared/ ./shared/
COPY --chown=appuser:appgroup pipelines/resume_analysis/ ./pipelines/resume_analysis/
COPY --chown=appuser:appgroup README.md .

ENV PATH="/app/.venv/bin:$PATH"

ENV PYTHONPATH="/app:/app/pipelines"
ENV TIKTOKEN_CACHE_DIR=/app/pipelines/resume_analysis/utils/tiktoken_cache

USER appuser

CMD ["bash", "-c", "taskiq worker shared.pipeline_bridge.interface:broker_resume resume_analysis.main & taskiq worker shared.pipeline_bridge.interface:broker_portfolio resume_analysis.main & wait -n"]
