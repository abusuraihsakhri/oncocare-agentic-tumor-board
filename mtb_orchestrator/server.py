"""
FastAPI REST API Server for MTB-Orchestrator.
"""

from typing import Dict, Any, List, Optional
from .models import PatientOncologyProfile, SomaticVariant
from .agents import MTBCoordinator

coordinator = MTBCoordinator()


def create_app():
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel

        app = FastAPI(
            title="MTB-Orchestrator API",
            description="Autonomous Molecular Tumor Board & Clinical Trial Matching Automated System",
            version="1.0.0",
        )

        class AuditOncologyRequest(BaseModel):
            case_id: str
            diagnosis: str
            stage: str
            ecog_ps: int = 0
            prior_therapies: List[str] = []
            somatic_variants: List[Dict[str, Any]] = []
            tmb_mut_per_mb: Optional[float] = None
            msi_status: Optional[str] = None
            current_medications: List[str] = []

        class ChatRequest(BaseModel):
            query: str

        @app.get("/health")
        def health():
            return {"status": "HEALTHY", "system": "MTB-Orchestrator", "version": "1.0.0"}

        @app.post("/api/mtb/audit")
        def audit_case(req: AuditOncologyRequest):
            vars_objs = [
                SomaticVariant(
                    gene=v.get("gene", "EGFR"),
                    alteration=v.get("alteration", "L858R"),
                    variant_allele_freq=float(v.get("variant_allele_freq", 0.35)),
                )
                for v in req.somatic_variants
            ]
            profile = PatientOncologyProfile(
                case_id=req.case_id,
                diagnosis=req.diagnosis,
                stage=req.stage,
                ecog_ps=req.ecog_ps,
                prior_therapies=req.prior_therapies,
                somatic_variants=vars_objs,
                tmb_mut_per_mb=req.tmb_mut_per_mb,
                msi_status=req.msi_status,
                current_medications=req.current_medications,
            )
            dossier = coordinator.audit_profile(profile)
            return dossier

        @app.post("/api/chat")
        def chat(req: ChatRequest):
            return {"response": coordinator.query_assistant(req.query)}

        return app
    except ImportError:
        return None
