
from functools import lru_cache

from langchain_groq import ChatGroq

from app.core.config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    validate_config
)


@lru_cache(maxsize=1)
def get_llm():

    validate_config()

    llm = ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0,
        max_retries=2,
        timeout=60
    )

    return llm


def test_groq_connection():

    llm = get_llm()

    response = llm.invoke(
        "Explain RAG in two simple sentences."
    )

    return response.content
