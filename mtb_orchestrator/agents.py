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

# STATIC EDUCATIONAL EXAMPLES: not guideline-validated treatment recommendations.
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

# SYNTHETIC TRIAL EXAMPLES: not real clinical-trial registry records.
# This site map is a limited demonstration guard, not a complete indication database.
TUMOR_SITE_RULES = {
    ("EGFR", "L858R"): {"lung"},
    ("EGFR", "EXON 19 DEL"): {"lung"},
    ("KRAS", "G12C"): {"lung", "colorectal"},
    ("BRAF", "V600E"): {"melanoma", "colorectal"},
    ("BRCA1", "PATHOGENIC"): {"breast", "ovarian", "pancreatic", "prostate"},
    ("BRCA2", "PATHOGENIC"): {"breast", "ovarian", "pancreatic", "prostate"},
    ("PIK3CA", "H1047R"): {"breast"},
    ("ERBB2", "AMPLIFICATION"): {"breast"},
}


def tumor_site(diagnosis: str) -> str:
    text = diagnosis.lower()
    for label, normalized in (
        ("nsclc", "lung"), ("lung", "lung"),
        ("colorectal", "colorectal"), ("colon", "colorectal"), ("rectal", "colorectal"),
        ("melanoma", "melanoma"), ("breast", "breast"),
        ("ovarian", "ovarian"), ("ovary", "ovarian"),
        ("pancrea", "pancreatic"), ("prostat", "prostate"),
    ):
        if label in text:
            return normalized
    return "unmapped"


CLINICAL_TRIALS_DB = [
    ClinicalTrialRecord("DEMO-KRAS-001", "Phase 2 Study of Next-Gen KRAS G12C Inhibitor + Anti-PD1 in Refractory Solid Tumors", "Phase 2", ["KRAS G12C"], ["Non-Small Cell Lung Cancer", "Colorectal"]),
    ClinicalTrialRecord("DEMO-BRAF-002", "Phase 1b Dose Escalation of Novel Pan-RAF Inhibitor in BRAF V600E/K Carcinomas", "Phase 1b", ["BRAF V600E"], ["All Solid Tumors", "Melanoma", "Colorectal"]),
    ClinicalTrialRecord("DEMO-HRD-003", "Phase 3 Trial of PARP Inhibitor Maintenance in Homologous Recombination Deficient (HRD) Cancers", "Phase 3", ["BRCA1", "BRCA2", "HRD"], ["Ovarian", "Breast", "Pancreatic", "Prostate"]),
    ClinicalTrialRecord("DEMO-TMB-004", "Phase 2 Trial of Dual Checkpoint Blockade in High Tumor Mutation Burden (TMB >= 10 mut/Mb)", "Phase 2", ["TMB-H", "MSI-H"], ["All Solid Tumors"]),
]


class GenomicVariantTriageAgent:
    """
    Provides illustrative variant associations only. Does not implement formal AMP/ASCO/CAP classification.
    """
    def evaluate(self, profile: PatientOncologyProfile) -> Dict[str, List[Dict[str, Any]]]:
        tier_1 = []
        tier_2 = []

        site = tumor_site(profile.diagnosis)
        for var in profile.somatic_variants:
            gene_upper = var.gene.strip().upper()
            alt_upper = var.alteration.strip().upper()

            matched = False
            for (g, a), (tier, therapies) in ACTIONABLE_TARGETS.items():
                # Exact alteration match prevents accidental substring matches.
                if g == gene_upper and a == alt_upper and site in TUMOR_SITE_RULES.get((g, a), set()):
                    # Prevent cross-tumor regimen display for BRAF V600E.
                    local_therapies = list(therapies)
                    if (g, a) == ("BRAF", "V600E"):
                        local_therapies = (["Encorafenib + Cetuximab (CRC example)"]
                                           if site == "colorectal"
                                           else ["Dabrafenib + Trametinib (melanoma example)"])
                    var.tier = tier
                    var.targeted_therapies = local_therapies
                    tier_1.append({
                        "gene": gene_upper,
                        "alteration": var.alteration,
                        "vaf_pct": f"{var.variant_allele_freq * 100:.1f}%",
                        "tier": "Illustrative candidate (clinical evidence not verified)",
                        "therapies": local_therapies,
                    })
                    matched = True
                    break

            if not matched:
                tier_2.append({
                    "gene": gene_upper,
                    "alteration": var.alteration,
                    "vaf_pct": f"{var.variant_allele_freq * 100:.1f}%",
                    "tier": "Unclassified (no validated evidence tier)",
                    "therapies": [],
                })

        # High TMB
        if profile.tmb_mut_per_mb and profile.tmb_mut_per_mb >= 10.0:
            tier_1.append({
                "gene": "TMB-High",
                "alteration": f"{profile.tmb_mut_per_mb:.1f} mut/Mb (>=10 threshold)",
                "vaf_pct": "N/A",
                "tier": "Screening flag only; cannot establish an indication",
                "therapies": [],
            })

        # MSI-High
        if profile.msi_status and "MSI-H" in profile.msi_status.upper():
            tier_1.append({
                "gene": "MSI-High / dMMR",
                "alteration": "Microsatellite Instability High",
                "vaf_pct": "N/A",
                "tier": "Screening flag only; cannot establish an indication",
                "therapies": [],
            })

        return {"tier_1": tier_1, "tier_2": tier_2}


