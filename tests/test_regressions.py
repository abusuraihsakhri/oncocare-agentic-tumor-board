"""Regression tests for safety boundaries and synthetic-only examples."""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agents.base import AuditTrail
from agents.models import SystemTaskPayload
from agents.api import app as core_app
from mtb_orchestrator.server import create_app
from mtb_orchestrator.models import SomaticVariant, PatientOncologyProfile
from mtb_orchestrator.agents import MTBCoordinator, TrialMatchingAgent
from cli import parse_csv_bool


TOKEN = "test-only-access-token-at-least-32-characters"


def test_csv_boolean_parsing():
    assert parse_csv_bool("False") is False
    assert parse_csv_bool("0") is False
    assert parse_csv_bool("yes") is True
    with pytest.raises(ValueError):
        parse_csv_bool("nonsense")


def test_nonfinite_and_nested_identifier_rejected():
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="SYNTH", target_identifier="EXAMPLE", primary_metric=float("inf"))
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="SYNTH", target_identifier="EXAMPLE", primary_metric=4, attributes={"note": "MRN-123456"})


def test_audit_readers_cannot_alter_internal_state():
    trail = AuditTrail(secret_key="long-test-secret-key-for-tests")
    entry = trail.log("test", "worker", "TEST", {"kind": "synthetic"})
    entry["current_hash"] = "tampered"
    copied = trail.get_trail()
    copied[0]["current_hash"] = "tampered"
    assert trail.verify_integrity()


def test_core_api_fails_closed(monkeypatch):
    monkeypatch.delenv("API_ACCESS_TOKEN", raising=False)
    client = TestClient(core_app)
    payload = {"task_id":"SYNTH", "target_identifier":"SPECIMEN", "primary_metric":2}
    assert client.get("/health").status_code == 200
    assert client.get("/api/audit/logs").status_code == 503
    assert client.post("/api/audit", json=payload).status_code == 503
    monkeypatch.setenv("API_ACCESS_TOKEN", TOKEN)
    assert client.post("/api/audit", json=payload).status_code == 401
    res = client.post("/api/audit", json=payload, headers={"X-API-Key": TOKEN})
    assert res.status_code == 200, res.text
    assert res.json()["overall_urgency"] == "ROUTINE"


def test_mtb_api_validation_and_access(monkeypatch):
    app = create_app()
    assert app is not None
    client = TestClient(app)
    req = {
        "case_id":"SYNTH-01", "diagnosis":"NSCLC", "stage":"IV", "ecog_ps":1,
        "somatic_variants":[{"gene":"KRAS","alteration":"G12C","variant_allele_freq":0.35}],
    }
    monkeypatch.delenv("API_ACCESS_TOKEN", raising=False)
    assert client.post("/api/mtb/audit", json=req).status_code == 503
    monkeypatch.setenv("API_ACCESS_TOKEN", TOKEN)
    assert client.post("/api/mtb/audit", json=req).status_code == 401
    headers = {"X-API-Key":TOKEN}
    response = client.post("/api/mtb/audit", json=req, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["matched_clinical_trials"][0]["synthetic"] is True
    invalid = {**req, "somatic_variants":[{"gene":"KRAS","alteration":"G12C","variant_allele_freq":1.1}]}
    assert client.post("/api/mtb/audit", json=invalid, headers=headers).status_code == 422
    phi = {**req, "case_id":"MRN-123456"}
    assert client.post("/api/mtb/audit", json=phi, headers=headers).status_code == 422


def test_illustrative_records_are_not_real_trials_or_cross_site_drugs():
    profile = PatientOncologyProfile(
        case_id="SYNTH", diagnosis="Colorectal cancer", stage="IV", ecog_ps=1,
        somatic_variants=[SomaticVariant("BRAF","V600E",0.3)],
    )
    dossier = MTBCoordinator().audit_profile(profile)
    assert "Encorafenib" in " ".join(dossier["tier_I_variants"][0]["therapies"])
    assert "Dabrafenib" not in " ".join(dossier["tier_I_variants"][0]["therapies"])
    assert "Not a treatment recommendation" in dossier["consensus_recommendation"]
    assert all(t["nct_id"].startswith("DEMO-") for t in TrialMatchingAgent().evaluate(profile))
    off_site = PatientOncologyProfile(case_id="SYNTH", diagnosis="Breast cancer", stage="IV", ecog_ps=1,
        somatic_variants=[SomaticVariant("EGFR","L858R",0.3)])
    assert not MTBCoordinator().audit_profile(off_site)["tier_I_variants"]


def test_invalid_somatic_variant_and_performance():
    with pytest.raises(ValueError):
        SomaticVariant("KRAS", "G12C", float("nan"))
    with pytest.raises(ValueError):
        PatientOncologyProfile(case_id="X", diagnosis="NSCLC", stage="IV", ecog_ps=8)


def test_simulator_rejects_zero_iterations():
    from simulator import run_simulation
    with pytest.raises(ValueError, match="positive"):
        run_simulation(0)
