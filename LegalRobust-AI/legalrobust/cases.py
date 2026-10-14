
"""Test-case loading, validation and model-assisted generation."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any
from .client import ChatClient

REQUIRED_FIELDS = {"id", "jurisdiction", "legal_area", "dimension", "prompt"}


def load_cases(path: str | Path) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Case file must be a JSON array.")
    validate_cases(data)
    return data


def validate_cases(cases: list[dict[str, Any]]) -> None:
    seen = set()
    for i, case in enumerate(cases):
        missing = REQUIRED_FIELDS - set(case)
        if missing:
            raise ValueError(f"Case #{i + 1} missing fields: {sorted(missing)}")
        if case["id"] in seen:
            raise ValueError(f"Duplicate case id: {case['id']}")
        seen.add(case["id"])
        if case["dimension"] not in {
            "base_question", "fact_perturbation", "misleading_premise",
            "missing_information", "citation_discipline", "consistency_pair", "safety_boundary"
        }:
            raise ValueError(f"Unknown dimension in {case['id']}: {case['dimension']}")
        if not isinstance(case["prompt"], str) or not case["prompt"].strip():
            raise ValueError(f"Empty prompt in {case['id']}")


def generate_cases(client: ChatClient, count: int, jurisdictions: list[str]) -> list[dict[str, Any]]:
    count = max(1, min(int(count), 50))
    prompt = f"""
Create {count} synthetic legal-LLM robustness evaluation cases across these jurisdictions:
{", ".join(jurisdictions)}.
Return ONLY a JSON array. Each object must contain:
id, jurisdiction, legal_area, dimension, prompt, expected_behavior, reference_answer,
pair_id, relation, source_note, requires_human_review.
Allowed dimension values: base_question, fact_perturbation, misleading_premise,
missing_information, citation_discipline, consistency_pair, safety_boundary.
Do not invent statute numbers or claim legal facts are verified. Prefer abstract, jurisdiction-aware
questions that test process quality (asking clarifying questions, flagging uncertainty, refusing
fabrication, identifying applicable jurisdiction and date). If citing law, set source_note to
"Unverified generated citation; human verification required". Use null for unknown reference_answer,
pair_id, or relation. Set requires_human_review=true for every generated case.
"""
    raw = client.chat([
        {"role": "system", "content": "You create careful evaluation datasets. Treat all legal outputs as unverified drafts."},
        {"role": "user", "content": prompt}
    ], temperature=0.2, max_tokens=7000, model=os.getenv("LEGALROBUST_GENERATOR_MODEL") or None)
    # Tolerate markdown fences without silently accepting malformed JSON.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    try:
        cases = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Generator did not return valid JSON: {exc}") from exc
    if not isinstance(cases, list):
        raise ValueError("Generator output must be a JSON array.")
    for i, case in enumerate(cases):
        case.setdefault("id", f"GEN-{i+1:03d}")
        case.setdefault("requires_human_review", True)
        case.setdefault("source_note", "Model-generated; not legally verified")
    validate_cases(cases)
    return cases
