from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_admin
from backend.app.database.session import get_db
from backend.app.models.feedback import Feedback
from backend.app.models.user import User
from backend.app.schemas.mlops import ModelVersionInfo, MLOpsSummary, PromoteRequest, RollbackRequest
from backend.app.services import monitoring_service
from src.rag.knowledge_base import load_chunks
from src.registry.model_registry import InvalidTransitionError, list_versions, rollback_to_version, set_lifecycle_stage

router = APIRouter(prefix="/mlops", tags=["mlops"])

REGISTERED_MODELS = [
    "finpilot-savings-predictor",
    "finpilot-transaction-categorizer",
    "finpilot-expense-forecaster",
    "finpilot-cashflow-forecaster",
]


@router.get("/models/{name}/versions", response_model=list[ModelVersionInfo])
def get_model_versions(name: str, current_admin: User = Depends(get_current_admin)):
    if name not in REGISTERED_MODELS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown registered model")
    return list_versions(name)


@router.post("/models/{name}/versions/{version}/promote", response_model=ModelVersionInfo)
def promote_model_version(
    name: str, version: str, payload: PromoteRequest, current_admin: User = Depends(get_current_admin)
):
    if name not in REGISTERED_MODELS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown registered model")
    try:
        result = set_lifecycle_stage(name, version, payload.target_stage)
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    versions = {v["version"]: v for v in list_versions(name)}
    return versions[version]


@router.post("/models/{name}/rollback")
def rollback_model(name: str, payload: RollbackRequest, current_admin: User = Depends(get_current_admin)):
    if name not in REGISTERED_MODELS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown registered model")
    try:
        return rollback_to_version(name, payload.target_version)
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/summary", response_model=MLOpsSummary)
def mlops_summary(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    registry = {name: list_versions(name) for name in REGISTERED_MODELS}
    performance = monitoring_service.performance_summary(db)
    drift = monitoring_service.drift_summary(db)

    total_feedback = db.query(Feedback).count()
    category_corrections = db.query(Feedback).filter(Feedback.feedback_type == "category_correction").count()

    chunks = load_chunks()
    documents = {c.document_id for c in chunks}

    return MLOpsSummary(
        registry=registry,
        performance=performance,
        drift=drift,
        feedback={
            "total_feedback": total_feedback,
            "category_corrections": category_corrections,
            "note": "Retraining is a manual step: python -m scripts.retrain_from_feedback",
        },
        rag={
            "document_count": len(documents),
            "chunk_count": len(chunks),
            "embedding_method": "TF-IDF (see src/rag/retrieval.py)",
        },
    )
