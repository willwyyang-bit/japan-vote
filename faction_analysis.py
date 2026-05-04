"""Print or write a computed faction report."""

from __future__ import annotations

import argparse
from pathlib import Path

from data_loader import load_data
from factions import compute_factions, member_faction, mermaid_graph, pairwise_similarities


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute Japan-VOTE factions from voting similarity")
    parser.add_argument("--exclude-bill", help="Exclude a bill when computing factions")
    parser.add_argument("--write", help="Write a Markdown faction report to this path")
    args = parser.parse_args()

    data = load_data()
    report = build_report(data, args.exclude_bill)
    if args.write:
        Path(args.write).write_text(report, encoding="utf-8")
        print(f"Wrote {args.write}")
    else:
        print(report)


def build_report(data, exclude_bill_id: str | None = None) -> str:
    factions = compute_factions(data, exclude_bill_id)
    pairs = pairwise_similarities(data, exclude_bill_id)
    lines = [
        "# Computed Faction Report",
        "",
        "Factions are calculated from voting similarity, not entered by hand.",
        "An edge means two members agreed on at least 72% of common recorded votes with at least three common votes.",
        "",
    ]
    if exclude_bill_id:
        lines.append(f"Excluded target bill: `{exclude_bill_id}`")
        lines.append("")

    lines.append("## Factions")
    lines.append("")
    for index, faction in enumerate(factions, start=1):
        names = ", ".join(data.members[member_id].name_en for member_id in faction)
        lines.append(f"- Faction {index}: {names}")

    lines.append("")
    lines.append("## Member Faction Signals")
    lines.append("")
    for member_id, member in data.members.items():
        faction = member_faction(data, member_id, exclude_bill_id)
        lines.append(f"- {member.name_en}: {faction['id']}, cohesion={faction['cohesion']:.2f}")

    lines.append("")
    lines.append("## Strong Pairwise Similarities")
    lines.append("")
    for (left, right), (score, common) in sorted(pairs.items(), key=lambda item: item[1][0], reverse=True):
        if common >= 3 and score >= 0.72:
            lines.append(f"- {data.members[left].name_en} - {data.members[right].name_en}: {score:.2f} over {common} common votes")

    lines.append("")
    lines.append("## Mermaid Faction Plot")
    lines.append("")
    lines.append("```mermaid")
    lines.append(mermaid_graph(data, exclude_bill_id))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
