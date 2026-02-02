from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from shared.config import settings

# MariaDB 연결 URL
DATABASE_URL = settings.DATABASE_URL

# 비동기 엔진 생성
# pool_recycle: 연결이 끊어지는 것을 방지하기 위해 주기적으로 재생성 (초 단위)
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 쿼리 로깅 여부 (개발 시 True 권장)
    pool_pre_ping=True,  # 연결 유효성 체크
    pool_recycle=3600,
)

# 비동기 세션 팩토리
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# 모델 베이스 클래스
class Base(DeclarativeBase):
    pass


# 의존성 주입(Dependency Injection)용 함수
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
