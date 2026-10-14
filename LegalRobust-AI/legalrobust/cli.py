
"""Command-line interface."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from .cases import load_cases, validate_cases, generate_cases
from .client import ChatClient
from .reporting import export_report
from .runner import run_evaluation


def _bool(value: str) -> bool:
    val = value.lower().strip()
    if val in {"true", "1", "yes", "y"}:
        return True
    if val in {"false", "0", "no", "n"}:
        return False
    raise argparse.ArgumentTypeError("Expected true or false.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="legalrobust", description="Legal LLM robustness evaluation")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="Validate a JSON test-case file")
    validate.add_argument("--input", required=True)
    gen = sub.add_parser("generate", help="Generate draft test cases using an LLM")
    gen.add_argument("--count", type=int, default=10)
    gen.add_argument("--jurisdictions", default="China mainland,United States,England and Wales,European Union")
    gen.add_argument("--output", required=True)
    run = sub.add_parser("run", help="Run evaluation against a configured model")
    run.add_argument("--input", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--judge", type=_bool, default=False)
    run.add_argument("--model", default=None, help="Override target model ID")

    args = parser.parse_args()
    if args.command == "validate":
        cases = load_cases(args.input)
        print(f"Valid: {len(cases)} cases")
        return
    if args.command == "generate":
        client = ChatClient(model=os.getenv("LEGALROBUST_GENERATOR_MODEL") or None)
        cases = generate_cases(client, args.count, [x.strip() for x in args.jurisdictions.split(",") if x.strip()])
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {len(cases)} unverified draft cases to {out}")
        return
    if args.command == "run":
        cases = load_cases(args.input)
        target = ChatClient(model=args.model)
        judge_client = None
        if args.judge:
            judge_client = ChatClient(model=os.getenv("LEGALROBUST_JUDGE_MODEL") or target.model)
        report = run_evaluation(cases, target, judge=args.judge, judge_client=judge_client, target_model=args.model)
        export_report(report, args.output)
        print(json.dumps({"metadata": report["metadata"], "summary": report["summary"]}, ensure_ascii=False, indent=2))
        print(f"Reports written to: {args.output}")
        return


if __name__ == "__main__":
    main()
