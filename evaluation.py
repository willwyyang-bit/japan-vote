"""Evaluate Japan-VOTE predictions against curated recorded votes."""

from __future__ import annotations

from collections import defaultdict

from data_loader import load_data
from reasoner import decide


def main() -> None:
    data = load_data()
    rows = []
    for bill in data.bills.values():
        for member_id, real_vote in bill.real_votes.items():
            if real_vote not in {"for", "against"}:
                continue
            decision = decide(data, member_id, bill.id)
            if decision.predicted_vote not in {"for", "against"}:
                correct = 0
            else:
                correct = int(decision.predicted_vote == real_vote)
            rows.append((bill.id, member_id, data.members[member_id].party, decision.strategy, correct))

    print_summary("Overall", rows)
    print_breakdown("By bill", rows, key_index=0)
    print_breakdown("By party", rows, key_index=2)
    print_breakdown("By strategy", rows, key_index=3)


def print_summary(title: str, rows) -> None:
    correct = sum(row[4] for row in rows)
    total = len(rows)
    pct = correct / total if total else 0.0
    print(f"{title}: {correct}/{total} = {pct:.1%}")


def print_breakdown(title: str, rows, key_index: int) -> None:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[key_index]].append(row)
    print(f"\n{title}:")
    for key in sorted(grouped):
        group = grouped[key]
        correct = sum(row[4] for row in group)
        total = len(group)
        print(f"  {key:32} {correct:2}/{total:<2} {correct / total:.1%}")


if __name__ == "__main__":
    main()
