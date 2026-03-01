from tavily import TavilyClient
from shared.config import settings
client = TavilyClient(settings.TAVILY_API_KEY)
response = client.search(
    query="QLoRA 기반 Llama-3 모델 도메인 특화 성능 향상 경험",
    search_depth="advanced"
)
print(response)