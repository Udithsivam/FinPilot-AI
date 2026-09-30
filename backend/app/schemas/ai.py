from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class ChatSource(BaseModel):
    index: int
    title: str
    source: str
    document_id: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    user_facts: list[str]
    predictions: list[str]
    provider: str
