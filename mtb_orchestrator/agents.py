"""
MTB-Orchestrator Distributed Component Molecular Tumor Board Hierarchy.
"""

from typing import List, Dict, Any, Optional
from .models import (
    PatientOncologyProfile,
    SomaticVariant,
    VariantTier,
    ClinicalTrialRecord,
    MTBDossier,
)

# Standard Actionable Oncology Biomarker Knowledge Base
ACTIONABLE_TARGETS = {
    ("EGFR", "L858R"): (VariantTier.TIER_I_STRONG, ["Osimertinib (1st-line)", "Afatinib"]),
    ("EGFR", "EXON 19 DEL"): (VariantTier.TIER_I_STRONG, ["Osimertinib (1st-line)", "Erlotinib"]),
    ("KRAS", "G12C"): (VariantTier.TIER_I_STRONG, ["Sotorasib", "Adagrasib"]),
    ("BRAF", "V600E"): (VariantTier.TIER_I_STRONG, ["Dabrafenib + Trametinib", "Encorafenib + Cetuximab (CRC)"]),
    ("BRCA1", "PATHOGENIC"): (VariantTier.TIER_I_STRONG, ["Olaparib", "Talazoparib", "Rucaparib"]),
    ("BRCA2", "PATHOGENIC"): (VariantTier.TIER_I_STRONG, ["Olaparib", "Niraparib"]),
    ("PIK3CA", "H1047R"): (VariantTier.TIER_I_STRONG, ["Alpelisib + Fulvestrant (HR+ Breast)"]),
    ("ERBB2", "AMPLIFICATION"): (VariantTier.TIER_I_STRONG, ["Trastuzumab Deruxtecan", "T-DM1"]),
}

# Synthetic Trial Registry
CLINICAL_TRIALS_DB = [
    ClinicalTrialRecord("NCT05012345", "Phase 2 Study of Next-Gen KRAS G12C Inhibitor + Anti-PD1 in Refractory Solid Tumors", "Phase 2", ["KRAS G12C"], ["Non-Small Cell Lung Cancer", "Colorectal"]),
    ClinicalTrialRecord("NCT04987654", "Phase 1b Dose Escalation of Novel Pan-RAF Inhibitor in BRAF V600E/K Carcinomas", "Phase 1b", ["BRAF V600E"], ["All Solid Tumors", "Melanoma", "Colorectal"]),
    ClinicalTrialRecord("NCT05234567", "Phase 3 Trial of PARP Inhibitor Maintenance in Homologous Recombination Deficient (HRD) Cancers", "Phase 3", ["BRCA1", "BRCA2", "HRD"], ["Ovarian", "Breast", "Pancreatic", "Prostate"]),
    ClinicalTrialRecord("NCT05345678", "Phase 2 Trial of Dual Checkpoint Blockade in High Tumor Mutation Burden (TMB >= 10 mut/Mb)", "Phase 2", ["TMB-H", "MSI-H"], ["All Solid Tumors"]),
]


class GenomicVariantTriageAgent:
    """
    Classifies somatic genomic variants into AMP/ASCO/CAP Tiers and matches FDA-approved therapies.
    """
    def evaluate(self, profile: PatientOncologyProfile) -> Dict[str, List[Dict[str, Any]]]:
        tier_1 = []
        tier_2 = []

        for var in profile.somatic_variants:
            gene_upper = var.gene.strip().upper()
            alt_upper = var.alteration.strip().upper()

            matched = False
            for (g, a), (tier, therapies) in ACTIONABLE_TARGETS.items():
                if g == gene_upper and (a in alt_upper or alt_upper in a):
                    var.tier = tier
                    var.targeted_therapies = therapies
                    tier_1.append({
                        "gene": gene_upper,
                        "alteration": var.alteration,
                        "vaf_pct": f"{var.variant_allele_freq * 100:.1f}%",
                        "tier": "Tier I (FDA / NCCN Strong Evidence)",
                        "therapies": therapies,
                    })
                    matched = True
                    break

            if not matched:
                tier_2.append({
                    "gene": gene_upper,
                    "alteration": var.alteration,
                    "vaf_pct": f"{var.variant_allele_freq * 100:.1f}%",
                    "tier": "Tier II (Investigational / Trial Matching Candidate)",
                    "therapies": ["Consider phase 1/2 clinical trial protocol"],
                })

        # High TMB
        if profile.tmb_mut_per_mb and profile.tmb_mut_per_mb >= 10.0:
            tier_1.append({
                "gene": "TMB-High",
                "alteration": f"{profile.tmb_mut_per_mb:.1f} mut/Mb (>=10 threshold)",
                "vaf_pct": "N/A",
                "tier": "Tier I (FDA Tumor-Agnostic Biomarker)",
                "therapies": ["Pembrolizumab (FDA-approved tumor-agnostic)"],
            })

        # MSI-High
        if profile.msi_status and "MSI-H" in profile.msi_status.upper():
            tier_1.append({
                "gene": "MSI-High / dMMR",
                "alteration": "Microsatellite Instability High",
                "vaf_pct": "N/A",
                "tier": "Tier I (FDA Tumor-Agnostic Biomarker)",
                "therapies": ["Pembrolizumab", "Dostarlimab"],
            })

        return {"tier_1": tier_1, "tier_2": tier_2}


