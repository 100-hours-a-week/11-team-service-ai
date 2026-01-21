from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="에러 식별 코드")
    message: str = Field(..., description="사용자용 에러 메시지")
    details: Optional[str] = Field(None, description="개발자 디버깅용 상세 정보")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = Field(..., description="요청 처리 성공 여부")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 생성 일시 (ISO 8601)")
    data: Optional[T] = Field(None, description="요청 처리 성공 시 반환되는 데이터")
    error: Optional[ErrorDetail] = Field(None, description="요청 처리 실패 시 반환되는 에러 정보")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
