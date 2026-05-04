"""Concrete ranked decision strategies for Japan-VOTE."""

from __future__ import annotations

from goals import goal_dominates, opposing_pressures, pressures_for_vote
from models import EvidenceMatch, Stance, StrategyResult, importance_value, opposite_vote, stronger


STRATEGY_LABELS = {
    "coalition_loyalty": ("coalition loyalty", "連立与党への忠誠"),
    "cabinet_agenda_support": ("cabinet agenda support", "内閣提出法案の支持"),
    "opposition_bloc_alignment": ("opposition bloc alignment", "野党ブロックとの一致"),
    "faction_alignment": ("computed faction alignment", "\u8a08\u7b97\u3055\u308c\u305f\u6d3e\u95a5\u4e00\u81f4"),
    "party_line": ("party-line voting", "党議拘束"),
    "committee_deference": ("committee deference", "委員会への信頼"),
    "constituency_protection": ("constituency protection", "選挙区利益の保護"),
    "personal_credo": ("personal credo", "個人的信念"),
    "normative_decision": ("normative decision", "規範的判断"),
    "simple_consensus": ("simple consensus", "単純な合意"),
    "minimize_adverse_effects": ("minimize adverse effects", "悪影響の最小化"),
    "simple_majority": ("simple majority", "単純多数"),
    "deeper_analysis": ("deeper analysis", "より深い分析"),
    "no_decision": ("no decision", "判断不能"),
}


def label(strategy_id: str) -> tuple[str, str]:
    return STRATEGY_LABELS[strategy_id]


def apply_strategy(strategy_id: str, context) -> StrategyResult:
    return STRATEGIES[strategy_id](context)


def coalition_loyalty(context) -> StrategyResult:
    bill = context.bill
    member = context.member
    if (
        member.party in context.data.ruling_coalition
        and bill.coalition_position in {"for", "against"}
        and goal_dominates(context, "coalition_coordination", bill.coalition_position, tolerance=2)
    ):
        vote = bill.coalition_position
        return StrategyResult(
            True,
            vote,
            institutional_reason(context, vote, "ruling_coalition", "A", "coalition agreement"),
            context.reasons_for_vote(opposite_vote(vote)),
            strategy_note(context, vote, "coalition_coordination"),
            "議員は与党連立に属しており、この法案には明確な連立方針があります。",
        )
    return StrategyResult(False)


def cabinet_agenda_support(context) -> StrategyResult:
    bill = context.bill
    member = context.member
    if bill.sponsor == "government" and bill.salience == "A" and member.party in context.data.ruling_coalition:
        vote = bill.coalition_position or bill.party_positions.get(member.party)
        if vote in {"for", "against"}:
            return StrategyResult(
                True,
                vote,
                institutional_reason(context, vote, "government", "A", "cabinet legislative agenda"),
                context.reasons_for_vote(opposite_vote(vote)),
                strategy_note(context, vote, "cabinet_agenda"),
                "これは重要な政府提出法案であり、内閣の政策 agenda が優先されます。",
            )
    return StrategyResult(False)


def opposition_bloc_alignment(context) -> StrategyResult:
    bill = context.bill
    member = context.member
    if member.party in context.data.opposition_bloc and bill.opposition_position in {"for", "against"}:
        vote = bill.opposition_position
        return StrategyResult(
            True,
            vote,
            institutional_reason(context, vote, "opposition_bloc", "A", "opposition coordination"),
            context.reasons_for_vote(opposite_vote(vote)),
            strategy_note(context, vote, "party_discipline"),
            "議員の政党はこの法案について野党ブロックの方針と一致しています。",
        )
    return StrategyResult(False)


def faction_alignment(context) -> StrategyResult:
    faction = context.metrics.get("faction", {})
    vote = faction.get("vote")
    peers = faction.get("peers", [])
    cohesion = faction.get("cohesion", 0.0)
    if vote in {"for", "against"} and peers and cohesion >= 0.70:
        peer_names = ", ".join(context.data.members[peer_id].name_en for peer_id in peers[:4])
        note_en = (
            strategy_note(context, vote, "faction_cohesion")
            + f" The faction signal is based on historical voting similarity with {peer_names}; "
            f"faction cohesion is {cohesion:.2f}."
        )
        note_ja = (
            f"\u904e\u53bb\u306e\u6295\u7968\u985e\u4f3c\u5ea6\u304b\u3089\u8a08\u7b97\u3055\u308c\u305f\u6d3e\u95a5\u304c"
            f"\u300c{vote}\u300d\u3092\u793a\u3057\u307e\u3059\u3002\u6d3e\u95a5\u306e\u7d50\u675f\u5ea6\u306f{cohesion:.2f}\u3067\u3059\u3002"
        )
        return StrategyResult(
            True,
            vote,
            institutional_reason(context, vote, "computed_faction", "B", "computed faction signal"),
            context.reasons_for_vote(opposite_vote(vote)),
            note_en,
            note_ja,
        )
    return StrategyResult(False)


