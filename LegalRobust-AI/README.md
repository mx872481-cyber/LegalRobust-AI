
# LegalRobust AI

A reproducible, multi-jurisdiction legal-LLM robustness evaluation starter project. It generates or loads test cases, calls a target model through an OpenAI-compatible Chat Completions endpoint, scores outputs with transparent heuristics and optional LLM-as-judge review, and exports JSON/CSV/HTML reports.

> **Research prototype, not legal advice or a validated legal benchmark.** Example cases are illustrative and deliberately avoid asserting jurisdiction-specific legal outcomes. For serious evaluation, use reviewed gold cases, authoritative legal sources, and qualified human adjudication.

## Features

- Multi-jurisdiction labels: jurisdiction, legal area, reference date, language, source notes.
- Test dimensions: factual perturbation, misleading premise, missing facts, citation discipline, consistency, safety boundaries.
- OpenAI-compatible target API; configure any provider exposing `POST /chat/completions`.
- Optional separate generator and judge models; can use one model for all roles, but independent models are preferable.
- Transparent baseline scoring: response presence, uncertainty/caveat signals, unsupported certainty signals, reference-answer keyword coverage, and pairwise consistency.
- Optional LLM judge with structured JSON parsing fallback.
- Reports: `report.json`, `cases.csv`, `report.html`; raw model answers are retained.
- CLI, example dataset, unit tests, no mandatory third-party runtime dependencies.

## Requirements

- Python 3.10+
- For live model calls: an API endpoint, API key, and model ID compatible with the configured Chat Completions API.
- No API key is needed to validate the project or run unit tests.

## Quick start

### 1. Create an environment

Windows PowerShell:
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Configure

Copy `.env.example` to `.env`, then set your endpoint, key and model. The CLI reads environment variables directly; it does not automatically parse `.env`, so export variables in your shell or use the optional `python-dotenv` package.

PowerShell:
```powershell
$env:LEGALROBUST_BASE_URL="https://YOUR_PROVIDER/v1"
$env:LEGALROBUST_API_KEY="YOUR_API_KEY"
$env:LEGALROBUST_MODEL="YOUR_MODEL_ID"
```

macOS/Linux:
```bash
export LEGALROBUST_BASE_URL="https://YOUR_PROVIDER/v1"
export LEGALROBUST_API_KEY="YOUR_API_KEY"
export LEGALROBUST_MODEL="YOUR_MODEL_ID"
```

The endpoint is constructed as `{BASE_URL}/chat/completions`. If your provider uses a different API shape, adapt `legalrobust/client.py`.

### 3. Run a live evaluation

```bash
python -m legalrobust.cli run \
  --input examples/cases.json \
  --output runs/demo \
  --judge false
```

This sends each case to the configured target model. It may incur provider charges. Start with a small dataset.

Optional LLM-as-judge:
```bash
python -m legalrobust.cli run --input examples/cases.json --output runs/judged --judge true
```
Set `LEGALROBUST_JUDGE_MODEL` if you want a different judge model. Judge outputs are advisory and should not be treated as ground truth.

### 4. Generate cases using a model

```bash
python -m legalrobust.cli generate \
  --count 12 \
  --jurisdictions "US,England and Wales,European Union,China mainland" \
  --output runs/generated_cases.json
```

Generation uses `LEGALROBUST_GENERATOR_MODEL` if set, otherwise `LEGALROBUST_MODEL`. Generated cases are **unverified drafts**; review before treating them as a benchmark.

### 5. Validate without an API

```bash
python -m unittest discover -s tests -v
python -m legalrobust.cli validate --input examples/cases.json
```

## Environment variables

| Variable | Purpose |
|---|---|
| `LEGALROBUST_BASE_URL` | Base URL, e.g. `https://api.example.com/v1` |
| `LEGALROBUST_API_KEY` | API key |
| `LEGALROBUST_MODEL` | Target model ID |
| `LEGALROBUST_GENERATOR_MODEL` | Optional test-case generator model |
| `LEGALROBUST_JUDGE_MODEL` | Optional judge model |
| `LEGALROBUST_TIMEOUT` | Request timeout seconds; default 90 |
| `LEGALROBUST_MAX_RETRIES` | Retry count for transient errors; default 2 |

Never commit `.env` or API keys.

## How scoring works

The baseline score is a **diagnostic heuristic, not a legal correctness score**:
- 20% response completeness
- 20% uncertainty / limitation handling
- 20% avoidance of absolute-certainty signals
- 20% reference-keyword coverage when a reference answer exists
- 20% paired consistency when a pair is available

A score can be misleading if the case or reference answer is poor. The report therefore exposes component scores and flags records as requiring review. When no reference answer exists, that component is marked unavailable and weights are renormalized. LLM-judge scores are reported separately, not silently mixed into the heuristic score.

For robustness, inspect **paired delta**: compare a base case with a minimally changed variant. Some changes legitimately alter the legal result; only use a pair when its expected relation has been reviewed.

## Supported test dimensions

- `base_question`: baseline question
- `fact_perturbation`: change a material fact and see whether the model notices
- `misleading_premise`: include a false or unverified premise
- `missing_information`: omit facts needed for a reliable answer
- `citation_discipline`: ask for authority and watch for fabricated citations
- `consistency_pair`: compare responses to paired prompts
- `safety_boundary`: requests involving deception, evidence fabrication, or evasion

## Project layout

```text
LegalRobust-AI/
  legalrobust/
    __init__.py client.py cases.py scoring.py runner.py reporting.py cli.py
  examples/cases.json
  configs/jurisdictions.json
  tests/test_core.py
  .env.example
  .gitignore
  requirements.txt
  LICENSE
```

## GitHub publishing

1. Create an empty GitHub repository named `LegalRobust-AI`.
2. Unzip this project and push the folder:
   ```bash
   git init
   git add .
   git commit -m "Initial LegalRobust AI robustness evaluation framework"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/LegalRobust-AI.git
   git push -u origin main
   ```
3. Add a README screenshot only after running the app with a real provider and redacting sensitive data.
4. Do not publish API keys, private client cases, privileged documents, or personal information.

## Limitations and responsible use

- No jurisdiction-specific legal conclusion is certified by this software.
- The starter examples are synthetic evaluation prompts, not legal authority.
- A language model judge can share the target model's biases and hallucinations.
- The heuristic does not verify statutes, cases, citations, or current law against authoritative sources.
- For production, add jurisdiction-specific gold datasets, authoritative retrieval, blinded human review, inter-rater agreement, prompt/version tracking, rate limits, privacy controls, and a formal severity taxonomy.
