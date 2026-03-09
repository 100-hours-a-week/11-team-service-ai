ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
    libmagic1 \
    xvfb \
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

# 채용 공고 크롤링을 수행하는 모듈이므로 Playwright(Chromium) 브라우저를 설치
RUN /app/.venv/bin/playwright install --with-deps chromium

COPY --chown=appuser:appgroup shared/ ./shared/
COPY --chown=appuser:appgroup pipelines/job_analysis/ ./pipelines/job_analysis/
COPY --chown=appuser:appgroup README.md .

RUN chown -R appuser:appgroup /app/.venv

USER appuser

CMD ["uv", "run", "taskiq", "worker", "shared.pipeline_bridge.interface:broker_job", "job_analysis.main"]

#================================
# 프로덕션 스테이지
#================================
FROM base AS production

COPY --from=deps /app/.venv /app/.venv

RUN /app/.venv/bin/playwright install --with-deps chromium

COPY --chown=appuser:appgroup shared/ ./shared/
COPY --chown=appuser:appgroup pipelines/job_analysis/ ./pipelines/job_analysis/
COPY --chown=appuser:appgroup README.md .

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

CMD ["taskiq", "worker", "shared.pipeline_bridge.interface:broker_job", "job_analysis.main"]