class TrialMatchingAgent:
    """
    Matches patient's actionable genomic alterations and tumor histology against clinical trial protocols.
    """
    def evaluate(self, profile: PatientOncologyProfile) -> List[Dict[str, Any]]:
        matched_trials = []
        biomarkers = [f"{v.gene} {v.alteration}".upper() for v in profile.somatic_variants]
        biomarker_genes = [v.gene.upper() for v in profile.somatic_variants]

        if profile.tmb_mut_per_mb and profile.tmb_mut_per_mb >= 10.0:
            biomarkers.append("TMB-H")
        if profile.msi_status and "MSI-H" in profile.msi_status.upper():
            biomarkers.append("MSI-H")

        for trial in CLINICAL_TRIALS_DB:
            is_bio_match = any(
                any(tb in b or b in tb for b in biomarkers + biomarker_genes)
                for tb in trial.target_biomarkers
            )
            if is_bio_match:
                matched_trials.append({
                    "nct_id": trial.nct_id,
                    "title": trial.title,
                    "phase": trial.phase,
                    "matched_biomarkers": trial.target_biomarkers,
                    "status": trial.status,
                })

        return matched_trials


class DrugInteractionAgent:
    """
    Audits prospective targeted drug therapies against patient's current medications for CYP3A4 and toxicity interactions.
    """
    def evaluate(self, current_meds: List[str], prospective_therapies: List[str]) -> List[str]:
        warnings = []
        meds_lower = [m.lower() for m in current_meds]

        # Proton Pump Inhibitors (PPI) and KRAS/EGFR TKIs
        if any("prazole" in m or "omeprazole" in m or "pantoprazole" in m for m in meds_lower):
            if any("sotorasib" in t.lower() or "erlotinib" in t.lower() for t in prospective_therapies):
                warnings.append(
                    "PPI INTERACTION: Gastric acid suppression significantly reduces oral bioavailability of Sotorasib/Erlotinib. Consider switching to H2-blocker separated by 10 hours."
                )

        # Strong CYP3A4 inducers (e.g. Carbamazepine, Phenytoin, Rifampin, St. John's Wort)
        if any(c in m for m in meds_lower for c in ["carbamazepine", "phenytoin", "rifampin", "st. john"]):
            if any(t in "".join(prospective_therapies).lower() for t in ["osimertinib", "sotorasib", "alpelisib", "olaparib"]):
                warnings.append(
                    "CYP3A4 INDUCTION WARNING: Strong inducer co-administration markedly decreases plasma exposure of targeted TKI/PARP inhibitors. Dose adjustment or med substitution required."
                )

        return warnings


class MTBCoordinator:
    """
    Central orchestrator for Molecular Tumor Board briefing synthesis.
    """
    def __init__(self):
        self.variant_agent = GenomicVariantTriageAgent()
        self.trial_agent = TrialMatchingAgent()
        self.safety_agent = DrugInteractionAgent()
        self.case_registry: Dict[str, Dict[str, Any]] = {}

    def audit_profile(self, profile: PatientOncologyProfile) -> Dict[str, Any]:
        variant_res = self.variant_agent.evaluate(profile)
        tier_1 = variant_res["tier_1"]
        tier_2 = variant_res["tier_2"]

        matched_trials = self.trial_agent.evaluate(profile)

        # Extract prospective therapies
        prospective_therapies = []
        for t in tier_1 + tier_2:
            prospective_therapies.extend(t.get("therapies", []))

        safety_warnings = self.safety_agent.evaluate(profile.current_medications, prospective_therapies)

        # Formulate consensus brief
        if tier_1:
            best_therapies = ", ".join(tier_1[0]["therapies"])
            consensus = f"Targeted Therapy Recommended: {tier_1[0]['gene']} {tier_1[0]['alteration']} -> {best_therapies}."
        elif matched_trials:
            consensus = f"No standard Tier I therapies identified. Enrollment in clinical trial ({matched_trials[0]['nct_id']}) strongly recommended."
        else:
            consensus = "Standard-of-care systemic chemotherapy / immunotherapy continuation."

        dossier = {
            "case_id": profile.case_id,
            "diagnosis": profile.diagnosis,
            "stage": profile.stage,
            "ecog_ps": profile.ecog_ps,
            "tier_I_variants": tier_1,
            "tier_II_variants": tier_2,
            "matched_clinical_trials": matched_trials,
            "drug_safety_warnings": safety_warnings,
            "consensus_recommendation": consensus,
        }

        self.case_registry[profile.case_id] = dossier
        return dossier

    def query_assistant(self, user_query: str) -> str:
        q = user_query.strip().lower()
        if "kras" in q:
            return "KRAS G12C mutations in NSCLC are actionable with covalent switch-II pocket inhibitors (Sotorasib / Adagrasib). Combination trials with anti-PD-1 or SHP2 inhibitors are actively recruiting."
        elif "osimertinib" in q or "egfr" in q:
            return "EGFR Exon 19 del and L858R mutations: Osimertinib is standard 1st-line monotherapy or combined with chemotherapy (FLAURA2)."
        else:
            return "MTB-Orchestrator standing by. Actively indexing genomic alterations, FDA-approved precision therapies, and open clinical trials."