class TrialMatchingAgent:
    """
    Screens synthetic biomarker examples. No live trial or eligibility verification.
    """
    def evaluate(self, profile: PatientOncologyProfile) -> List[Dict[str, Any]]:
        matched_trials = []
        biomarkers = [f"{v.gene} {v.alteration}".upper() for v in profile.somatic_variants]
        biomarker_genes = [v.gene.upper() for v in profile.somatic_variants]

        if profile.tmb_mut_per_mb and profile.tmb_mut_per_mb >= 10.0:
            biomarkers.append("TMB-H")
        if profile.msi_status and "MSI-H" in profile.msi_status.upper():
            biomarkers.append("MSI-H")

        site = tumor_site(profile.diagnosis)
        for trial in CLINICAL_TRIALS_DB:
            is_bio_match = any(
                tb.upper() in biomarkers + biomarker_genes
                for tb in trial.target_biomarkers
            )
            allowed = {tumor_site(diagnosis) for diagnosis in trial.organ_sites}
            site_matches = "All Solid Tumors" in trial.organ_sites or site in allowed
            if is_bio_match and site_matches:
                matched_trials.append({
                    "nct_id": trial.nct_id,
                    "title": trial.title,
                    "phase": trial.phase,
                    "matched_biomarkers": trial.target_biomarkers,
                    "status": "SYNTHETIC — NOT VERIFIED",
                    "synthetic": True,
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
                    "POTENTIAL ACID-SUPPRESSION INTERACTION: Check drug-specific prescribing information and consult an oncology pharmacist; no substitution or timing advice is automated."
                )

        # Strong CYP3A4 inducers (e.g. Carbamazepine, Phenytoin, Rifampin, St. John's Wort)
        if any(c in m for m in meds_lower for c in ["carbamazepine", "phenytoin", "rifampin", "st. john"]):
            if any(t in "".join(prospective_therapies).lower() for t in ["osimertinib", "sotorasib", "alpelisib", "olaparib"]):
                warnings.append(
                    "POTENTIAL ENZYME-INDUCTION INTERACTION: Check current drug labeling and consult an oncology pharmacist before any medication change."
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
            consensus = f"Illustrative candidate examples for specialist review: {tier_1[0]['gene']} {tier_1[0]['alteration']} -> {best_therapies}. Not a treatment recommendation."
        elif matched_trials:
            consensus = "Only synthetic trial examples matched. Consult an up-to-date registry; no enrollment recommendation can be made."
        else:
            consensus = "No contextual treatment recommendation can be made from this example data."

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
            "limitations": "Synthetic educational lookup; no current FDA label, guideline, or trial status verification.",
        }

        self.case_registry[profile.case_id] = dossier
        return dossier

    def query_assistant(self, user_query: str) -> str:
        q = user_query.strip().lower()
        if "kras" in q:
            return "KRAS G12C mutations in NSCLC are actionable with covalent switch-II pocket inhibitors (Sotorasib / Adagrasib). Current trial enrollment is not checked in this application."
        elif "osimertinib" in q or "egfr" in q:
            return "EGFR Exon 19 del and L858R mutations: Osimertinib is standard 1st-line monotherapy or combined with chemotherapy (FLAURA2)."
        else:
            return "MTB-Orchestrator uses a static educational lookup, not live labels, guidelines, or clinical trial data."
