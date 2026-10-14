
"""Run test cases against a target model and assemble results."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from .client import ChatClient
from .scoring import heuristic_score, judge_answer


def run_evaluation(cases: list[dict[str, Any]], target: ChatClient,
                   judge: bool = False, judge_client: ChatClient | None = None,
                   target_model: str | None = None) -> dict[str, Any]:
    records = []
    pair_answers: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        started = datetime.now(timezone.utc).isoformat()
        error = None
        answer = ""
        try:
            answer = target.chat([
                {"role": "system", "content": (
                    "You are being evaluated for legal reasoning. Identify the applicable jurisdiction "
                    "and relevant date, do not invent legal authorities, state material uncertainties, "
                    "ask for missing facts when needed, and distinguish general information from legal advice."
                )},
                {"role": "user", "content": case["prompt"]}
            ], temperature=0, model=target_model)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        scored = heuristic_score(case, answer)
        record = {
            "case_id": case["id"], "jurisdiction": case["jurisdiction"],
            "legal_area": case["legal_area"], "dimension": case["dimension"],
            "pair_id": case.get("pair_id"), "prompt": case["prompt"],
            "expected_behavior": case.get("expected_behavior"),
            "reference_answer": case.get("reference_answer"),
            "answer": answer, "error": error, "started_at": started,
            "requires_human_review": bool(case.get("requires_human_review", True)),
            **scored
        }
        if judge and judge_client and not error:
            try:
                record.update(judge_answer(judge_client, case, answer))
            except Exception as exc:
                record.update({"judge_score": None, "judge_error": f"{type(exc).__name__}: {exc}",
                               "judge_requires_human_review": True})
        records.append(record)
        if case.get("pair_id"):
            pair_answers.setdefault(str(case["pair_id"]), []).append(record)

    # Simple pair diagnostics: flag whether exact normalized answers are identical.
    # This is only a signal; different facts may legitimately change the legal conclusion.
    pair_summary = []
    for pair_id, items in pair_answers.items():
        if len(items) >= 2:
            normalized = [" ".join(x["answer"].lower().split()) for x in items]
            pair_summary.append({
                "pair_id": pair_id, "case_ids": [x["case_id"] for x in items],
                "identical_answer": len(set(normalized)) == 1,
                "note": "Exact-text similarity is a coarse diagnostic, not a correctness criterion."
            })
    valid_scores = [r["heuristic_score"] for r in records if r["heuristic_score"] is not None and not r["error"]]
    dimensions = {}
    for record in records:
        if record["error"]:
            continue
        dimensions.setdefault(record["dimension"], []).append(record["heuristic_score"])
    return {
        "metadata": {
            "project": "LegalRobust AI", "schema_version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "target_model": target_model or target.model,
            "case_count": len(cases), "completed_count": sum(not r["error"] for r in records),
            "failed_count": sum(bool(r["error"]) for r in records),
            "score_warning": "Heuristic score is diagnostic only, not legal correctness."
        },
        "summary": {
            "mean_heuristic_score": round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else None,
            "dimension_means": {
                k: round(sum(v) / len(v), 2) for k, v in dimensions.items() if v
            },
            "pair_diagnostics": pair_summary,
            "human_review_count": sum(1 for r in records if r["requires_human_review"])
        },
        "records": records
    }
