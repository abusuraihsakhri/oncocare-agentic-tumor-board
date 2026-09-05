"""
Automated Pytest Test Suite for Oncocare Automated Tumor Board.
Domain: Clinical & Biomedical AI
Standard: CAP / CLSI / ISO Standards
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from agents.base import PHIGuard, AuditLogger, AuditTrail, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_audit_trail_signature_verification():
    """Verify that audit trail integrity check validates cryptographic signatures."""
    audit = AuditTrail(secret_key="test-key-for-unit-testing-only")

    # Log some entries
    audit.log("test_actor", "test_tier", "TEST_EVENT", {"data": "test1"})
    audit.log("test_actor", "test_tier", "TEST_EVENT", {"data": "test2"})
    audit.log("test_actor", "test_tier", "TEST_EVENT", {"data": "test3"})

    # Verify integrity passes for valid trail
    assert audit.verify_integrity() is True

    # Verify chain linkage
    assert len(audit.logs) == 3
    assert audit.logs[0]["prev_hash"] == "GENESIS_BLOCK_0000000000000000"
    assert audit.logs[1]["prev_hash"] == audit.logs[0]["current_hash"]
    assert audit.logs[2]["prev_hash"] == audit.logs[1]["current_hash"]


def test_audit_trail_tamper_detection():
    """Verify that tampering with audit entries is detected."""
    audit = AuditTrail(secret_key="test-key-for-tamper-detection")

    audit.log("actor", "tier", "EVENT", {"data": "original"})

    # Tamper with the entry
    audit.logs[0]["payload_hash"] = "tampered_hash"

    # Integrity check should fail
    assert audit.verify_integrity() is False


def test_audit_trail_secret_key_validation():
    """Verify that short or missing secret keys are rejected."""
    # Too short key
    with pytest.raises(ValueError, match="at least 16 characters"):
        AuditTrail(secret_key="short")

    # Missing key (no env var set)
    import os
    original = os.environ.pop("AUDIT_SECRET_KEY", None)
    try:
        with pytest.raises(ValueError, match="AUDIT_SECRET_KEY must be provided"):
            AuditTrail()
    finally:
        if original:
            os.environ["AUDIT_SECRET_KEY"] = original


def test_phi_guard_email_detection():
    """Verify PHI guard detects email addresses."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Contact patient at john.doe@hospital.org")


def test_phi_guard_ssn_detection():
    """Verify PHI guard detects SSN patterns."""
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient SSN: 123-45-6789")


def test_phi_redaction():
    """Verify PHI redaction works correctly."""
    text = "Patient MRN-123456 has appointment. Contact: john@email.com"
    redacted = PHIGuard.redact_phi(text)
    assert "MRN-123456" not in redacted
    assert "john@email.com" not in redacted
    assert "[REDACTED_IDENTIFIER]" in redacted
