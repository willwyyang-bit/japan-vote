"""Goal-pressure analysis for Japan-VOTE decisions.

This layer makes the decision system more like a goal-based reasoner. A strategy
does not merely check one condition; it can inspect a ranked set of political
goals, institutional pressures, and tradeoffs before explaining why one family
of goals dominates in the current case.
"""

from __future__ import annotations

from dataclasses import dataclass

from models import importance_value


@dataclass(frozen=True)
class GoalPressure:
    goal_id: str
    name_en: str
    vote: str
    weight: int
    source: str
    reason_en: str


GOAL_NAMES = {
    "coalition_coordination": "maintaining coalition alignment and policy coordination",
    "cabinet_agenda": "advancing the cabinet's legislative agenda",
    "party_discipline": "following the party line",
    "faction_cohesion": "staying aligned with the member's voting faction",
    "committee_expertise": "deferring to committee expertise",
    "constituency_protection": "protecting district interests",
    "personal_commitment": "honoring the member's personal commitments",
    "constitutional_norm": "respecting constitutional and rights-based norms",
    "deliberative_legitimacy": "responding to official deliberative evidence",
    "evidence_balance": "balancing matched policy reasons",
}


def compute_goal_pressures(context) -> list[GoalPressure]:
    data = context.data
    member = context.member
    bill = context.bill
    metrics = context.metrics
    pressures: list[GoalPressure] = []

    if member.party in data.ruling_coalition and bill.coalition_position in {"for", "against"}:
        weight = 9 if bill.sponsor == "government" and bill.salience == "A" else 7
        pressures.append(
            GoalPressure(
                "coalition_coordination",
                GOAL_NAMES["coalition_coordination"],
                bill.coalition_position,
                weight,
                "ruling coalition",
                "the bill has a clear ruling-coalition position",
            )
        )

    if bill.sponsor == "government" and member.party in data.ruling_coalition:
        weight = {"A": 8, "B": 6, "C": 4, "D": 2}.get(bill.salience, 4)
        vote = bill.coalition_position or bill.party_positions.get(member.party)
        if vote in {"for", "against"}:
            pressures.append(
                GoalPressure(
                    "cabinet_agenda",
                    GOAL_NAMES["cabinet_agenda"],
                    vote,
                    weight,
                    "government sponsor",
                    f"the bill is a salience-{bill.salience} government bill",
                )
            )

    party_vote = bill.party_positions.get(member.party)
    if party_vote in {"for", "against"}:
        pressures.append(
            GoalPressure(
                "party_discipline",
                GOAL_NAMES["party_discipline"],
                party_vote,
                8 if bill.salience in {"A", "B"} else 6,
                data.parties[member.party].name_en,
                "the member's party has an explicit position",
            )
        )

    faction = metrics.get("faction", {})
    faction_vote = faction.get("vote")
    if faction_vote in {"for", "against"} and faction.get("peers"):
        cohesion = faction.get("cohesion", 0.0)
        pressures.append(
            GoalPressure(
                "faction_cohesion",
                GOAL_NAMES["faction_cohesion"],
                faction_vote,
                5 + min(3, int(cohesion * 4)),
                "computed faction",
                f"historical co-voting similarity gives a faction cohesion of {cohesion:.2f}",
            )
        )

    if bill.committee_recommendation in {"for", "against"} and (bill.technical or bill.committee in member.committees):
        pressures.append(
            GoalPressure(
                "committee_expertise",
                GOAL_NAMES["committee_expertise"],
                bill.committee_recommendation,
                7 if bill.committee in member.committees else 5,
                bill.committee,
                "the committee path supplies a specialized recommendation",
            )
        )

    local_impact = metrics.get("local_impact")
    if local_impact and local_impact.get("vote") in {"for", "against"}:
        pressures.append(
            GoalPressure(
                "constituency_protection",
                GOAL_NAMES["constituency_protection"],
                local_impact["vote"],
                10,
                member.district,
                local_impact.get("reason_en", "the bill has direct district consequences"),
            )
        )

    strong_credo = metrics.get("strong_credo_side")
    if strong_credo in {"for", "against"}:
        pressures.append(
            GoalPressure(
                "personal_commitment",
                GOAL_NAMES["personal_commitment"],
                strong_credo,
                9,
                member.name_en,
                "a top-importance personal stance points to this vote",
            )
        )

    normative = metrics.get("normative_side")
    if normative in {"for", "against"}:
        pressures.append(
            GoalPressure(
                "constitutional_norm",
                GOAL_NAMES["constitutional_norm"],
                normative,
                8 if bill.rights_or_constitutional else 6,
                "normative issue structure",
                "the bill activates rights, constitutional, or rule-of-law norms",
            )
        )

    official = metrics.get("official_vote_support", {})
    official_for = official.get("for", 0)
    official_against = official.get("against", 0)
    if official_for != official_against:
        vote = "for" if official_for > official_against else "against"
        margin = abs(official_for - official_against)
        pressures.append(
            GoalPressure(
                "deliberative_legitimacy",
                GOAL_NAMES["deliberative_legitimacy"],
                vote,
                min(6, 3 + margin),
                "NDL deliberation sample",
                f"official speech evidence leans {vote} by {margin} parsed item(s)",
            )
        )

    for_weight = sum(importance_value(reason.importance) for reason in context.reasons_for)
    against_weight = sum(importance_value(reason.importance) for reason in context.reasons_against)
    if for_weight != against_weight:
        vote = "for" if for_weight > against_weight else "against"
        pressures.append(
            GoalPressure(
                "evidence_balance",
                GOAL_NAMES["evidence_balance"],
                vote,
                min(7, 3 + abs(for_weight - against_weight)),
                "matched stance evidence",
                "the matched policy reasons are stronger on this side",
            )
        )

    return sorted(pressures, key=lambda item: item.weight, reverse=True)


def summarize_goal_pressures(pressures: list[GoalPressure]) -> dict:
    totals = {"for": 0, "against": 0}
    for pressure in pressures:
        if pressure.vote in totals:
            totals[pressure.vote] += pressure.weight
    leading = max(totals, key=totals.get) if any(totals.values()) else None
    return {
        "totals": totals,
        "leading_vote": leading,
        "top": pressures[:4],
    }


def pressures_for_vote(context, vote: str | None) -> list[GoalPressure]:
    return [pressure for pressure in context.metrics.get("goal_pressures", []) if pressure.vote == vote]


def opposing_pressures(context, vote: str | None) -> list[GoalPressure]:
    return [pressure for pressure in context.metrics.get("goal_pressures", []) if pressure.vote != vote]


def goal_dominates(context, goal_id: str, vote: str | None, tolerance: int = 0) -> bool:
    selected = [p for p in pressures_for_vote(context, vote) if p.goal_id == goal_id]
    if not selected:
        return False
    selected_weight = max(p.weight for p in selected)
    opposing_weight = max((p.weight for p in opposing_pressures(context, vote)), default=0)
    return selected_weight + tolerance >= opposing_weight
