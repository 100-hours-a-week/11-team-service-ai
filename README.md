# Backend Project Guide

## 🏗️ 아키텍처
- **Backend**: FastAPI (Python)
- **Package Manager**: uv

## 🛠️ 환경 구성 (Environment Setup)

### 1. `.env` 파일 설정
프로젝트 실행 전 환경 변수 파일을 생성합니다.
```bash
cp .env.example .env
```

---

## 📦 패키지 설치 (Installation)

빠른 속도의 Python 패키지 매니저인 **uv**를 사용합니다.

### 1. uv 설치
```bash
brew install uv
```

### 2. 가상환경 생성 및 의존성 설치
`pyproject.toml`을 기반으로 가상환경을 구성합니다.
```bash
uv sync
```

---

## 🚀 프로젝트 실행 (Execution)

가상환경을 사용하여### 3. 서버 실행 (Run Server)

```bash
# 개발 모드 실행
# 기본 포트: 8000
uv run uvicorn api.main:app --reload
```

---

## 🧪 테스트 실행 (Testing)
작성된 단위 테스트를 실행하여 API와 파이프라인 연동을 검증할 수 있습니다.

```bash
# 전체 테스트 실행
uv run pytest

# 특정 테스트 파일 실행
uv run pytest tests/api/test_job_posting_router.py
```

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔧 트러블슈팅 (Troubleshooting)

### 데이터베이스 접속 확인

### 가상환경 오류 해결
의존성이 꼬였을 경우 가상환경을 초기화합니다.
```bash
rm -rf .venv
rm -f uv.lock
uv sync
```