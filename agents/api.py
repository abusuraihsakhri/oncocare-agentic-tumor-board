"""
FastAPI REST API Server for Oncocare Automated Tumor Board.
"""
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from .base import AuditLogger, PHIGuard, SecurityException
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor

supervisor = SystemSupervisor(model_provider="mock")

app = FastAPI(
    title="Oncocare Automated Tumor Board API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User query for the supervisory assistant")

    @field_validator("query")
    @classmethod
    def validate_query_no_phi(cls, v: str) -> str:
        """Validate query does not contain PHI before processing."""
        try:
            PHIGuard.assert_no_phi(v)
        except SecurityException as e:
            raise ValueError(str(e))
        return v.strip()


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "oncocare-automated-tumor-board", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    try:
        dossier = supervisor.process_task(payload)
        return dossier.to_dict()
    except SecurityException as e:
        raise HTTPException(status_code=422, detail=f"Security violation: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except SecurityException as e:
        raise HTTPException(status_code=422, detail=f"Security violation: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs(limit: int = Query(default=100, ge=1, le=10000, description="Maximum number of audit entries to return")):
    trail = AuditLogger.get_trail()
    return {
        "audit_trail": trail[-limit:],
        "total_blocks": len(trail),
        "returned_count": min(limit, len(trail)),
        "verified": AuditLogger.verify_integrity()
    }
