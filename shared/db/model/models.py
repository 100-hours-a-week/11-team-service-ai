from sqlalchemy import Column, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# --- User 테이블 ---
class User(Base):
    __tablename__ = "User"
    user_id = Column(String(50), primary_key=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=False)  # UNIQUE 제약조건 제거
    img_id = Column(String(50))  # 외래키 정보 제거
