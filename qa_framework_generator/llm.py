from __future__ import annotations

import os
from dotenv import load_dotenv


def get_openai_chat_model():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for LLM generation nodes. "
            "Set it in your environment or in a .env file."
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
    )
