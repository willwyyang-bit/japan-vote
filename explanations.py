"""English and Japanese explanation rendering."""

from __future__ import annotations

from models import Decision, EvidenceMatch


def explain(data, decision: Decision, lang: str = "en") -> str:
    if lang == "ja":
        return explain_ja(data, decision)
    return explain_en(data, decision)


def explain_en(data, decision: Decision) -> str:
    member = data.members[decision.member_id]
    bill = data.bills[decision.bill_id]
    real = f" The recorded vote is {decision.real_vote}." if decision.real_vote else ""
    reasons = summarize_reasons(data, decision.reasons) or "the available symbolic evidence does not supply a decisive policy reason"
    downside = summarize_tradeoffs(data, decision)
    goal_sentence = summarize_goals(decision)
    strategy_note = f" {decision.strategy_note_en}" if decision.strategy_note_en else ""
    score = ""
    if decision.score is not None:
        score = " The prediction is correct." if decision.score else " The prediction does not match the recorded vote."
    return (
        f"{member.name_en} votes {vote_target_phrase(decision.predicted_vote, bill.title_en)}.{real} "
        f"The selected meta-strategy is {decision.meta_strategy_name_en}, so the system treats this as a case where "
        f"{decision.meta_strategy_name_en} reasoning should structure the decision. The selected strategy is "
        f"{decision.strategy_name_en}.{strategy_note} Supporting considerations include {reasons}. "
        f"{downside}{direction_sentence(decision)} {goal_sentence}{score}"
    )


def explain_ja(data, decision: Decision) -> str:
    member = data.members[decision.member_id]
    bill = data.bills[decision.bill_id]
    real = f" 実際の記録投票は「{vote_ja(decision.real_vote)}」です。" if decision.real_vote else ""
    reasons = "；".join(format_reason(data, r, "ja") for r in decision.reasons[:3]) or "決定的な支持理由はありません"
    downside = "；".join(format_reason(data, r, "ja") for r in decision.downside[:2]) or "大きな不利益は記録されていません"
    score = ""
    if decision.score is not None:
        score = " 予測は実際の投票と一致します。" if decision.score else " 予測は実際の投票と一致しません。"
    return (
        f"{member.name_ja}は「{bill.title_ja}」に{vote_ja(decision.predicted_vote)}すると予測されます。{real} "
        f"選択されたメタ戦略は「{decision.meta_strategy_name_ja}」、具体的な戦略は"
        f"「{decision.strategy_name_ja}」です。支持理由：{reasons}。"
        f"不利益またはトレードオフ：{downside}。{score}"
    )


def vote_phrase(vote: str | None) -> str:
    return {
        "for": "in favor",
        "against": "against",
        "abstain": "to abstain",
        "absent": "absent",
        None: "without a clear recommendation",
    }.get(vote, str(vote))


def vote_target_phrase(vote: str | None, bill_title: str) -> str:
    if vote == "for":
        return f"in favor of {bill_title}"
    if vote == "against":
        return f"against {bill_title}"
    return f"{vote_phrase(vote)} on {bill_title}"


def summarize_reasons(data, reasons: list[EvidenceMatch]) -> str:
    if not reasons:
        return ""
    issue_names = []
    source_names = []
    for reason in reasons[:4]:
        issue = data.issues.get(reason.bill_stance.issue_id)
        issue_name = issue.name_en if issue else reason.bill_stance.issue_id
        if issue_name not in issue_names:
            issue_names.append(issue_name)
        source = reason.source_label_en
        if source and source not in source_names:
            source_names.append(source)
    issue_text = natural_list(issue_names)
    source_text = natural_list(source_names[:3])
    if source_text and issue_text:
        return f"{issue_text}, supported by {source_text}"
    return issue_text or source_text


def summarize_goals(decision: Decision) -> str:
    summary = decision.metrics.get("goal_summary", {})
    totals = summary.get("totals", {})
    top = summary.get("top", [])
    if not totals or not top:
        return ""
    top_text = natural_list(f"{pressure.name_en} ({pressure.weight})" for pressure in top[:3])
    return (
        f"Goal-pressure totals are for={totals.get('for', 0)} and against={totals.get('against', 0)}; "
        f"the leading pressures are {top_text}."
    )


def direction_sentence(decision: Decision) -> str:
    predicted = decision.predicted_vote or "without a clear direction"
    leading = decision.metrics.get("goal_summary", {}).get("leading_vote")
    if leading == decision.predicted_vote:
        return f"the dominant goal pressures point toward voting {predicted}."
    return f"the selected strategy treats its highest-priority goal as decisive and points toward voting {predicted}."


def summarize_tradeoffs(data, decision: Decision) -> str:
    matched = summarize_reasons(data, decision.downside)
    if matched:
        return f"Although there are tradeoffs involving {matched}, "

    bill = data.bills[decision.bill_id]
    opposite_stances = bill.stance_against if decision.predicted_vote == "for" else bill.stance_for
    issue_names = []
    for stance in opposite_stances[:3]:
        issue = data.issues.get(stance.issue_id)
        issue_name = issue.name_en if issue else stance.issue_id
        if issue_name not in issue_names:
            issue_names.append(issue_name)

    official = decision.metrics.get("official_vote_support", {})
    opposite_vote = "against" if decision.predicted_vote == "for" else "for"
    official_count = official.get(opposite_vote, 0)
    if issue_names and official_count:
        return (
            f"Although the bill raises concerns about {natural_list(issue_names)} and the official speech sample "
            f"contains {official_count} parsed item(s) on the opposite side, "
        )
    if issue_names:
        return f"Although the bill raises concerns about {natural_list(issue_names)}, "
    if official_count:
        return f"Although the official speech sample contains {official_count} parsed item(s) on the opposite side, "
    return "With no major countervailing goal recorded, "


def format_reason(data, reason: EvidenceMatch, lang: str) -> str:
    issue = data.issues.get(reason.bill_stance.issue_id)
    issue_name = issue.name_ja if lang == "ja" and issue else issue.name_en if issue else reason.bill_stance.issue_id
    source = reason.source_label_ja if lang == "ja" else reason.source_label_en
    side = side_ja(reason.bill_stance.side) if lang == "ja" else reason.bill_stance.side
    if lang == "ja":
        return f"{source}が「{issue_name}」に{side}の立場を持つ"
    return f"{source} has a {side} stance on {issue_name}"


def vote_ja(vote: str | None) -> str:
    return {
        "for": "賛成",
        "against": "反対",
        "abstain": "棄権",
        "absent": "欠席",
        "unknown": "不明",
        None: "明確な投票なし",
    }.get(vote, str(vote))


def side_ja(side: str | None) -> str:
    return {"pro": "支持", "con": "反対"}.get(side, str(side))


def natural_list(items) -> str:
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"
