import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from mtb_orchestrator.models import PatientOncologyProfile, SomaticVariant, VariantTier
from mtb_orchestrator.agents import (
    GenomicVariantTriageAgent,
    TrialMatchingAgent,
    DrugInteractionAgent,
    MTBCoordinator,
)
from mtb_orchestrator.cli import main


def test_genomic_variant_triage():
    agent = GenomicVariantTriageAgent()
    profile = PatientOncologyProfile(
        case_id="C-01",
        diagnosis="Colorectal Cancer",
        stage="Stage IV",
        ecog_ps=0,
        somatic_variants=[
            SomaticVariant("BRAF", "V600E", 0.40),
            SomaticVariant("APC", "R1450*", 0.50),
        ],
        tmb_mut_per_mb=15.0,
        msi_status="MSI-H",
    )
    res = agent.evaluate(profile)
    assert len(res["tier_1"]) >= 3  # BRAF V600E, TMB-H, MSI-H
    assert any("Encorafenib" in "".join(t["therapies"]) or "Dabrafenib" in "".join(t["therapies"]) for t in res["tier_1"])


def test_trial_matching():
    agent = TrialMatchingAgent()
    profile = PatientOncologyProfile(
        case_id="C-02",
        diagnosis="NSCLC",
        stage="Stage IV",
        ecog_ps=1,
        somatic_variants=[SomaticVariant("KRAS", "G12C", 0.35)],
    )
    trials = agent.evaluate(profile)
    assert len(trials) >= 1
    assert any("KRAS G12C" in "".join(t["matched_biomarkers"]) for t in trials)


def test_drug_interaction():
    agent = DrugInteractionAgent()
    warnings = agent.evaluate(
        current_meds=["Pantoprazole 40mg", "Carbamazepine 200mg"],
        prospective_therapies=["Sotorasib 960mg daily"],
    )
    assert len(warnings) >= 2  # PPI warning + CYP3A4 warning


def test_mtb_coordinator():
    coord = MTBCoordinator()
    profile = PatientOncologyProfile(
        case_id="C-03",
        diagnosis="Metastatic Breast Cancer",
        stage="Stage IV",
        ecog_ps=0,
        somatic_variants=[SomaticVariant("BRCA1", "Pathogenic", 0.48)],
    )
    dossier = coord.audit_profile(profile)
    assert len(dossier["tier_I_variants"]) >= 1
    assert "Olaparib" in "".join(dossier["tier_I_variants"][0]["therapies"])

    ans = coord.query_assistant("What are the KRAS G12C inhibitors?")
    assert "Sotorasib" in ans


def test_cli():
    assert main(["audit"]) == 0
    assert main(["chat", "What", "is", "Osimertinib?"]) == 0
