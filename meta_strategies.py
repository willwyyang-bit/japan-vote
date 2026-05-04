"""Meta-strategy selection for Japan-VOTE.

The original VOTE system ranks concrete strategies. Japan-VOTE adds a meta
layer that scores the political situation using qualitative arithmetic before
choosing which ranked strategy list to try.
"""

from __future__ import annotations

from qualitative import choose_highest, compact_score_trace, score_meta_strategies


META_STRATEGIES = {
    "rights_or_constitutional": {
        "name_en": "rights or constitutional bill",
        "name_ja": "\u6a29\u5229\u30fb\u61b2\u6cd5\u95a2\u9023\u6cd5\u6848",
        "order": [
            "normative_decision",
            "personal_credo",
            "faction_alignment",
            "party_line",
            "opposition_bloc_alignment",
            "coalition_loyalty",
            "minimize_adverse_effects",
            "simple_consensus",
            "simple_majority",
            "deeper_analysis",
            "no_decision",
        ],
    },
    "local_impact": {
        "name_en": "local impact bill",
        "name_ja": "\u5730\u57df\u5f71\u97ff\u6cd5\u6848",
        "order": [
            "constituency_protection",
            "personal_credo",
            "faction_alignment",
            "coalition_loyalty",
            "party_line",
            "minimize_adverse_effects",
            "simple_consensus",
            "simple_majority",
            "deeper_analysis",
            "no_decision",
        ],
    },
    "high_salience_government": {
        "name_en": "high-salience government bill",
        "name_ja": "\u91cd\u8981\u306a\u653f\u5e9c\u63d0\u51fa\u6cd5\u6848",
        "order": [
            "coalition_loyalty",
            "cabinet_agenda_support",
            "faction_alignment",
            "opposition_bloc_alignment",
            "party_line",
            "personal_credo",
            "committee_deference",
            "minimize_adverse_effects",
            "simple_consensus",
            "simple_majority",
            "deeper_analysis",
            "no_decision",
        ],
    },
    "technical_committee": {
        "name_en": "technical committee bill",
        "name_ja": "\u5c02\u9580\u59d4\u54e1\u4f1a\u6cd5\u6848",
        "order": [
            "committee_deference",
            "faction_alignment",
            "party_line",
            "coalition_loyalty",
            "opposition_bloc_alignment",
            "simple_consensus",
            "minimize_adverse_effects",
            "simple_majority",
            "deeper_analysis",
            "no_decision",
        ],
    },
    "relational_faction": {
        "name_en": "computed faction alignment",
        "name_ja": "\u8a08\u7b97\u3055\u308c\u305f\u6d3e\u95a5\u4e00\u81f4",
        "order": [
            "faction_alignment",
            "party_line",
            "coalition_loyalty",
            "opposition_bloc_alignment",
            "committee_deference",
            "minimize_adverse_effects",
            "simple_consensus",
            "simple_majority",
            "deeper_analysis",
            "no_decision",
        ],
    },
    "fallback_balancing": {
        "name_en": "fallback balancing",
        "name_ja": "\u7dcf\u5408\u8861\u91cf",
        "order": [
            "simple_consensus",
            "normative_decision",
            "minimize_adverse_effects",
            "faction_alignment",
            "party_line",
            "simple_majority",
            "deeper_analysis",
            "no_decision",
        ],
    },
}


def choose_meta_strategy(context):
    scores = score_meta_strategies(context)
    selected = choose_highest(scores)
    context.metrics["meta_scores"] = scores
    context.metrics["meta_score_trace"] = compact_score_trace(scores)
    return selected
