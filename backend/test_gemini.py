"""Quick test to verify Groq LLM works."""
import asyncio
from services.llm_service import call_llm_async
from config import settings

async def test():
    print(f"Testing model: {settings.LLM_MODEL}")
    print(f"API key: {settings.GROQ_API_KEY[:10]}...")
    result = await call_llm_async(
        [{"role": "user", "content": "Say hello in one sentence."}],
        max_tokens=50
    )
    print(f"Response: {result}")
    print("SUCCESS!")

if __name__ == "__main__":
    asyncio.run(test())
