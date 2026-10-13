"""Local FastAPI service for synthetic molecular-tumor-board demonstrations."""
import hmac
import os
from typing import Optional, List

from agents.base import PHIGuard, SecurityException
from .models import PatientOncologyProfile, SomaticVariant
from .agents import MTBCoordinator

coordinator = MTBCoordinator()


def create_app():
    try:
        from fastapi import Depends, FastAPI, Header, HTTPException
        from pydantic import BaseModel, Field
    except ImportError:
        return None

    app = FastAPI(title="MTB-Orchestrator educational API", version="1.0.1")

    def require_token(x_api_key: Optional[str] = Header(default=None)):
        token = os.getenv("API_ACCESS_TOKEN", "")
        if len(token) < 32:
            raise HTTPException(status_code=503, detail="API_ACCESS_TOKEN is not configured")
        if not x_api_key or not hmac.compare_digest(x_api_key, token):
            raise HTTPException(status_code=401, detail="Invalid API key")

    class VariantInput(BaseModel):
        gene: str = Field(..., min_length=1, max_length=40)
        alteration: str = Field(..., min_length=1, max_length=100)
        variant_allele_freq: float = Field(..., ge=0, le=1, allow_inf_nan=False)

    class AuditOncologyRequest(BaseModel):
        case_id: str = Field(..., min_length=1, max_length=100)
        diagnosis: str = Field(..., min_length=1, max_length=200)
        stage: str = Field(..., min_length=1, max_length=100)
        ecog_ps: int = Field(default=0, ge=0, le=4)
        prior_therapies: List[str] = Field(default_factory=list)
        somatic_variants: List[VariantInput] = Field(default_factory=list)
        tmb_mut_per_mb: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
        msi_status: Optional[str] = None
        current_medications: List[str] = Field(default_factory=list)

    class ChatRequest(BaseModel):
        query: str = Field(..., min_length=1, max_length=1000)

    @app.get("/health")
    def health():
        return {"status": "HEALTHY", "service": "MTB synthetic demo", "live_clinical_data": False}

    @app.post("/api/mtb/audit", dependencies=[Depends(require_token)])
    def audit_case(req: AuditOncologyRequest):
        try:
            PHIGuard.assert_no_phi(req.model_dump_json())
        except SecurityException:
            raise HTTPException(status_code=422, detail="Potential personal identifier detected; use synthetic data")
        profile = PatientOncologyProfile(
            case_id=req.case_id,
            diagnosis=req.diagnosis,
            stage=req.stage,
            ecog_ps=req.ecog_ps,
            prior_therapies=req.prior_therapies,
            somatic_variants=[
                SomaticVariant(gene=v.gene, alteration=v.alteration, variant_allele_freq=v.variant_allele_freq)
                for v in req.somatic_variants
            ],
            tmb_mut_per_mb=req.tmb_mut_per_mb,
            msi_status=req.msi_status,
            current_medications=req.current_medications,
        )
        return coordinator.audit_profile(profile)

    @app.post("/api/chat", dependencies=[Depends(require_token)])
    def chat(req: ChatRequest):
        try:
            PHIGuard.assert_no_phi(req.query)
        except SecurityException:
            raise HTTPException(status_code=422, detail="Potential personal identifier detected; use synthetic data")
        return {"response": coordinator.query_assistant(req.query)}

    return app
