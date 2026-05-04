"""Unit tests for Japan-VOTE."""

from __future__ import annotations

import unittest

from data_loader import load_data
from factions import compute_factions, faction_projected_vote
from models import Stance, importance_value
from ndl_ingest import classify_stance_text, normalize_records
from reasoner import build_context, decide, match_vote_stances


class JapanVoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data()

    def test_importance_order(self):
        self.assertGreater(importance_value("A"), importance_value("B"))
        self.assertGreater(importance_value("B"), importance_value("C"))
        self.assertGreater(importance_value("C"), importance_value("D"))

    def test_stance_matching(self):
        bill_stance = Stance("privacy", "pro", "B", "b", "bill")
        evidence = [Stance("privacy", "pro", "A", "m", "member")]
        matches = match_vote_stances(self.data, "against", [bill_stance], evidence)
        self.assertEqual(len(matches), 1)

    def test_coalition_strategy(self):
        decision = decide(self.data, "member_sato_hiroshi", "digital_governance_act")
        self.assertEqual(decision.predicted_vote, "for")
        self.assertEqual(decision.strategy, "coalition_loyalty")

    def test_constituency_strategy(self):
        decision = decide(self.data, "member_yamamoto_daichi", "nuclear_restart_safety_act")
        self.assertEqual(decision.predicted_vote, "against")
        self.assertEqual(decision.strategy, "constituency_protection")

    def test_committee_strategy(self):
        decision = decide(self.data, "member_ito_masato", "agricultural_resilience_bill")
        self.assertEqual(decision.predicted_vote, "for")
        self.assertEqual(decision.strategy, "committee_deference")

    def test_normative_strategy(self):
        decision = decide(self.data, "member_mori_ayaka", "constitutional_privacy_bill")
        self.assertEqual(decision.predicted_vote, "for")
        self.assertEqual(decision.strategy, "normative_decision")

    def test_explanation_languages(self):
        decision = decide(self.data, "member_tanaka_keiko", "child_family_support_act", enable_japanese=True)
        self.assertIn("selected strategy", decision.explanation_en)
        self.assertIn("具体的な戦略", decision.explanation_ja)

    def test_japanese_output_is_opt_in(self):
        decision = decide(self.data, "member_tanaka_keiko", "child_family_support_act")
        self.assertEqual(decision.explanation_ja, "")

    def test_context_metrics(self):
        member = self.data.members["member_nakamura_yui"]
        bill = self.data.bills["security_cooperation_act"]
        context = build_context(self.data, member, bill)
        self.assertGreaterEqual(context.metrics["number_against"], 1)

    def test_official_evidence_is_loaded_and_scored(self):
        bill = self.data.bills["digital_governance_act"]
        self.assertGreaterEqual(len(bill.official_evidence), 1)
        context = build_context(self.data, self.data.members["member_sato_hiroshi"], bill)
        self.assertGreaterEqual(context.metrics["official_evidence_count"], 1)
        self.assertIn("for", context.metrics["official_vote_support"])

    def test_goal_pressures_drive_rich_explanation(self):
        decision = decide(self.data, "member_sato_hiroshi", "digital_governance_act", trace=True)
        self.assertIn("goal pressures", decision.explanation_en)
        self.assertIn("coalition", decision.explanation_en)
        self.assertIn("goals:for=", "\n".join(decision.trace))

    def test_qualitative_meta_scores_are_recorded(self):
        decision = decide(self.data, "member_fujita_mika", "digital_governance_act", trace=True)
        self.assertIn("meta_scores:", "\n".join(decision.trace))
        self.assertEqual(decision.strategy, "faction_alignment")

    def test_factions_are_computed_from_votes(self):
        factions = compute_factions(self.data, exclude_bill_id="digital_governance_act")
        self.assertTrue(any("member_fujita_mika" in faction and "member_sato_hiroshi" in faction for faction in factions))
        signal = faction_projected_vote(self.data, "member_fujita_mika", "digital_governance_act")
        self.assertEqual(signal["vote"], "for")

    def test_ndl_text_classifier_is_transparent(self):
        side, importance, support, concern = classify_stance_text("この政策は重要であり、支援を強化する必要がある。")
        self.assertEqual(side, "pro")
        self.assertEqual(importance, "B")
        self.assertGreater(support, concern)

    def test_ndl_record_normalization_accepts_singleton(self):
        records = normalize_records({"speechRecord": {"speaker": "sample"}})
        self.assertEqual(records, [{"speaker": "sample"}])


if __name__ == "__main__":
    unittest.main()
