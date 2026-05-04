"""Japan-VOTE reasoning loop."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from explanations import explain
from factions import faction_projected_vote
from goals import compute_goal_pressures, summarize_goal_pressures
from meta_strategies import META_STRATEGIES, choose_meta_strategy
from models import (
    Bill,
    DataSet,
    Decision,
    EvidenceMatch,
    Member,
    Stance,
    importance_value,
    opposite_vote,
)
from strategies import apply_strategy, label


@dataclass
class DecisionContext:
    data: DataSet
    member: Member
    bill: Bill
    reasons_for: list[EvidenceMatch]
    reasons_against: list[EvidenceMatch]
    metrics: dict
    trace: list[str]
    expanded: bool = False

    def reasons_for_vote(self, vote: str | None) -> list[EvidenceMatch]:
        if vote == "for":
            return list(self.reasons_for)
        if vote == "against":
            return list(self.reasons_against)
        return []


def decide(data: DataSet, member_id: str, bill_id: str, trace: bool = False, enable_japanese: bool = False) -> Decision:
    member = data.members[member_id]
    bill = data.bills[bill_id]
    context = build_context(data, member, bill, expanded=False)
    meta_id = choose_meta_strategy(context)
    meta = META_STRATEGIES[meta_id]
    context.trace.append(f"meta_scores:{context.metrics.get('meta_score_trace')}")
    goal_summary = context.metrics.get("goal_summary", {})
    if goal_summary:
        totals = goal_summary.get("totals", {})
        context.trace.append(f"goals:for={totals.get('for', 0)}; against={totals.get('against', 0)}")
    if context.metrics.get("official_evidence_count"):
        support = context.metrics.get("official_vote_support", {})
        context.trace.append(
            "official_evidence:"
            f"count={context.metrics['official_evidence_count']}; "
            f"for={support.get('for', 0)}; against={support.get('against', 0)}; context={support.get('context', 0)}"
        )
    context.trace.append(f"meta:{meta_id}")

    strategy_id, result, final_context = _apply_ranked_strategies(context, meta["order"])
    strategy_name_en, strategy_name_ja = label(strategy_id)
    real_vote = bill.real_votes.get(member.id)
    score = int(real_vote == result.vote) if real_vote in {"for", "against"} and result.vote in {"for", "against"} else None

    decision = Decision(
        member_id=member.id,
        bill_id=bill.id,
        predicted_vote=result.vote,
        real_vote=real_vote,
        strategy=strategy_id,
        strategy_name_en=strategy_name_en,
        strategy_name_ja=strategy_name_ja,
        meta_strategy=meta_id,
        meta_strategy_name_en=meta["name_en"],
        meta_strategy_name_ja=meta["name_ja"],
        reasons=result.reasons,
        downside=result.downside,
        metrics=final_context.metrics,
        trace=final_context.trace if trace else [],
        strategy_note_en=result.note_en,
        strategy_note_ja=result.note_ja,
        score=score,
    )
    decision.explanation_en = explain(data, decision, "en")
    if enable_japanese:
        decision.explanation_ja = explain(data, decision, "ja")
    return decision


def build_context(data: DataSet, member: Member, bill: Bill, expanded: bool = False) -> DecisionContext:
    evidence = collect_member_evidence(data, member, exclude_bill_id=bill.id)
    for_stances = list(bill.stance_for)
    against_stances = list(bill.stance_against)
    if expanded:
        for_stances = expand_stances(data, for_stances)
        against_stances = expand_stances(data, against_stances)

    reasons_for = match_vote_stances(data, "for", for_stances, evidence)
    reasons_against = match_vote_stances(data, "against", against_stances, evidence)
    metrics = compute_metrics(data, member, bill, reasons_for, reasons_against)
    return DecisionContext(data, member, bill, reasons_for, reasons_against, metrics, [], expanded)


def _apply_ranked_strategies(context: DecisionContext, strategy_order: Iterable[str]):
    for strategy_id in strategy_order:
        context.trace.append(f"try:{strategy_id}")
        if strategy_id == "deeper_analysis":
            result = _try_deeper_analysis(context)
            if result[1].applies:
                return result
            continue
        result = apply_strategy(strategy_id, context)
        if result.applies:
            context.trace.append(f"success:{strategy_id}")
            return strategy_id, result, context
        context.trace.append(f"fail:{strategy_id}")
    result = apply_strategy("no_decision", context)
    return "no_decision", result, context


def _try_deeper_analysis(context: DecisionContext):
    expanded_context = build_context(context.data, context.member, context.bill, expanded=True)
    expanded_context.trace = list(context.trace) + ["deeper_analysis:expanded_issue_implications"]
    fallback_order = ["normative_decision", "simple_consensus", "minimize_adverse_effects", "simple_majority"]
    for strategy_id in fallback_order:
        expanded_context.trace.append(f"try:{strategy_id}")
        result = apply_strategy(strategy_id, expanded_context)
        if result.applies:
            expanded_context.trace.append(f"success:deeper_analysis->{strategy_id}")
            result.note_en = "Deeper analysis expanded issue implications before selecting: " + result.note_en
            result.note_ja = "より深い分析で争点の含意を展開してから判断しました。" + result.note_ja
            return "deeper_analysis", result, expanded_context
        expanded_context.trace.append(f"fail:{strategy_id}")
    return "deeper_analysis", apply_strategy("deeper_analysis", expanded_context), expanded_context


def collect_member_evidence(data: DataSet, member: Member, exclude_bill_id: str | None = None) -> list[Stance]:
    evidence = list(member.credo)

    for relation in member.relations:
        group = data.groups[relation.group_id]
        for stance in group.stances:
            side = stance.side if relation.side == "pro" else ("con" if stance.side == "pro" else "pro")
            level = min_importance(relation.importance, stance.importance)
            evidence.append(
                Stance(
                    issue_id=stance.issue_id,
                    side=side,
                    importance=level,
                    source_id=group.id,
                    source_type="group_relation",
                    evidence=relation.evidence or stance.evidence,
                )
            )

    for old_bill_id, vote in member.vote_history.items():
        if old_bill_id == exclude_bill_id:
            continue
        old_bill = data.bills.get(old_bill_id)
        if not old_bill:
            continue
        old_stances = old_bill.stance_for if vote == "for" else old_bill.stance_against
        for stance in old_stances:
            evidence.append(
                Stance(
                    issue_id=stance.issue_id,
                    side=stance.side,
                    importance=stance.importance,
                    source_id=old_bill.id,
                    source_type="voting_record",
                    evidence=f"past vote {vote} on {old_bill.title_en}",
                )
            )
    return evidence


def match_vote_stances(data: DataSet, vote: str, bill_stances: Iterable[Stance], evidence: Iterable[Stance]) -> list[EvidenceMatch]:
    matches: list[EvidenceMatch] = []
    for bill_stance in bill_stances:
        for evidence_stance in evidence:
            if bill_stance.issue_id == evidence_stance.issue_id and bill_stance.side == evidence_stance.side:
                matches.append(
                    EvidenceMatch(
                        vote=vote,
                        bill_stance=bill_stance,
                        evidence_stance=evidence_stance,
                        source_label_en=source_label(data, evidence_stance, "en"),
                        source_label_ja=source_label(data, evidence_stance, "ja"),
                    )
                )
    matches.sort(key=lambda item: importance_value(item.importance), reverse=True)
    return matches


def expand_stances(data: DataSet, stances: Iterable[Stance]) -> list[Stance]:
    result = list(stances)
    seen = {(s.issue_id, s.side, s.source_id, s.source_type) for s in result}
    for stance in list(stances):
        issue = data.issues.get(stance.issue_id)
        if not issue:
            continue
        implied = issue.pro_implications if stance.side == "pro" else issue.con_implications
        for implication in implied:
            key = (implication.issue_id, implication.side, stance.source_id, "deeper_analysis")
            if key not in seen:
                seen.add(key)
                result.append(
                    Stance(
                        implication.issue_id,
                        implication.side,
                        min_importance(stance.importance, implication.importance),
                        stance.source_id,
                        "deeper_analysis",
                        f"implied by {stance.issue_id}",
                    )
                )
    return result


def compute_metrics(data: DataSet, member: Member, bill: Bill, reasons_for: list[EvidenceMatch], reasons_against: list[EvidenceMatch]) -> dict:
    top_for = top_importance(reasons_for)
    top_against = top_importance(reasons_against)
    normative_side, normative_reasons = normative_result(data, reasons_for, reasons_against)
    strong_credo_side, strong_credo_reasons = strong_credo_result(reasons_for, reasons_against)
    faction = faction_projected_vote(data, member.id, bill.id)
    official = official_evidence_summary(bill)
    metrics = {
        "number_for": len(reasons_for),
        "number_against": len(reasons_against),
        "top_for_importance": top_for,
        "top_against_importance": top_against,
        "normative_side": normative_side,
        "normative_reasons": normative_reasons,
        "strong_credo_side": strong_credo_side,
        "strong_credo_reasons": strong_credo_reasons,
        "party_position": bill.party_positions.get(member.party),
        "coalition_position": bill.coalition_position,
        "committee_member": bill.committee in member.committees,
        "local_impact": bill.local_impacts.get(member.district),
        "faction": faction,
        "official_evidence_count": official["count"],
        "official_issue_coverage": official["issue_coverage"],
        "official_vote_support": official["vote_support"],
        "official_cue_strength": official["cue_strength"],
    }
    temp_context = DecisionContext(data, member, bill, reasons_for, reasons_against, metrics, [], False)
    pressures = compute_goal_pressures(temp_context)
    metrics["goal_pressures"] = pressures
    metrics["goal_summary"] = summarize_goal_pressures(pressures)
    return metrics


def official_evidence_summary(bill: Bill) -> dict:
    support = {"for": 0, "against": 0, "context": 0}
    cue_strength = 0
    covered_issues = set()
    for item in bill.official_evidence:
        vote = item.vote_alignment if item.vote_alignment in support else "context"
        support[vote] += 1
        covered_issues.add(item.issue_id)
        cue_strength += item.support_cues + item.concern_cues
    return {
        "count": len(bill.official_evidence),
        "issue_coverage": len(covered_issues),
        "vote_support": support,
        "cue_strength": cue_strength,
    }


def normative_result(data: DataSet, reasons_for: list[EvidenceMatch], reasons_against: list[EvidenceMatch]):
    norm_for = [r for r in reasons_for if data.issues[r.bill_stance.issue_id].norm_side == r.bill_stance.side]
    norm_against = [r for r in reasons_against if data.issues[r.bill_stance.issue_id].norm_side == r.bill_stance.side]
    if norm_for and not norm_against:
        return "for", norm_for
    if norm_against and not norm_for:
        return "against", norm_against
    if norm_for and norm_against:
        if importance_value(top_importance(norm_for)) > importance_value(top_importance(norm_against)):
            return "for", norm_for
        if importance_value(top_importance(norm_against)) > importance_value(top_importance(norm_for)):
            return "against", norm_against
    return None, []


def strong_credo_result(reasons_for: list[EvidenceMatch], reasons_against: list[EvidenceMatch]):
    credo_for = [r for r in reasons_for if r.evidence_stance.source_type == "member" and r.evidence_stance.importance == "A"]
    credo_against = [r for r in reasons_against if r.evidence_stance.source_type == "member" and r.evidence_stance.importance == "A"]
    if credo_for and not credo_against:
        return "for", credo_for
    if credo_against and not credo_for:
        return "against", credo_against
    return None, []


def top_importance(reasons: list[EvidenceMatch]) -> str | None:
    if not reasons:
        return None
    return max((r.importance for r in reasons), key=importance_value)


def min_importance(left: str, right: str) -> str:
    return left if importance_value(left) <= importance_value(right) else right


def source_label(data: DataSet, stance: Stance, lang: str) -> str:
    if stance.source_type == "member" and stance.source_id in data.members:
        return data.members[stance.source_id].name_ja if lang == "ja" else data.members[stance.source_id].name_en
    if stance.source_type == "group_relation" and stance.source_id in data.groups:
        return data.groups[stance.source_id].name_ja if lang == "ja" else data.groups[stance.source_id].name_en
    if stance.source_type in {"voting_record", "bill", "deeper_analysis"} and stance.source_id in data.bills:
        return data.bills[stance.source_id].title_ja if lang == "ja" else data.bills[stance.source_id].title_en
    if stance.source_id in data.parties:
        return data.parties[stance.source_id].name_ja if lang == "ja" else data.parties[stance.source_id].name_en
    if stance.source_id == "computed_faction":
        return "計算された派閥" if lang == "ja" else "computed faction"
    return stance.evidence or stance.source_id or stance.source_type
