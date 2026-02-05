import pytest
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from shared.config import settings


@pytest.mark.asyncio
async def test_gemini_api_call():
    """
    LangChain을 사용하여 Google Gemini API 호출 테스트
    """
    # 1. API Key 확인
    api_key = settings.GOOGLE_API_KEY

    if not api_key:
        pytest.skip("⚠️ GOOGLE_API_KEY is not set in .env. Skipping Gemini API test.")

    print(f"\n🔑 Using Google API Key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 10 else ''}")

    try:
        # 2. Gemini 모델 초기화
        # gemini-1.5-flash 또는 gemini-pro 사용 권장
        llm = ChatGoogleGenerativeAI(
            model="gemini-3-flash-preview",
            google_api_key=api_key,
            temperature=0.7
        )

        # 3. 메시지 생성 및 호출
        message = HumanMessage(content="안녕하세요! 자기소개를 짧게 부탁해요.")
        
        print("\n🤖 Sending request to Gemini...")
        response = await llm.ainvoke([message])
        
        # 4. 결과 검증
        print(f"\n✅ Gemini Response:\n{response.content}")
        
        assert response is not None
        assert response.content is not None
        assert len(response.content) > 0

    except Exception as e:
        pytest.fail(f"❌ Gemini API Call Failed: {e}")

if __name__ == "__main__":
    # 직접 실행 시 비동기 런처 사용
    import asyncio
    try:
        asyncio.run(test_gemini_api_call())
    except Exception as e:
        # pytest.skip() 등은 여기서 잡히지 않을 수 있으므로 단순 출력
        print(e)
