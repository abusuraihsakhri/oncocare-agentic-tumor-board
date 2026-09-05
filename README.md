# Oncocare Agentic Tumor Board

> **Domain:** Medical Oncology & Cancer Staging Systems
> **Reference Guidelines & Standards:** `AJCC Cancer Staging Manual & NCCN Clinical Practice Guidelines`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Oncocare Agentic Tumor Board** is an advanced analytical and computational platform implementing a multi-agent architecture for clinical decision support. The system provides:

- **Deterministic Calculation Engine**: Strict compliance with standard reference formulations and thresholds.
- **Risk & Urgency Classification**: Multi-tier categorization with automated clinical/operational action recommendations.
- **Validation & Guardrails**: Rigorous input bounds checking and anomaly detection.
- **Genomic Variant Triage**: AMP/ASCO/CAP tier classification with FDA-approved therapy matching.
- **Clinical Trial Matching**: Patient profile matching against trial eligibility criteria.
- **Drug Interaction Auditing**: CYP3A4 and toxicity interaction detection.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### Core Agents (`agents/`)
- **SystemSupervisor**: Master orchestrator coordinating multi-worker evaluations.
- **InvariantQCWorker**: Primary mathematical and protocol boundary auditor.
- **SafetyEscalationWorker**: Safety boundary, toxicity, and emergency interlock detection.
- **ProtocolConformanceWorker**: Spec conformance and anomaly triage.

### MTB Orchestrator (`mtb_orchestrator/`)
- **GenomicVariantTriageAgent**: Classifies somatic variants into AMP/ASCO/CAP Tiers.
- **TrialMatchingAgent**: Matches patient biomarkers against clinical trial protocols.
- **DrugInteractionAgent**: Audits prospective therapies against current medications.
- **MTBCoordinator**: Central orchestrator for Molecular Tumor Board briefing synthesis.

### Enrichment Engines (`enrichment.py`)
- **OverviewEngine**, **GoalEngine**, and 6 additional domain-specific engines.
- **OncocareagentictumorboardEnrichmentSuite**: Master coordinator executing all enrichment features.

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/oncocare-agentic-tumor-board.git
cd oncocare-agentic-tumor-board

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Set required environment variable for audit security
export AUDIT_SECRET_KEY="your-secure-minimum-16-char-key-here"
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py audit
```

### 2. Available Commands
```bash
# Run single task evaluation
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT

# Query the supervisory assistant
python cli.py chat "What is Osimertinib?"

# Batch process CSV records
python cli.py batch -i input.csv -o results.csv

# Verify HMAC audit trail integrity
python cli.py verify-audit

# Launch FastAPI REST server
python cli.py serve --host 127.0.0.1 --port 8000
```

### 3. MTB-Orchestrator Commands
```bash
# Generate Molecular Tumor Board briefing
python -m mtb_orchestrator.cli audit

# Export sample oncology profile
python -m mtb_orchestrator.cli sample -o profile.json

# Query oncology knowledge assistant
python -m mtb_orchestrator.cli chat "KRAS G12C inhibitors"
```

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition. Full signature verification on integrity checks.
* **Secure Key Management:** Audit signing key must be provided via `AUDIT_SECRET_KEY` environment variable (minimum 16 characters). No hardcoded defaults.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Required Environment Variable
```bash
export AUDIT_SECRET_KEY="your-secure-minimum-16-char-key-here"
```

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
# Set audit key for tests
export AUDIT_SECRET_KEY="test-key-for-development-only-2026"

# Run all tests
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

Run the MTB-Orchestrator CLI:

```bash
python -m mtb_orchestrator.cli audit
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
docker build -t oncocare-agentic-tumor-board .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-production-key" oncocare-agentic-tumor-board

# Or use docker-compose
AUDIT_SECRET_KEY="your-production-key" docker-compose up
```

---

## 📁 Project Structure

```
oncocare-agentic-tumor-board/
├── agents/                    # Core agent modules
│   ├── api.py                # FastAPI REST endpoints
│   ├── base.py               # Security, PHI guard, HMAC audit
│   ├── models.py             # Pydantic data models
│   ├── supervisor.py         # Master orchestrator
│   ├── workers.py            # Specialized domain workers
│   ├── llm_factory.py        # LLM provider factory
│   ├── learning.py           # Bayesian calibration engine
│   ├── metrics.py            # Prometheus metrics collector
│   └── streamer.py           # WebSocket telemetry broadcaster
├── mtb_orchestrator/          # Molecular Tumor Board modules
│   ├── agents.py             # Genomic triage, trial matching, drug interactions
│   ├── models.py             # Oncology data models
│   ├── cli.py                # MTB-specific CLI
│   └── server.py             # MTB FastAPI server
├── tests/                     # Pytest test suite
├── web/                       # Operations console (HTML/JS)
├── cli.py                     # Main CLI entry point
├── simulator.py               # High-throughput simulation
├── enrichment.py              # Domain enrichment engines
├── Dockerfile                 # Container build
├── docker-compose.yml         # Multi-container orchestration
└── pyproject.toml             # Project configuration
```

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
