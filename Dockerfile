ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
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
# 개발 스테이지
#================================
FROM base AS development

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --frozen --no-install-project

COPY --chown=appuser:appgroup . .

RUN uv run playwright install --with-deps chromium

RUN chown -R appuser:appgroup /app/.venv

USER appuser

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

#================================
# 프로덕션 스테이지
#================================
FROM base AS production

COPY --from=deps /app/.venv /app/.venv

RUN /app/.venv/bin/playwright install --with-deps chromium

COPY --chown=appuser:appgroup . .

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
