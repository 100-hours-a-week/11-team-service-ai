import warnings
from dotenv import load_dotenv

load_dotenv(override=True)

# SSL 소켓 미종료 관련 ResourceWarning 무시 (LLM 클라이언트 등에서 발생)
# 특정 라이브러리(httpx, sqlalchemy 등) 내부에서 간헐적으로 나타나는 경고를 전역적으로 차단
warnings.filterwarnings(
    "ignore", category=ResourceWarning, message=r"unclosed <ssl\.SSLSocket"
)

from pydantic_settings import BaseSettings, SettingsConfigDict  # noqa: E402


# BaseSettings클래스 안에 변수를 설정하면 "model_config = SettingsConfigDict" 을 통해 .env를 읽어와서 각 변수에 매핑
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Profile (dev/prod)
    PROFILE: str = "dev"
    # Mock mode option (only works when PROFILE=dev)
    USE_MOCK: bool = True

    @property
    def use_mock(self) -> bool:
        """dev 프로필이면서 USE_MOCK=true일 때만 목업 데이터 사용"""
        return self.PROFILE.lower() == "dev" and self.USE_MOCK

    # Weaviate configs
    WEAVIATE_HOST: str = "127.0.0.1"
    WEAVIATE_PORT: int = 8080
    WEAVIATE_GRPC_PORT: int = 50051

    # Database configs
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "ai_db"

    @property
    def DATABASE_URL(self) -> str:
        """Constructs the MariaDB connection URL asynchronously."""
        return f"mysql+asyncmy://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def WEAVIATE_URL(self) -> str:
        """Constructs the Weaviate connection URL."""
        return f"http://{self.WEAVIATE_HOST}:{self.WEAVIATE_PORT}"

    # LLM 공급자
    LLM_PROVIDER: str = "openai"  # openai or gemini

    # OpenAI
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Gemini
    GOOGLE_API_KEY: str | None = None
    GOOGLE_MODEL: str = "gemini-3-flash-preview"

    # VLLM
    VLLM_BASE_URL: str | None = None
    VLLM_MODEL: str = "Qwen/Qwen3-32B-FP8"

    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "ap-northeast-2"
    AWS_S3_BUCKET_NAME: str

    EMBEDDING_MODEL: str
    TAVILY_API_KEY: str

    # rabbitmq
    RABBITMQ_URL: str

    # redis
    REDIS_URL: str

    # MQ_CALLBACK_URL
    MQ_CALLBACK_URL: str

    RERANKER_MODEL_URL: str
    RERANKER_MODEL: str


settings = Settings()  # type: ignore
