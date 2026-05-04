"""Core symbolic objects for Japan-VOTE.

The model mirrors the original Lisp VOTE program's style: votes are not just
labels, but decisions with stances, relations, strategies, reasons, downsides,
real votes, and scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


IMPORTANCE_ORDER = {"A": 4, "B": 3, "C": 2, "D": 1}
VALID_VOTES = {"for", "against", "abstain", "absent", "unknown"}
VALID_STANCE_SIDES = {"pro", "con"}


def importance_value(level: str | None) -> int:
    return IMPORTANCE_ORDER.get((level or "").upper(), 0)


def stronger(left: str | None, right: str | None) -> bool:
    return importance_value(left) > importance_value(right)


def weaker(left: str | None, right: str | None) -> bool:
    return importance_value(left) < importance_value(right)


def opposite_vote(vote: str | None) -> str | None:
    if vote == "for":
        return "against"
    if vote == "against":
        return "for"
    return None


def opposite_side(side: str | None) -> str | None:
    if side == "pro":
        return "con"
    if side == "con":
        return "pro"
    return None


@dataclass(frozen=True)
class Stance:
    issue_id: str
    side: str
    importance: str = "C"
    source_id: str = ""
    source_type: str = ""
    evidence: str = ""

    def __post_init__(self) -> None:
        if self.side not in VALID_STANCE_SIDES:
            raise ValueError(f"Bad stance side: {self.side}")
        if self.importance not in IMPORTANCE_ORDER:
            raise ValueError(f"Bad importance: {self.importance}")

    def flipped(self, source_id: str = "", source_type: str = "", evidence: str = "") -> "Stance":
        return Stance(
            issue_id=self.issue_id,
            side=opposite_side(self.side) or self.side,
            importance=self.importance,
            source_id=source_id or self.source_id,
            source_type=source_type or self.source_type,
            evidence=evidence or self.evidence,
        )


@dataclass(frozen=True)
class Relation:
    group_id: str
    side: str
    importance: str = "C"
    evidence: str = ""

    def __post_init__(self) -> None:
        if self.side not in VALID_STANCE_SIDES:
            raise ValueError(f"Bad relation side: {self.side}")
        if self.importance not in IMPORTANCE_ORDER:
            raise ValueError(f"Bad importance: {self.importance}")


@dataclass(frozen=True)
class Issue:
    id: str
    name_en: str
    name_ja: str
    category: str
    norm_side: str | None = None
    pro_implications: tuple[Stance, ...] = ()
    con_implications: tuple[Stance, ...] = ()


@dataclass(frozen=True)
class Group:
    id: str
    name_en: str
    name_ja: str
    type: str
    stances: tuple[Stance, ...] = ()


@dataclass(frozen=True)
class Party:
    id: str
    name_en: str
    name_ja: str
    bloc: str


@dataclass(frozen=True)
class OfficialEvidence:
    issue_id: str
    side: str
    importance: str = "C"
    vote_alignment: str = "context"
    source: str = ""
    source_url: str = ""
    api_url: str = ""
    date: str = ""
    house: str = ""
    meeting: str = ""
    speaker: str = ""
    speaker_group: str = ""
    query: str = ""
    support_cues: int = 0
    concern_cues: int = 0
    excerpt: str = ""

    def __post_init__(self) -> None:
        if self.side not in VALID_STANCE_SIDES | {"mixed"}:
            raise ValueError(f"Bad official evidence side: {self.side}")
        if self.importance not in IMPORTANCE_ORDER:
            raise ValueError(f"Bad importance: {self.importance}")
        if self.vote_alignment not in VALID_VOTES | {"context"}:
            raise ValueError(f"Bad vote alignment: {self.vote_alignment}")


@dataclass(frozen=True)
class Member:
    id: str
    name_en: str
    name_ja: str
    party: str
    district: str
    district_ja: str
    committees: tuple[str, ...] = ()
    relations: tuple[Relation, ...] = ()
    credo: tuple[Stance, ...] = ()
    vote_history: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Bill:
    id: str
    title_en: str
    title_ja: str
    date: str
    chamber: str
    sponsor: str
    committee: str
    salience: str
    issues: tuple[str, ...]
    stance_for: tuple[Stance, ...] = ()
    stance_against: tuple[Stance, ...] = ()
    party_positions: dict[str, str] = field(default_factory=dict)
    real_votes: dict[str, str] = field(default_factory=dict)
    coalition_position: str | None = None
    opposition_position: str | None = None
    committee_recommendation: str | None = None
    local_impacts: dict[str, dict[str, str]] = field(default_factory=dict)
    technical: bool = False
    rights_or_constitutional: bool = False
    evidence: str = ""
    official_evidence: tuple[OfficialEvidence, ...] = ()


@dataclass
class EvidenceMatch:
    vote: str
    bill_stance: Stance
    evidence_stance: Stance
    source_label_en: str
    source_label_ja: str

    @property
    def importance(self) -> str:
        left = self.bill_stance.importance
        right = self.evidence_stance.importance
        return left if importance_value(left) <= importance_value(right) else right


@dataclass
class StrategyResult:
    applies: bool
    vote: str | None = None
    reasons: list[EvidenceMatch] = field(default_factory=list)
    downside: list[EvidenceMatch] = field(default_factory=list)
    note_en: str = ""
    note_ja: str = ""


@dataclass
class Decision:
    member_id: str
    bill_id: str
    predicted_vote: str | None
    real_vote: str | None
    strategy: str
    strategy_name_en: str
    strategy_name_ja: str
    meta_strategy: str
    meta_strategy_name_en: str
    meta_strategy_name_ja: str
    reasons: list[EvidenceMatch]
    downside: list[EvidenceMatch]
    metrics: dict[str, Any]
    trace: list[str]
    explanation_en: str = ""
    explanation_ja: str = ""
    strategy_note_en: str = ""
    strategy_note_ja: str = ""
    score: int | None = None


@dataclass(frozen=True)
class DataSet:
    issues: dict[str, Issue]
    groups: dict[str, Group]
    parties: dict[str, Party]
    members: dict[str, Member]
    bills: dict[str, Bill]
    ruling_coalition: tuple[str, ...]
    opposition_bloc: tuple[str, ...]
