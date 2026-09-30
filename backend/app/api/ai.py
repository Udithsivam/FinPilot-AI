from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.ai import ChatRequest, ChatResponse
from src.rag.assistant import answer_question

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Grounded financial assistant: combines the user's own data, real
    ML predictions, and retrieved knowledge-base content (see
    src/rag/assistant.py). Always scoped to current_user.id — the
    assistant never sees another user's financial data."""
    return answer_question(db, current_user.id, payload.question)
