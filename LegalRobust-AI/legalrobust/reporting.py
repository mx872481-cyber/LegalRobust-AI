
"""Export evaluation data to JSON, CSV, and self-contained HTML."""
from __future__ import annotations
import csv
import html
import json
from pathlib import Path
from typing import Any


def export_report(report: dict[str, Any], output_dir: str | Path) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    records = report.get("records", [])
    fields = ["case_id", "jurisdiction", "legal_area", "dimension", "heuristic_score",
              "answer", "error", "flags", "judge_score", "judge_issue_types",
              "judge_rationale", "requires_human_review"]
    with (out / "cases.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for rec in records:
            row = dict(rec)
            for key in ("flags", "judge_issue_types"):
                if key in row:
                    row[key] = json.dumps(row[key], ensure_ascii=False)
            writer.writerow(row)
    summary = report.get("summary", {})
    meta = report.get("metadata", {})
    rows = []
    for rec in records:
        rows.append(
            "<tr>" + "".join([
                f"<td>{html.escape(str(rec.get('case_id','')))}</td>",
                f"<td>{html.escape(str(rec.get('jurisdiction','')))}</td>",
                f"<td>{html.escape(str(rec.get('dimension','')))}</td>",
                f"<td>{html.escape(str(rec.get('heuristic_score','')))}</td>",
                f"<td><pre>{html.escape(str(rec.get('answer','')))}</pre></td>",
                f"<td>{html.escape(str(', '.join(rec.get('flags', []))))}</td>",
                f"<td>{'Yes' if rec.get('requires_human_review') else 'No'}</td>",
            ]) + "</tr>"
        )
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LegalRobust AI Report</title><style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:2rem;color:#20242b;background:#f6f7f9}}
h1{{margin-bottom:.25rem}}.muted{{color:#606875}}.cards{{display:flex;gap:1rem;flex-wrap:wrap;margin:1.5rem 0}}
.card{{background:white;border:1px solid #e0e3e8;border-radius:12px;padding:1rem;min-width:170px}}
table{{border-collapse:collapse;background:white;width:100%;font-size:14px}}th,td{{border:1px solid #e0e3e8;padding:.65rem;vertical-align:top;text-align:left}}
th{{background:#eceff3}}pre{{white-space:pre-wrap;max-width:560px;overflow-wrap:anywhere;margin:0}}
.warning{{padding:1rem;background:#fff3d8;border:1px solid #f0d28a;border-radius:10px}}
</style></head><body><h1>LegalRobust AI</h1>
<p class="muted">Model: {html.escape(str(meta.get('target_model','unknown')))} · Created: {html.escape(str(meta.get('created_at','')))}</p>
<div class="warning"><strong>Interpretation warning:</strong> {html.escape(str(meta.get('score_warning','Scores are diagnostic only.')))} Legal accuracy and current law require authoritative source verification and human review.</div>
<div class="cards">
<div class="card"><div class="muted">Cases</div><h2>{meta.get('case_count',0)}</h2></div>
<div class="card"><div class="muted">Completed</div><h2>{meta.get('completed_count',0)}</h2></div>
<div class="card"><div class="muted">Failed API calls</div><h2>{meta.get('failed_count',0)}</h2></div>
<div class="card"><div class="muted">Mean heuristic score</div><h2>{summary.get('mean_heuristic_score','N/A')}</h2></div>
<div class="card"><div class="muted">Human review</div><h2>{summary.get('human_review_count',0)}</h2></div>
</div>
<h2>Dimension means</h2><pre>{html.escape(json.dumps(summary.get('dimension_means',{}),ensure_ascii=False,indent=2))}</pre>
<h2>Case results</h2><table><thead><tr><th>Case</th><th>Jurisdiction</th><th>Dimension</th><th>Heuristic</th><th>Target answer</th><th>Flags</th><th>Human review</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</body></html>"""
    (out / "report.html").write_text(page, encoding="utf-8")
