
from pydantic import BaseModel, Field
from typing import Optional


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=5000,
        description="User's question"
    )


class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=5000,
        description="User's chat message"
    )
    session_id: Optional[str] = None


class AnswerResponse(BaseModel):
    answer: str
    sources: list[dict]
    retrieved_contexts: list[str]
