"""Fold generated NDL speech evidence into the curated Japan-VOTE dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_DATASET = Path("japan_vote_data.json")
DEFAULT_EVIDENCE = Path("ndl_sample_evidence.json")


def vote_alignment(bill: dict[str, Any], issue_id: str, side: str) -> str:
    if side not in {"pro", "con"}:
        return "context"
    for stance in bill.get("stance_for", []):
        if stance.get("issue_id") == issue_id and stance.get("side") == side:
            return "for"
    for stance in bill.get("stance_against", []):
        if stance.get("issue_id") == issue_id and stance.get("side") == side:
            return "against"
    return "context"


def convert_item(item: dict[str, Any], bill: dict[str, Any]) -> dict[str, Any]:
    source_url = item.get("speech_url") or item.get("api_url", "")
    return {
        "issue_id": item["issue_id"],
        "side": item.get("stance_side", "mixed"),
        "importance": item.get("importance", "C"),
        "vote_alignment": vote_alignment(bill, item["issue_id"], item.get("stance_side", "mixed")),
        "source": "National Diet Library Kokkai API",
        "source_url": source_url,
        "api_url": item.get("api_url", ""),
        "date": item.get("date", ""),
        "house": item.get("house", ""),
        "meeting": item.get("meeting", ""),
        "speaker": item.get("speaker", ""),
        "speaker_group": item.get("speaker_group", ""),
        "query": item.get("query", ""),
        "support_cues": item.get("support_cues", 0),
        "concern_cues": item.get("concern_cues", 0),
        "excerpt": item.get("excerpt", ""),
    }


def enrich(dataset_path: Path, evidence_path: Path) -> dict[str, int]:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    items = evidence.get("evidence", [])
    inserted = 0
    touched_bills = 0

    for bill in dataset["bills"]:
        bill_issues = set(bill.get("issues", []))
        for stance in bill.get("stance_for", []) + bill.get("stance_against", []):
            bill_issues.add(stance.get("issue_id"))
        official = [convert_item(item, bill) for item in items if item.get("issue_id") in bill_issues]
        bill["official_evidence"] = official
        if official:
            touched_bills += 1
            inserted += len(official)

    dataset_path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"bills": touched_bills, "evidence_items": inserted}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich japan_vote_data.json with generated NDL evidence.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = enrich(args.dataset, args.evidence)
    print(f"Enriched {result['bills']} bills with {result['evidence_items']} official evidence items")


if __name__ == "__main__":
    main()
