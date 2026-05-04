"""Pull a small systematic evidence sample from the NDL Kokkai API.

The curated Japan-VOTE dataset is kept stable for grading. This script adds an
optional official-data path: it queries National Diet Library speech records,
extracts short issue-relevant snippets, and writes a structured evidence file
that can be inspected or folded into future dataset revisions.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ENDPOINT = "https://kokkai.ndl.go.jp/api/speech"
DEFAULT_JSON = Path("ndl_sample_evidence.json")
DEFAULT_MARKDOWN = Path("ndl_sample_evidence.md")

ISSUE_QUERIES = {
    "digital_governance": ["デジタル", "行政データ", "データ利活用"],
    "privacy": ["個人情報", "プライバシー"],
    "national_security": ["安全保障", "防衛協力"],
    "family_support": ["子育て", "こども政策"],
    "nuclear_safety": ["原子力", "原発", "避難計画"],
    "agriculture_support": ["農業", "農家支援", "食料安全保障"],
}

SUPPORT_CUES = (
    "賛成",
    "推進",
    "支援",
    "促進",
    "強化",
    "必要",
    "重要",
    "進める",
    "整備",
)

CONCERN_CUES = (
    "反対",
    "懸念",
    "問題",
    "慎重",
    "危険",
    "リスク",
    "不十分",
    "見直し",
    "課題",
)


@dataclass(frozen=True)
class SpeechEvidence:
    issue_id: str
    query: str
    stance_side: str
    importance: str
    support_cues: int
    concern_cues: int
    date: str
    house: str
    meeting: str
    speaker: str
    speaker_group: str
    excerpt: str
    speech_url: str
    api_url: str


def classify_stance_text(text: str) -> tuple[str, str, int, int]:
    """Classify deliberation text by transparent cue counting."""
    support = sum(text.count(cue) for cue in SUPPORT_CUES)
    concern = sum(text.count(cue) for cue in CONCERN_CUES)

    if support > concern:
        side = "pro"
    elif concern > support:
        side = "con"
    else:
        side = "mixed"

    importance = "B" if max(support, concern) >= 2 else "C"
    return side, importance, support, concern


def normalize_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("speechRecord", [])
    if isinstance(records, dict):
        return [records]
    if isinstance(records, list):
        return records
    return []


def short_excerpt(text: str, query: str, limit: int = 140) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned

    index = cleaned.find(query)
    if index < 0:
        return cleaned[: limit - 1] + "..."

    half = max(10, limit // 2)
    start = max(0, index - half)
    end = min(len(cleaned), start + limit)
    snippet = cleaned[start:end]
    if start > 0:
        snippet = "..." + snippet[3:]
    if end < len(cleaned):
        snippet = snippet[:-3] + "..."
    return snippet


def text_field(record: dict[str, Any], key: str) -> str:
    value = record.get(key, "")
    return "" if value is None else str(value)


def build_url(
    query: str,
    *,
    house: str,
    limit: int,
    from_date: str | None = None,
    until_date: str | None = None,
) -> str:
    params = {
        "any": query,
        "nameOfHouse": house,
        "maximumRecords": str(limit),
        "recordPacking": "json",
    }
    if from_date:
        params["from"] = from_date
    if until_date:
        params["until"] = until_date
    return f"{API_ENDPOINT}?{urlencode(params)}"


def fetch_json(url: str, timeout: float) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "Japan-VOTE course project evidence ingester"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
    return json.loads(body.decode("utf-8"))


def evidence_from_record(issue_id: str, query: str, record: dict[str, Any], api_url: str) -> SpeechEvidence:
    speech = str(record.get("speech", ""))
    side, importance, support, concern = classify_stance_text(speech)
    return SpeechEvidence(
        issue_id=issue_id,
        query=query,
        stance_side=side,
        importance=importance,
        support_cues=support,
        concern_cues=concern,
        date=text_field(record, "date"),
        house=text_field(record, "nameOfHouse"),
        meeting=text_field(record, "nameOfMeeting"),
        speaker=text_field(record, "speaker"),
        speaker_group=text_field(record, "speakerGroup"),
        excerpt=short_excerpt(speech, query),
        speech_url=text_field(record, "speechURL"),
        api_url=api_url,
    )


def collect_evidence(
    issues: list[str],
    *,
    house: str,
    limit: int,
    keywords_per_issue: int,
    sleep_seconds: float,
    timeout: float,
    from_date: str | None,
    until_date: str | None,
) -> dict[str, Any]:
    all_items: list[SpeechEvidence] = []
    requests: list[dict[str, Any]] = []

    for issue_id in issues:
        queries = ISSUE_QUERIES.get(issue_id)
        if not queries:
            raise ValueError(f"Unknown issue id for NDL ingest: {issue_id}")

        for query in queries[:keywords_per_issue]:
            url = build_url(query, house=house, limit=limit, from_date=from_date, until_date=until_date)
            payload = fetch_json(url, timeout)
            records = normalize_records(payload)
            requests.append(
                {
                    "issue_id": issue_id,
                    "query": query,
                    "api_url": url,
                    "number_of_records": payload.get("numberOfRecords", len(records)),
                    "returned_records": len(records),
                }
            )
            all_items.extend(evidence_from_record(issue_id, query, record, url) for record in records)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    return {
        "metadata": {
            "source": "National Diet Library Kokkai API",
            "endpoint": API_ENDPOINT,
            "house": house,
            "limit_per_query": limit,
            "keywords_per_issue": keywords_per_issue,
            "from_date": from_date,
            "until_date": until_date,
            "note": "Speech evidence only. This is not a complete roll-call vote source.",
        },
        "requests": requests,
        "evidence": [item.__dict__ for item in all_items],
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, data: dict[str, Any]) -> None:
    lines = [
        "# NDL API Evidence Sample",
        "",
        "This file is generated by `ndl_ingest.py` from the National Diet Library Kokkai API.",
        "It is a systematic speech-evidence sample, not a complete source of recorded roll-call votes.",
        "",
        "## Request Summary",
        "",
        "| Issue | Query | Returned | API URL |",
        "| --- | --- | ---: | --- |",
    ]
    for request in data["requests"]:
        lines.append(
            "| {issue_id} | {query} | {returned_records} | {api_url} |".format(
                issue_id=request["issue_id"],
                query=request["query"],
                returned_records=request["returned_records"],
                api_url=request["api_url"],
            )
        )

    lines.extend(
        [
            "",
            "## Parsed Evidence",
            "",
            "| Issue | Date | Speaker | Group | Stance | Cues | Excerpt | Source |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in data["evidence"]:
        cues = f"+{item['support_cues']} / -{item['concern_cues']}"
        source = item["speech_url"] or item["api_url"]
        excerpt = item["excerpt"].replace("|", " ")
        lines.append(
            "| {issue_id} | {date} | {speaker} | {speaker_group} | {stance_side}/{importance} | {cues} | {excerpt} | {source} |".format(
                issue_id=item["issue_id"],
                date=item["date"],
                speaker=item["speaker"],
                speaker_group=item["speaker_group"],
                stance_side=item["stance_side"],
                importance=item["importance"],
                cues=cues,
                excerpt=excerpt,
                source=source,
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pull NDL Kokkai speech evidence for Japan-VOTE.")
    parser.add_argument(
        "--issues",
        default="digital_governance,privacy,national_security,family_support,nuclear_safety,agriculture_support",
        help="Comma-separated issue ids to query.",
    )
    parser.add_argument("--house", default="参議院", help="House name, for example 参議院 or 衆議院.")
    parser.add_argument("--limit", type=int, default=2, help="Maximum speech records per query.")
    parser.add_argument("--keywords-per-issue", type=int, default=1, help="How many query keywords to use per issue.")
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds to pause between API requests.")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP request timeout in seconds.")
    parser.add_argument("--from-date", default=None, help="Optional YYYY-MM-DD start date.")
    parser.add_argument("--until-date", default=None, help="Optional YYYY-MM-DD end date.")
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MARKDOWN)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    issues = [issue.strip() for issue in args.issues.split(",") if issue.strip()]
    if args.limit < 1 or args.limit > 100:
        raise ValueError("--limit must be between 1 and 100 for the NDL speech endpoint")
    if args.keywords_per_issue < 1:
        raise ValueError("--keywords-per-issue must be at least 1")

    data = collect_evidence(
        issues,
        house=args.house,
        limit=args.limit,
        keywords_per_issue=args.keywords_per_issue,
        sleep_seconds=args.sleep,
        timeout=args.timeout,
        from_date=args.from_date,
        until_date=args.until_date,
    )
    write_json(args.output_json, data)
    write_markdown(args.output_md, data)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    print(f"Parsed {len(data['evidence'])} speech evidence records")


if __name__ == "__main__":
    main()
