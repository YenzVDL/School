"""Reproduce fixed checks on exported scenario/question pairs without a model.

Usage: python -m scripts.score_questions export.json --output checks.json
"""
import argparse
import json
from pathlib import Path
from backend.script_evaluation import evaluate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true", help="Explicitly replace an existing report file (never enabled by default)")
    args = parser.parse_args()
    data = json.loads(args.export.read_text(encoding="utf-8-sig"))
    outputs = data.get("outputs", data.get("records", {}).get("outputs"))
    if not isinstance(outputs, list):
        parser.error("Expected an experiment export with outputs or a workspace export with records.outputs")
    if any(o.get("status") in ["pending", "running", "evaluating", "interrupted"] for o in outputs):
        parser.error("Collection is incomplete. Export again after all planned outputs have finished.")
    from backend.store import now
    report = {**evaluate(outputs), 'created_at': now()}
    if data.get('job'):
        report.update(dataset_snapshot_id=data['job'].get('dataset_snapshot_id'), bank_snapshot_id=data['job'].get('bank_snapshot_id'))
    result = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        if args.output.exists() and not args.overwrite:
            parser.error('Output file already exists. Use a new versioned filename to preserve history, or explicitly pass --overwrite.')
        args.output.write_text(result + "\n", encoding="utf-8")
    else:
        print(result)


if __name__ == "__main__":
    main()
