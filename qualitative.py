"""Qualitative arithmetic for selecting Japan-VOTE meta-strategies.

This module replaces a purely hard-coded meta-strategy cascade with a small
symbolic scoring model. Scores are still interpretable: each meta-strategy gets
qualitative evidence from bill features, member features, and relational signals.
"""

from __future__ import annotations


POINTS = {
    "none": 0,
    "weak": 1,
    "medium": 2,
    "strong": 3,
}


def qadd(*levels: str) -> int:
    return sum(POINTS.get(level, 0) for level in levels)


def qlevel(score: int) -> str:
    if score >= 6:
        return "strong"
    if score >= 3:
        return "medium"
    if score >= 1:
        return "weak"
    return "none"


def bill_salience_level(bill) -> str:
    return {"A": "strong", "B": "medium", "C": "weak", "D": "none"}.get(bill.salience, "none")


def feature_levels(context) -> dict[str, str]:
    bill = context.bill
    member = context.member
    metrics = context.metrics
    faction = metrics.get("faction", {})
    official_count = metrics.get("official_evidence_count", 0)
    official_cues = metrics.get("official_cue_strength", 0)

    return {
        "government": "strong" if bill.sponsor == "government" else "weak" if bill.sponsor == "committee" else "none",
        "salience": bill_salience_level(bill),
        "coalition": "strong" if member.party in context.data.ruling_coalition and bill.coalition_position else "none",
        "party": "strong" if metrics.get("party_position") in {"for", "against"} else "none",
        "committee": "strong" if metrics.get("committee_member") else "medium" if bill.technical else "none",
        "rights": "strong" if bill.rights_or_constitutional else "medium" if metrics.get("normative_side") else "none",
        "local": "strong" if metrics.get("local_impact") else "none",
        "credo": "strong" if metrics.get("strong_credo_side") else "none",
        "faction": "strong" if faction.get("vote") in {"for", "against"} and faction.get("cohesion", 0) >= 0.70 else "none",
        "evidence": "medium" if metrics.get("number_for", 0) or metrics.get("number_against", 0) else "weak" if official_count else "none",
        "deliberation": "medium" if official_count >= 2 or official_cues >= 8 else "weak" if official_count else "none",
    }


def score_meta_strategies(context) -> dict[str, dict]:
    features = feature_levels(context)
    government_score = (
        qadd(features["government"], features["salience"], features["coalition"], features["party"])
        if context.bill.sponsor == "government"
        else 0
    )
    scores = {
        "high_salience_government": government_score,
        "technical_committee": qadd(features["committee"], features["committee"], features["evidence"]),
        "rights_or_constitutional": qadd(features["rights"], features["credo"], features["evidence"]),
        "local_impact": qadd(features["local"], features["local"], features["local"], features["credo"], features["evidence"]),
        "relational_faction": qadd(features["faction"], features["party"], features["evidence"]),
        "fallback_balancing": qadd(features["evidence"], features["deliberation"]),
    }
    return {
        meta_id: {
            "score": score,
            "level": qlevel(score),
            "features": features_for_meta(meta_id, features),
        }
        for meta_id, score in scores.items()
    }


def features_for_meta(meta_id: str, features: dict[str, str]) -> dict[str, str]:
    used = {
        "high_salience_government": ("government", "salience", "coalition", "party"),
        "technical_committee": ("committee", "evidence"),
        "rights_or_constitutional": ("rights", "credo", "evidence"),
        "local_impact": ("local", "credo", "evidence"),
        "relational_faction": ("faction", "party", "evidence"),
        "fallback_balancing": ("evidence", "deliberation"),
    }[meta_id]
    return {key: features[key] for key in used}


def choose_highest(scores: dict[str, dict]) -> str:
    priority = [
        "local_impact",
        "rights_or_constitutional",
        "high_salience_government",
        "technical_committee",
        "relational_faction",
        "fallback_balancing",
    ]
    return max(priority, key=lambda item: (scores[item]["score"], -priority.index(item)))


def compact_score_trace(scores: dict[str, dict]) -> str:
    parts = []
    for meta_id, info in sorted(scores.items(), key=lambda item: item[1]["score"], reverse=True):
        parts.append(f"{meta_id}={info['score']}({info['level']})")
    return "; ".join(parts)
