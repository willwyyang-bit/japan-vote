"""Command-line demo for Japan-VOTE."""

from __future__ import annotations

import argparse
import sys

from data_loader import load_data
from reasoner import decide


def main() -> None:
    configure_output()
    parser = argparse.ArgumentParser(description="Japan-VOTE symbolic legislative voting demo")
    parser.add_argument("--list", action="store_true", help="List available members and bills")
    parser.add_argument("--member", help="Member id")
    parser.add_argument("--bill", help="Bill id")
    parser.add_argument("--lang", choices=["en", "ja", "both"], default="en")
    parser.add_argument("--enable-japanese", action="store_true", help="Enable Japanese explanation output")
    parser.add_argument("--trace", action="store_true", help="Show strategy trace")
    args = parser.parse_args()

    if args.lang in {"ja", "both"} and not args.enable_japanese:
        parser.error("Japanese output is disabled by default. Add --enable-japanese to use --lang ja or --lang both.")

    data = load_data()
    if args.list:
        print_inventory(data)
        return

    if not args.member or not args.bill:
        parser.error("--member and --bill are required unless --list is used")

    decision = decide(data, args.member, args.bill, trace=args.trace, enable_japanese=args.enable_japanese)
    if args.lang in {"en", "both"}:
        print(decision.explanation_en)
    if args.lang in {"ja", "both"}:
        print(decision.explanation_ja)
    if args.trace:
        print("\nTrace:")
        for item in decision.trace:
            print(f"- {item}")


def print_inventory(data) -> None:
    print("Members:")
    for member in data.members.values():
        party = data.parties[member.party]
        print(f"  {member.id:24} {member.name_en:20} ({party.name_en}, {member.district})")
    print("\nBills:")
    for bill in data.bills.values():
        print(f"  {bill.id:32} {bill.title_en}")


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    main()
