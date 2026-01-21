from dotenv import load_dotenv
load_dotenv(override=True)

from pydantic_settings import BaseSettings, SettingsConfigDict

# BaseSettings클래스 안에 변수를 설정하면 "model_config = SettingsConfigDict" 을 통해 .env를 읽어와서 각 변수에 매핑
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Weaviate configs
    WEAVIATE_HOST: str = "127.0.0.1"
    WEAVIATE_PORT: int = 8080
    WEAVIATE_GRPC_PORT: int = 50051

    # RecordManager configs
    RECORD_MANAGER_DB_URL: str = "postgresql://user:password@localhost:5432/rag"

    # External APIs
    OPENAI_API_KEY: str

settings = Settings()