def party_line(context) -> StrategyResult:
    bill = context.bill
    member = context.member
    vote = bill.party_positions.get(member.party)
    if vote in {"for", "against"}:
        return StrategyResult(
            True,
            vote,
            institutional_reason(context, vote, member.party, "A", "party position"),
            context.reasons_for_vote(opposite_vote(vote)),
            strategy_note(context, vote, "party_discipline"),
            "議員は所属政党の明確な方針に従います。",
        )
    return StrategyResult(False)


def committee_deference(context) -> StrategyResult:
    bill = context.bill
    member = context.member
    if bill.committee_recommendation in {"for", "against"} and (bill.technical or bill.committee in member.committees):
        vote = bill.committee_recommendation
        return StrategyResult(
            True,
            vote,
            institutional_reason(context, vote, bill.committee, "B", "committee recommendation"),
            context.reasons_for_vote(opposite_vote(vote)),
            strategy_note(context, vote, "committee_expertise"),
            "この法案は専門的または委員会中心の案件であるため、委員会判断を重視します。",
        )
    return StrategyResult(False)


def constituency_protection(context) -> StrategyResult:
    bill = context.bill
    member = context.member
    impact = bill.local_impacts.get(member.district)
    if impact and impact.get("vote") in {"for", "against"}:
        vote = impact["vote"]
        reason = institutional_reason(context, vote, member.district, "A", impact.get("reason_en", "district impact"))
        reason[0].source_label_ja = impact.get("reason_ja", reason[0].source_label_ja)
        return StrategyResult(
            True,
            vote,
            reason,
            context.reasons_for_vote(opposite_vote(vote)),
            strategy_note(context, vote, "constituency_protection"),
            "この法案は議員の選挙区に直接的な影響を与えます。",
        )
    return StrategyResult(False)


def personal_credo(context) -> StrategyResult:
    side = context.metrics.get("strong_credo_side")
    if side in {"for", "against"}:
        return StrategyResult(
            True,
            side,
            context.metrics.get("strong_credo_reasons", []),
            context.reasons_for_vote(opposite_vote(side)),
            strategy_note(context, side, "personal_commitment"),
            "議員にはこの投票方向を示す最重要の個人的信念があります。",
        )
    return StrategyResult(False)


def normative_decision(context) -> StrategyResult:
    side = context.metrics.get("normative_side")
    if side in {"for", "against"}:
        return StrategyResult(
            True,
            side,
            context.metrics.get("normative_reasons", []),
            context.reasons_for_vote(opposite_vote(side)),
            strategy_note(context, side, "constitutional_norm"),
            "この法案は権利・憲法・法の支配に関する規範を作動させます。",
        )
    return StrategyResult(False)


def simple_consensus(context) -> StrategyResult:
    if context.reasons_for and not context.reasons_against:
        return StrategyResult(True, "for", context.reasons_for, [], "All matched reasons support voting for.", "一致した理由はすべて賛成を支持します。")
    if context.reasons_against and not context.reasons_for:
        return StrategyResult(True, "against", context.reasons_against, [], "All matched reasons support voting against.", "一致した理由はすべて反対を支持します。")
    return StrategyResult(False)


def minimize_adverse_effects(context) -> StrategyResult:
    for_top = context.metrics["top_for_importance"]
    against_top = context.metrics["top_against_importance"]
    if context.reasons_for and context.reasons_against and stronger(for_top, against_top):
        return StrategyResult(
            True,
            "for",
            context.reasons_for,
            context.reasons_against,
            "Both sides have reasons, but the strongest reasons for the bill outrank the downside.",
            "両側に理由がありますが、賛成側の最強理由が反対側の懸念を上回ります。",
        )
    if context.reasons_for and context.reasons_against and stronger(against_top, for_top):
        return StrategyResult(
            True,
            "against",
            context.reasons_against,
            context.reasons_for,
            "Both sides have reasons, but the strongest reasons against the bill outrank the benefits.",
            "両側に理由がありますが、反対側の最強理由が賛成側の利点を上回ります。",
        )
    return StrategyResult(False)


