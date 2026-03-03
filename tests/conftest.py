import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from shared.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_engine(event_loop):
    """
    테스트 함수 전용 Async Engine 생성.
    Scope를 function으로 설정하여 Loop 충돌 방지.
    """
    # settings에서 DATABASE_URL을 가져오거나 직접 지정
    DATABASE_URL = settings.DATABASE_URL

    engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    yield engine
    event_loop.run_until_complete(engine.dispose())


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    각 테스트 함수마다 실행되는 DB 세션 Fixture.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()

    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session

        # 테스트가 끝난 후 롤백
        if transaction.is_active:
            await transaction.rollback()
        await connection.close()
