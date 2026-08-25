"""
CLI for MTB-Orchestrator.
"""

import argparse
import json
import sys
from .models import PatientOncologyProfile, SomaticVariant
from .agents import MTBCoordinator


def get_sample_nsclc_profile() -> PatientOncologyProfile:
    return PatientOncologyProfile(
        case_id="MTB-2026-0042",
        diagnosis="Metastatic Non-Small Cell Lung Cancer (Adenocarcinoma)",
        stage="Stage IVB (Brain & Bone metastases)",
        ecog_ps=1,
        prior_therapies=["Carboplatin + Pemetrexed (4 cycles)"],
        somatic_variants=[
            SomaticVariant("KRAS", "G12C", variant_allele_freq=0.42),
            SomaticVariant("TP53", "R273H", variant_allele_freq=0.38),
        ],
        tmb_mut_per_mb=12.4,
        msi_status="MSS",
        current_medications=["Omeprazole 20mg daily", "Dexamethasone 2mg daily", "Amlodipine 5mg daily"],
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="mtb-orchestrator",
        description="Autonomous Molecular Tumor Board & Clinical Trial Matching Automated System.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Generate Molecular Tumor Board briefing dossier")
    audit_parser.add_argument("-p", "--profile-json", default=None, help="Path to profile JSON")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Query air-gapped oncology knowledge assistant")
    chat_parser.add_argument("query", nargs="+", help="Natural language query")

    # Sample command
    sample_parser = subparsers.add_parser("sample", help="Export sample oncology patient profile JSON")
    sample_parser.add_argument("-o", "--output", default=None, help="Output file path")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Launch FastAPI REST server")
    serve_parser.add_argument("--port", type=int, default=8003, help="Port")

    args = parser.parse_args(argv)
    coordinator = MTBCoordinator()

    if args.command == "sample":
        p = get_sample_nsclc_profile()
        p_dict = {
            "case_id": p.case_id,
            "diagnosis": p.diagnosis,
            "stage": p.stage,
            "ecog_ps": p.ecog_ps,
            "prior_therapies": p.prior_therapies,
            "somatic_variants": [
                {
                    "gene": v.gene,
                    "alteration": v.alteration,
                    "variant_allele_freq": v.variant_allele_freq,
                }
                for v in p.somatic_variants
            ],
            "tmb_mut_per_mb": p.tmb_mut_per_mb,
            "msi_status": p.msi_status,
            "current_medications": p.current_medications,
        }
        json_str = json.dumps(p_dict, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_str)
            print(f"Sample profile written to: {args.output}")
        else:
            print(json_str)
        return 0

    if args.command == "audit":
        if args.profile_json:
            with open(args.profile_json, "r", encoding="utf-8") as f:
                d = json.load(f)
            p = PatientOncologyProfile(
                case_id=d["case_id"],
                diagnosis=d["diagnosis"],
                stage=d["stage"],
                ecog_ps=d.get("ecog_ps", 0),
                prior_therapies=d.get("prior_therapies", []),
                somatic_variants=[
                    SomaticVariant(
                        gene=v["gene"],
                        alteration=v["alteration"],
                        variant_allele_freq=float(v["variant_allele_freq"]),
                    )
                    for v in d.get("somatic_variants", [])
                ],
                tmb_mut_per_mb=d.get("tmb_mut_per_mb"),
                msi_status=d.get("msi_status"),
                current_medications=d.get("current_medications", []),
            )
        else:
            p = get_sample_nsclc_profile()

        dossier = coordinator.audit_profile(p)

        print("=" * 80)
        print(f"  MOLECULAR TUMOR BOARD BRIEFING DOSSIER: {dossier['case_id']}")
        print(f"  Diagnosis: {dossier['diagnosis']} ({dossier['stage']}) | ECOG PS: {dossier['ecog_ps']}")
        print("=" * 80)

        print("\n[TIER I: FDA-APPROVED / NCCN ACTIONABLE TARGETS]")
        for v in dossier["tier_I_variants"]:
            print(f"  • {v['gene']} {v['alteration']} (VAF: {v['vaf_pct']}) -> Therapies: {', '.join(v['therapies'])}")

        if dossier["tier_II_variants"]:
            print("\n[TIER II: INVESTIGATIONAL / VUS ALTERATIONS]")
            for v in dossier["tier_II_variants"]:
                print(f"  • {v['gene']} {v['alteration']} (VAF: {v['vaf_pct']})")

        print(f"\n[MATCHED CLINICAL TRIALS ({len(dossier['matched_clinical_trials'])})]")
        for t in dossier["matched_clinical_trials"]:
            print(f"  • [{t['nct_id']}] ({t['phase']}) {t['title']}")

        if dossier["drug_safety_warnings"]:
            print("\n[DRUG-DRUG & SAFETY INTERACTIONS]")
            for w in dossier["drug_safety_warnings"]:
                print(f"  ⚠️  {w}")

        print("\n[MTB CONSENSUS RECOMMENDATION]")
        print(f"  {dossier['consensus_recommendation']}")

        print("\n" + "=" * 80)
        return 0

    if args.command == "chat":
        ans = coordinator.query_assistant(" ".join(args.query))
        print(f"\n[MTB-Orchestrator Assistant]:\n{ans}\n")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
