import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Use absolute imports based on the project root 'ai'
from api.core.exception import CustomException, ErrorCode
from api.routes import applicant, document, job_posting
from shared.schema.common_schema import ApiResponse, ErrorDetail
import uvicorn
from contextlib import asynccontextmanager

from shared.pipeline_bridge.broker import brokers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FastAPI 서버 구동 시: 브로커 연결 (Connection 생성) 및 큐 선언 대기
    for broker in brokers:
        await broker.startup()

    yield

    # FastAPI 서버 종료 시: 브로커 소켓 연결 안전하게 해제 (Graceful Shutdown)
    for broker in brokers:
        await broker.shutdown()


app = FastAPI(title="AI Service API", lifespan=lifespan)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 기본 에러처리
@app.exception_handler(Exception)
async def default_exception_handler(request: Request, exc: Exception):
    error_msg = str(exc)
    print(f"🚨 500 Internal Server Error: {error_msg}")

    error_detail = ErrorDetail(
        code=ErrorCode.INTERNAL_SERVER_ERROR,
        message="서버 내부 오류가 발생했습니다.",
        details=error_msg,
    )

    response: ApiResponse[None] = ApiResponse(success=False, error=error_detail)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(mode="json"),
    )


# 요청데이터가 pydantic검증에 실패하는 경우
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for error in exc.errors():
        msg = error["msg"].replace("Value error, ", "")
        loc = ".".join(str(loc_part) for loc_part in error["loc"])
        details.append(f"{loc}: {msg}")

    error_detail = ErrorDetail(
        code=ErrorCode.INVALID_INPUT_VALUE,
        message="입력값이 유효하지 않습니다.",
        details="; ".join(details),
    )

    response: ApiResponse[None] = ApiResponse(success=False, error=error_detail)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response.model_dump(mode="json"),
    )


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    error_detail = ErrorDetail(code=exc.code, message=exc.message)
    response: ApiResponse[None] = ApiResponse(success=False, error=error_detail)
    # Defaulting CustomException to 400 or mapping could be better, keeping 400 for now or 404 based on context
    # Original code had 404, let's stick to 400 typically for business logic errors unless specified
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=response.model_dump(mode="json"),
    )


@app.get("/")
async def root():
    print("hello")
    return {"message": "AI Model Server is running 🚀"}


@app.post("/api/internal/ai/callback", tags=["Internal"])
async def receive_callback(payload: dict):
    """
    [테스트/임시용] 워커가 처리 완료 후 보내는 콜백(Webhook)을 수신하는 서버 엔드포인트입니다.
    스프링 서버가 아직 연동되지 않았을 때 로컬에서 결과를 확인하기 위해 사용합니다.
    """
    import json

    logger.info("================== [CALLBACK RECEIVED] ==================")
    logger.info(json.dumps(payload, indent=2, ensure_ascii=False))
    logger.info("=========================================================")

    return {"status": "Callback received"}


# Include Routers
app.include_router(job_posting.router)
app.include_router(applicant.router)
app.include_router(document.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
