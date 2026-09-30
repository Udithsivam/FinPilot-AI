from typing import Literal

from pydantic import BaseModel


class ModelVersionInfo(BaseModel):
    name: str
    version: str
    run_id: str
    lifecycle_stage: Literal["candidate", "validated", "production", "archived"]
    created_at: int


class PromoteRequest(BaseModel):
    target_stage: Literal["validated", "production", "archived"]


class RollbackRequest(BaseModel):
    target_version: str


class MLOpsSummary(BaseModel):
    registry: dict
    performance: list
    drift: list
    feedback: dict
    rag: dict
