# Oncocare Agentic Tumor Board

An educational Python project illustrating molecular-tumor-board workflows, static biomarker examples, synthetic trial screening, medication-interaction flags, and generic quality-control rules.

**For research and teaching only. Not validated for patient diagnosis, staging, treatment selection, clinical escalation, trial enrollment, or regulated patient-data processing.**

## Browser demonstration

The standalone demonstration lives in [web/index.html](web/index.html). A GitHub Actions workflow publishes the web directory to GitHub Pages when the repository's Pages settings permit it. The published link should only be advertised after a successful deployment and live-site check.

The public page runs entirely in the browser, never sends or stores user inputs, requires no tokens, and does not generate signed audit records. Pyodide or other Python-in-browser runtimes are neither necessary nor used.

## Implemented features

- **Generic QC agent system:** Deterministic rules for primary values above 25, secondary values above 12, descriptor keywords, and a critical flag. **These are example thresholds, not medically validated cutoffs.**
- **Process-local audit trail:** HMAC-SHA256 hash chaining for generated QC entries. All records are lost on restart and no append-only durable store is provided.
- **Identifier pattern screening:** Basic detection of common MRNs, SSNs, email addresses, telephone patterns, and some labeled names. It cannot ensure PHI removal, anonymization, or HIPAA compliance.
- **Molecular example lookup:** Static variant/therapy illustrations with basic tumor-context gating, synthetic trial records prefixed DEMO-, and limited drug-interaction flags. No FDA, NCCN, AMP/ASCO/CAP, or real-time trial verification is performed.
- **Mock assistant:** Deterministic example responses. No real OpenAI, Claude, or Ollama integration is implemented.

## Install

Python 3.10+ is required.

~~~bash
git clone https://github.com/abusuraihsakhri/oncocare-agentic-tumor-board.git
cd oncocare-agentic-tumor-board
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
~~~

Generate two independent random secrets:

~~~bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
export AUDIT_SECRET_KEY="<first-generated-secret>"
export API_ACCESS_TOKEN="<second-generated-secret>"
~~~

## Use

~~~bash
# Example QC commands
python cli.py audit --primary 29.4 --secondary 14.8 --status DISCORDANT
python cli.py verify-audit

# Synthetic molecular-case report
python -m mtb_orchestrator.cli audit
python -m mtb_orchestrator.cli sample -o synthetic-profile.json

# Local QC API (health route open, other endpoints require X-API-Key)
python cli.py serve --host 127.0.0.1 --port 8000

# Separate synthetic molecular-case API
uvicorn mtb_orchestrator.server:create_app --factory --host 127.0.0.1 --port 8003

# Tests and browser demo logic
python -m pytest -q
node web/demo-tests.js
~~~

Pass the API_ACCESS_TOKEN value in the **X-API-Key** HTTP header to access API routes. The local API is intentionally separate from GitHub Pages, and the browser demo does not call it. Docker Compose binds to localhost, requires both environment secrets, and starts the core QC API with **docker compose up --build**.

## Privacy and clinical limitations

Only use synthetic or previously de-identified records. Never enter real patient names, identifiers, identifiable clinical histories, or private medication information. Pattern screening can miss identifiers. Neither the local services nor the browser example have undergone clinical validation, formal software regulatory assessment, security certification, or controlled deployment review.

Synthetic trial records are not real NCT entries; their availability and eligibility are unknown. Static therapy associations and drug warnings are not prescribing guidance. In-memory HMAC entries can help detect mutation of retained entries, but do not establish a durable tamper-proof audit record or prove completeness.

## Technology and compatibility

Python, Pydantic 2, FastAPI, Uvicorn, pytest; browser HTML, CSS and JavaScript. The static demonstration targets current Chromium, Firefox, and Safari. It loads no third-party JavaScript, fonts, or other runtime resources.

## License

[MIT](LICENSE).
