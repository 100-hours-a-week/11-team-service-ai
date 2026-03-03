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

# 정적 분석 (Linting, Formatting, Type Checking)
uv run ruff check .
uv run black --check .
uv run mypy .
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

---

## 🐳 Docker를 이용한 로컬 실행 (개발용)

어플리케이션을 도커 컨테이너 환경에서 실행하여 가상환경 및 종속성 세팅 없이도 원활한 개발 및 테스트를 진행할 수 있습니다. 
특히 코드 파일을 수정하면 컨테이너를 재시작할 필요 없이 실시간으로 반영(Hot Reload) 되도록 볼륨 마운트가 설정되어 있습니다.

### 1. 도커 이미지 빌드
먼저 `Dockerfile`을 기반으로 개발용 환경 타겟(`development`) 이미지를 빌드합니다.

```bash
docker build --target development -t ai-dev .
```
- `--target development`: 멀티 스테이지 빌드 중에서 서버 재시작 도구와 개발 의존성이 포함된 `development` 단계까지만 생성합니다.
- `-t ai-dev`: 방금 만들어진 도커 이미지에 저장하고 불러오기 쉽도록 `ai-dev`라는 태그(이름)를 지정합니다.
- `.`: 현재 위치한 디렉토리의 도커 파일을 사용하겠다는 의미입니다.

### 2. 도커 컨테이너 실행
위에서 만든 컨테이너 안에서 프로젝트를 실행하며, 로컬 코드를 컨테이너에 연동합니다.

```bash
docker run -p 8000:8000 --env-file .env -v $(pwd)/api:/app/api -v $(pwd)/shared:/app/shared -v $(pwd)/pipelines:/app/pipelines ai-dev
```
- `-p 8000:8000`: 로컬(내 컴퓨터)의 `8000` 포트와 컨테이너 내부 앱의 `8000` 포트를 서로 연결해줍니다. (`localhost:8000`으로 접속 가능)
- `--env-file .env`: 루트 경로에 작성해둔 `.env` 파일에 담긴 환경 변수들을 컨테이너 내부 시스템에 주입합니다.
- `-v $(pwd)/...:/app/...`: 사용 중인 로컬 컴퓨터의 주요 소스코드 폴더(`api`, `shared`, `pipelines`)들을 컨테이너 내부(`/app` 경로 아래)와 실시간으로 동기화(Volume Mount)시킵니다. 이 덕분에 코드를 변경하는 즉시 컨테이너에 반영되어 바로 테스트해볼 수 있습니다.
- `ai-dev`: 앞서 빌드했던 도커 이미지(`ai-dev`)를 바탕으로 컨테이너를 구동한다는 의미입니다.