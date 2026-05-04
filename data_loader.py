"""Load and validate the curated Japan-VOTE dataset."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models import Bill, DataSet, Group, Issue, Member, OfficialEvidence, Party, Relation, Stance, VALID_VOTES


DEFAULT_DATA_PATH = Path(__file__).with_name("japan_vote_data.json")


def _stance(raw: dict[str, Any], source_id: str = "", source_type: str = "") -> Stance:
    return Stance(
        issue_id=raw["issue_id"],
        side=raw["side"],
        importance=raw.get("importance", "C"),
        source_id=raw.get("source_id", source_id),
        source_type=raw.get("source_type", source_type),
        evidence=raw.get("evidence", ""),
    )


def _relation(raw: dict[str, Any]) -> Relation:
    return Relation(
        group_id=raw["group_id"],
        side=raw["side"],
        importance=raw.get("importance", "C"),
        evidence=raw.get("evidence", ""),
    )


def _official_evidence(raw: dict[str, Any]) -> OfficialEvidence:
    return OfficialEvidence(
        issue_id=raw["issue_id"],
        side=raw.get("side", "mixed"),
        importance=raw.get("importance", "C"),
        vote_alignment=raw.get("vote_alignment", "context"),
        source=raw.get("source", ""),
        source_url=raw.get("source_url", ""),
        api_url=raw.get("api_url", ""),
        date=raw.get("date", ""),
        house=raw.get("house", ""),
        meeting=raw.get("meeting", ""),
        speaker=raw.get("speaker", ""),
        speaker_group=raw.get("speaker_group", ""),
        query=raw.get("query", ""),
        support_cues=int(raw.get("support_cues", 0)),
        concern_cues=int(raw.get("concern_cues", 0)),
        excerpt=raw.get("excerpt", ""),
    )


def load_data(path: str | Path = DEFAULT_DATA_PATH) -> DataSet:
    data_path = Path(path)
    raw = json.loads(data_path.read_text(encoding="utf-8"))

    issues = {
        item["id"]: Issue(
            id=item["id"],
            name_en=item["name_en"],
            name_ja=item["name_ja"],
            category=item["category"],
            norm_side=item.get("norm_side"),
            pro_implications=tuple(_stance(s, item["id"], "issue") for s in item.get("pro_implications", [])),
            con_implications=tuple(_stance(s, item["id"], "issue") for s in item.get("con_implications", [])),
        )
        for item in raw["issues"]
    }

    groups = {
        item["id"]: Group(
            id=item["id"],
            name_en=item["name_en"],
            name_ja=item["name_ja"],
            type=item["type"],
            stances=tuple(_stance(s, item["id"], "group") for s in item.get("stances", [])),
        )
        for item in raw["groups"]
    }

    parties = {
        item["id"]: Party(
            id=item["id"],
            name_en=item["name_en"],
            name_ja=item["name_ja"],
            bloc=item["bloc"],
        )
        for item in raw["parties"]
    }

    members = {
        item["id"]: Member(
            id=item["id"],
            name_en=item["name_en"],
            name_ja=item["name_ja"],
            party=item["party"],
            district=item["district"],
            district_ja=item["district_ja"],
            committees=tuple(item.get("committees", [])),
            relations=tuple(_relation(r) for r in item.get("relations", [])),
            credo=tuple(_stance(s, item["id"], "member") for s in item.get("credo", [])),
            vote_history=dict(item.get("vote_history", {})),
        )
        for item in raw["members"]
    }

    bills = {
        item["id"]: Bill(
            id=item["id"],
            title_en=item["title_en"],
            title_ja=item["title_ja"],
            date=item["date"],
            chamber=item["chamber"],
            sponsor=item["sponsor"],
            committee=item["committee"],
            salience=item["salience"],
            issues=tuple(item.get("issues", [])),
            stance_for=tuple(_stance(s, item["id"], "bill") for s in item.get("stance_for", [])),
            stance_against=tuple(_stance(s, item["id"], "bill") for s in item.get("stance_against", [])),
            party_positions=dict(item.get("party_positions", {})),
            real_votes=dict(item.get("real_votes", {})),
            coalition_position=item.get("coalition_position"),
            opposition_position=item.get("opposition_position"),
            committee_recommendation=item.get("committee_recommendation"),
            local_impacts=dict(item.get("local_impacts", {})),
            technical=bool(item.get("technical", False)),
            rights_or_constitutional=bool(item.get("rights_or_constitutional", False)),
            evidence=item.get("evidence", ""),
            official_evidence=tuple(_official_evidence(e) for e in item.get("official_evidence", [])),
        )
        for item in raw["bills"]
    }

    dataset = DataSet(
        issues=issues,
        groups=groups,
        parties=parties,
        members=members,
        bills=bills,
        ruling_coalition=tuple(raw["metadata"]["ruling_coalition"]),
        opposition_bloc=tuple(raw["metadata"]["opposition_bloc"]),
    )
    validate_data(dataset)
    return dataset


def validate_data(data: DataSet) -> None:
    for member in data.members.values():
        if member.party not in data.parties:
            raise ValueError(f"{member.id} has unknown party {member.party}")
        for committee in member.committees:
            if not committee:
                raise ValueError(f"{member.id} has an empty committee id")
        for relation in member.relations:
            if relation.group_id not in data.groups:
                raise ValueError(f"{member.id} has unknown group relation {relation.group_id}")
        for stance in member.credo:
            _check_issue(data, stance.issue_id, f"{member.id} credo")
        for bill_id, vote in member.vote_history.items():
            if bill_id not in data.bills:
                raise ValueError(f"{member.id} vote history references unknown bill {bill_id}")
            if vote not in VALID_VOTES:
                raise ValueError(f"{member.id} vote history has bad vote {vote}")

    for group in data.groups.values():
        for stance in group.stances:
            _check_issue(data, stance.issue_id, f"{group.id} stance")

    for bill in data.bills.values():
        for issue_id in bill.issues:
            _check_issue(data, issue_id, f"{bill.id} issues")
        for stance in bill.stance_for + bill.stance_against:
            _check_issue(data, stance.issue_id, f"{bill.id} stances")
        for evidence in bill.official_evidence:
            _check_issue(data, evidence.issue_id, f"{bill.id} official evidence")
        for party_id, vote in bill.party_positions.items():
            if party_id not in data.parties:
                raise ValueError(f"{bill.id} references unknown party {party_id}")
            if vote not in VALID_VOTES:
                raise ValueError(f"{bill.id} has bad party vote {vote}")
        for member_id, vote in bill.real_votes.items():
            if member_id not in data.members:
                raise ValueError(f"{bill.id} references unknown member {member_id}")
            if vote not in VALID_VOTES:
                raise ValueError(f"{bill.id} has bad real vote {vote}")


def _check_issue(data: DataSet, issue_id: str, where: str) -> None:
    if issue_id not in data.issues:
        raise ValueError(f"{where} references unknown issue {issue_id}")
