"""
oncocare-automated-tumor-board (MTB-Orchestrator): Data Models & Genomic Catalogs.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import datetime


class VariantTier(str, Enum):
    TIER_I_STRONG = "TIER_I_STRONG_CLINICAL_SIGNIFICANCE"      # FDA-approved therapy / NCCN guideline
    TIER_II_POTENTIAL = "TIER_II_POTENTIAL_SIGNIFICANCE"        # Off-label / investigational trial
    TIER_III_UNKNOWN = "TIER_III_UNKNOWN_SIGNIFICANCE"          # VUS
    TIER_IV_BENIGN = "TIER_IV_BENIGN"


@dataclass
class SomaticVariant:
    gene: str                   # e.g., "EGFR", "BRAF", "KRAS", "BRCA1", "PIK3CA"
    alteration: str             # e.g., "L858R", "V600E", "G12C", "Exon 19 del"
    variant_allele_freq: float  # e.g., 0.35 (35%)
    tier: VariantTier = VariantTier.TIER_I_STRONG
    targeted_therapies: List[str] = field(default_factory=list)  # ["Osimertinib", "Dabrafenib + Trametinib"]


@dataclass
class ClinicalTrialRecord:
    nct_id: str
    title: str
    phase: str                  # "Phase 1b", "Phase 2", "Phase 3"
    target_biomarkers: List[str]# ["KRAS G12C", "BRAF V600E", "MSI-H"]
    organ_sites: List[str]      # ["Non-Small Cell Lung Cancer", "Colorectal", "Pancreatic"]
    status: str = "RECRUITING"


@dataclass
class PatientOncologyProfile:
    case_id: str
    diagnosis: str              # e.g., "Advanced Non-Small Cell Lung Cancer (Adenocarcinoma)"
    stage: str                  # "Stage IVB"
    ecog_ps: int                # 0, 1, 2
    prior_therapies: List[str] = field(default_factory=list)  # ["Carboplatin + Pemetrexed", "Pembrolizumab"]
    somatic_variants: List[SomaticVariant] = field(default_factory=list)
    tmb_mut_per_mb: Optional[float] = None
    msi_status: Optional[str] = None  # "MSI-H", "MSS"
    current_medications: List[str] = field(default_factory=list)


@dataclass
class MTBDossier:
    case_id: str
    diagnosis: str
    tier_I_variants: List[Dict[str, Any]]
    tier_II_variants: List[Dict[str, Any]]
    matched_clinical_trials: List[Dict[str, Any]]
    drug_safety_warnings: List[str]
    consensus_recommendation: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
