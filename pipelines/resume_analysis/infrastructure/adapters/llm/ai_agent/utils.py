"""Shared utility functions used in the project.

Functions:
    load_chat_model: Load a chat model based on provider and name.
"""

import logging
from typing import Optional

from langchain_core.language_models import BaseChatModel
from shared.config import settings

logger = logging.getLogger(__name__)

def load_chat_model(model_name: str, model_provider: str) -> BaseChatModel:
    """Load a chat model based on the provider and name."""
    
    if model_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        logger.info(f"🤖 Loading Gemini Model: {model_name}")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0,
        )
    else: # openai or default
        from langchain_openai import ChatOpenAI
        from pydantic import SecretStr

        logger.info(f"🤖 Loading OpenAI Model: {model_name}")
        return ChatOpenAI(
            model=model_name,
            temperature=0,
            api_key=(
                SecretStr(settings.OPENAI_API_KEY)
                if settings.OPENAI_API_KEY
                else None
            ),
        )