def simple_majority(context) -> StrategyResult:
    if len(context.reasons_for) > len(context.reasons_against):
        return StrategyResult(True, "for", context.reasons_for, context.reasons_against, "More matched reasons support voting for.", "賛成を支持する一致理由の数が多くなっています。")
    if len(context.reasons_against) > len(context.reasons_for):
        return StrategyResult(True, "against", context.reasons_against, context.reasons_for, "More matched reasons support voting against.", "反対を支持する一致理由の数が多くなっています。")
    return StrategyResult(False)


def deeper_analysis(context) -> StrategyResult:
    return StrategyResult(False)


def no_decision(context) -> StrategyResult:
    return StrategyResult(
        True,
        None,
        [],
        [],
        "No strategy produced a confident vote.",
        "十分な根拠を持つ戦略が見つかりませんでした。",
    )


def strategy_note(context, vote: str | None, primary_goal_id: str) -> str:
    selected = [p for p in pressures_for_vote(context, vote) if p.goal_id == primary_goal_id]
    primary = selected[0] if selected else None
    supporting = [p for p in pressures_for_vote(context, vote) if p.goal_id != primary_goal_id]
    opposing = opposing_pressures(context, vote)

    if primary:
        opening = (
            f"The selected strategy gives greatest weight to {primary.name_en}. "
            f"This pressure has weight {primary.weight} because {primary.reason_en}."
        )
    else:
        opening = "The selected strategy follows the strongest available goal pressure."

    if supporting:
        support_text = "; ".join(f"{p.name_en} ({p.weight})" for p in supporting[:2])
        opening += f" It is reinforced by {support_text}."

    if opposing:
        tradeoff_text = "; ".join(f"{p.name_en} ({p.weight})" for p in opposing[:2])
        opening += f" Countervailing goals remain, especially {tradeoff_text}, but they do not dominate this strategy."

    return opening


def institutional_reason(context, vote: str | None, source_id: str, importance: str, evidence: str) -> list[EvidenceMatch]:
    vote = vote or "unknown"
    stance_pool = context.bill.stance_for if vote == "for" else context.bill.stance_against
    issue_id = stance_pool[0].issue_id if stance_pool else (context.bill.issues[0] if context.bill.issues else "institutional_alignment")
    bill_side = stance_pool[0].side if stance_pool else "pro"
    bill_stance = Stance(issue_id, bill_side, importance, context.bill.id, "bill", context.bill.evidence)
    evidence_stance = Stance(issue_id, bill_side, importance, source_id, "institution", evidence)
    return [
        EvidenceMatch(
            vote=vote,
            bill_stance=bill_stance,
            evidence_stance=evidence_stance,
            source_label_en=evidence,
            source_label_ja=institutional_label_ja(context, source_id, evidence),
        )
    ]


def institutional_label_ja(context, source_id: str, evidence: str) -> str:
    if source_id in context.data.parties:
        return context.data.parties[source_id].name_ja
    if source_id in context.data.groups:
        return context.data.groups[source_id].name_ja
    if source_id == "computed_faction":
        return "\u8a08\u7b97\u3055\u308c\u305f\u6d3e\u95a5"
    labels = {
        "coalition agreement": "連立合意",
        "cabinet legislative agenda": "内閣の政策方針",
        "opposition coordination": "野党間調整",
        "party position": "党の方針",
        "committee recommendation": "委員会判断",
        "computed faction signal": "\u8a08\u7b97\u3055\u308c\u305f\u6d3e\u95a5\u30b7\u30b0\u30ca\u30eb",
    }
    return labels.get(evidence, evidence)


STRATEGIES = {
    "coalition_loyalty": coalition_loyalty,
    "cabinet_agenda_support": cabinet_agenda_support,
    "opposition_bloc_alignment": opposition_bloc_alignment,
    "faction_alignment": faction_alignment,
    "party_line": party_line,
    "committee_deference": committee_deference,
    "constituency_protection": constituency_protection,
    "personal_credo": personal_credo,
    "normative_decision": normative_decision,
    "simple_consensus": simple_consensus,
    "minimize_adverse_effects": minimize_adverse_effects,
    "simple_majority": simple_majority,
    "deeper_analysis": deeper_analysis,
    "no_decision": no_decision,
}
