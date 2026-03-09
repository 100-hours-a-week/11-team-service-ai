# Backend Project Guide

## 🏗️ 아키텍처
- **Backend**: FastAPI (Python)
- **Package Manager**: uv

## 🛠️ 실행 및 환경 세팅 가이드 (Quick Start)

본 프로젝트는 데이터베이스, 벡터 DB, 메시지 큐 등 다양한 인프라와 여러 대의 AI 모델 워커(Worker)들이 상호작용하는 **분산 마이크로서비스(MSA) 아키텍처**로 설계되어 있습니다.
따라서 로컬 패키지 설치 방식보다는 **Docker Compose를 활용한 전체 클러스터 동시 구동 방식**을 가장 권장합니다.

### 0. 사전 준비사항
- [Docker & Docker Compose](https://www.docker.com/products/docker-desktop/) 설치 완료
- 환경변수 템플릿 복사 및 설정 기입
  ```bash
  cp .env.example .env
  ```
- (선택) 로컬 테스트용 Python 패키지 매니저 **uv** 설치 (단축키: `brew install uv`)

---

### 1. 🏗️ 백그라운드 인프라 실행 (Message Queue, Database)
RabbitMQ, Redis, MySQL, Weaviate 인프라 4개를 먼저 구동합니다.

```bash
docker-compose -f docker-compose-infra.yml up -d
```
> **참고:** 이 명령어를 실행하면 `infra-network` Private Network가 생성되며, 앞으로 뜨게 될 모든 컨테이너는 이 안에서 격리되어 네트워크 통신을 합니다.

---

### 2. 🚀 API 서버 및 멀티 AI 워커 클러스터 실행
메인 어플리케이션(FastAPI 서버)과 4대의 도메인별 전담 AI 풀(Taskiq Workers)을 가동합니다.

```bash
docker-compose up --build -d
```
> **💡 동작 특징 (Hot Reload)** 
> - 편의를 위해 개발용(`target: development`) 컨테이너로 빌드됩니다.
> - 여러분이 IDE에서 파이썬 코드를 저장하는 즉시, 컨테이너 볼륨 마운트가 이를 감지하여 알아서 자동으로 자기를 재시작(Hot Reload)합니다.

---

### 3. 🔍 상태 모니터링 및 트러블슈팅

클러스터가 잘 돌고 있는지, 워커가 일을 잘하고 있는지 확인하고 싶을 때 사용합니다.

```bash
# 1. 뼈대 인프라(DB) 컨테이너 상태 보기
docker-compose -f docker-compose-infra.yml ps

# 2. 메인 앱(API, Worker) 컨테이너 상태 보기
docker-compose ps

# 3. 로그만 실시간으로 보기
# compose 파일 전체 확인
docker-compose logs -f
# 특정 컨테이너 확인
docker logs -f ai_worker_resume
```

- **Swagger UI (API 테스트 명세서):** [http://localhost:8000/docs](http://localhost:8000/docs) 접속

---

### 🛑 서버 종료 (Shutdown)
퇴근할 때, 혹은 네트워크 캐시를 깨끗히 밀고 다시 시작하고 싶을 때 아래의 명령어들을 순서대로 사용합니다.

```bash
# 1. 앱 서버(API, 워커) 일시 정지 및 삭제
docker-compose down

# 2. 백그라운드 인프라(DB 등) 삭제
docker-compose -f docker-compose-infra.yml down
```

---

## 🧪 로컬 테스트 (단위 테스트) 실행

도커 밖 환경(로컬)에서 직접 파이썬 의존성을 깔고 코드를 고치거나 테스트할 경우 활용합니다.

```bash
# 1. 의존성 1초만에 동기화 설치
uv sync

# 2. 전체 단위 테스트 구동
uv run pytest

# 3. 정적 코드 분석 (Linting, Formatting)
uv run ruff check .
uv run black --check .
uv run mypy .
```