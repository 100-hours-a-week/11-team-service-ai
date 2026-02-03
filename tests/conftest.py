
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# DB 설정 가져오기 (Import Error 방지)
try:
    from shared.db.connection import engine, Base
except ImportError:
    # shared 모듈이 경로에 없을 경우를 대비 (보통 pytest 실행 시, rootdir이 잡혀있어 괜찮음)
    pass

@pytest.fixture(scope="session")
def event_loop():
    """
    pytest-asyncio의 기본 event_loop fixture를 session scope로 재정의.
    이것이 없으면 'ScopeMismatch' 에러가 발생할 수 있음.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    각 테스트 함수마다 실행되는 DB 세션 Fixture.
    1. DB 연결 (connect)
    2. 트랜잭션 시작 (begin)
    3. 세션 생성 및 테스트에 전달 (yield)
    4. 테스트 종료 후 롤백 (rollback) -> 데이터 원상복구
    """
    connection = await engine.connect()
    transaction = await connection.begin()
    
    # 롤백을 보장하기 위해 비동기 세션 생성 시 bind=connection 사용
    session_factory = sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with session_factory() as session:
        yield session
        
        # 테스트가 끝난 후 롤백
        await transaction.rollback()
        await connection.close()
