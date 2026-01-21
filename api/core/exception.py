from enum import Enum
from fastapi import status

# 에러는 대 중 소 로 분류하여 나타내기
# 대 : HTTP상태코드
# 중 : ErrorCode
# 소 : 에러 메시지

# 에러코드는 최대한 공통적으로 관리
# 에러메시지는 raise Error를 던지면서 추가
class ErrorCode(str, Enum):

    # 500 서버 내부에러
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"

    # 400 Bad Request 관련
    INVALID_INPUT_VALUE = "INVALID_INPUT_VALUE"
    
    # 404 Not Found 관련
    USER_NOT_FOUND = "USER_NOT_FOUND"
    ITEM_NOT_FOUND = "ITEM_NOT_FOUND"
    
    # 401/403 Auth 관련
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    PERMISSION_DENIED = "PERMISSION_DENIED"

# 커스텀 Exception정의
# 서버 내부에서 잘못된 응답인경우 raise 커스텀Exception
# main라우터에서 에러응답 전역처리
class CustomException(Exception):
    def __init__(
        self, 
        code: ErrorCode, 
        message: str = "에러가 발생했습니다.", 
    ):
        self.code = code
        self.message = message
        super().__init__(message)