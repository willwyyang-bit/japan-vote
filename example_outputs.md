# Japan-VOTE Example Outputs

## Coalition Loyalty

Command:

```bash
python demo.py --member member_sato_hiroshi --bill digital_governance_act --trace
```

Output:

```text
Sato Hiroshi votes in favor of Digital Governance and Data Use Act. The recorded vote is for. The selected meta-strategy is high-salience government bill, so the system treats this as a case where high-salience government bill reasoning should structure the decision. The selected strategy is coalition loyalty. The selected strategy gives greatest weight to maintaining coalition alignment and policy coordination. This pressure has weight 9 because the bill has a clear ruling-coalition position. It is reinforced by advancing the cabinet's legislative agenda (8); following the party line (8). Supporting considerations include digital governance, supported by coalition agreement. Although the bill raises concerns about privacy and local autonomy and the official speech sample contains 7 parsed item(s) on the opposite side, the dominant goal pressures point toward voting for. Goal-pressure totals are for=57 and against=0; the leading pressures are maintaining coalition alignment and policy coordination (9), advancing the cabinet's legislative agenda (8), and following the party line (8). The prediction is correct.

Trace:
- meta_scores:high_salience_government=12(strong); technical_committee=8(strong); relational_faction=8(strong); rights_or_constitutional=4(medium); fallback_balancing=4(medium); local_impact=2(weak)
- goals:for=57; against=0
- official_evidence:count=20; for=8; against=7; context=5
- meta:high_salience_government
- try:coalition_loyalty
- success:coalition_loyalty
```

## Constituency Protection

Command:

```bash
python demo.py --member member_yamamoto_daichi --bill nuclear_restart_safety_act --trace
```

Output:

```text
Yamamoto Daichi votes against Nuclear Restart and Safety Review Act. The recorded vote is against. The selected meta-strategy is local impact bill, so the system treats this as a case where local impact bill reasoning should structure the decision. The selected strategy is constituency protection. The selected strategy gives greatest weight to protecting district interests. This pressure has weight 10 because Fukushima local safety and recovery pressure. It is reinforced by respecting constitutional and rights-based norms (6); responding to official deliberative evidence (6). Countervailing goals remain, especially honoring the member's personal commitments (9); following the party line (8), but they do not dominate this strategy. Supporting considerations include nuclear safety, supported by Fukushima local safety and recovery pressure. Although there are tradeoffs involving energy security and regional recovery, supported by ruling coalition, Yamamoto Daichi, and Fukushima fisheries, the selected strategy treats its highest-priority goal as decisive and points toward voting against. Goal-pressure totals are for=45 and against=28; the leading pressures are protecting district interests (10), honoring the member's personal commitments (9), and following the party line (8). The prediction is correct.

Trace:
- meta_scores:local_impact=14(strong); high_salience_government=11(strong); technical_committee=8(strong); relational_faction=8(strong); rights_or_constitutional=7(strong); fallback_balancing=4(medium)
- goals:for=45; against=28
- official_evidence:count=10; for=0; against=6; context=4
- meta:local_impact
- try:constituency_protection
- success:constituency_protection
```

## Computed Faction Alignment

Command:

```bash
python demo.py --member member_fujita_mika --bill digital_governance_act --trace
```

Output:

```text
Fujita Mika votes in favor of Digital Governance and Data Use Act. The recorded vote is for. The selected meta-strategy is high-salience government bill, so the system treats this as a case where high-salience government bill reasoning should structure the decision. The selected strategy is computed faction alignment. The selected strategy gives greatest weight to staying aligned with the member's voting faction. This pressure has weight 8 because historical co-voting similarity gives a faction cohesion of 0.76. It is reinforced by following the party line (8); responding to official deliberative evidence (4). Countervailing goals remain, especially balancing matched policy reasons (4), but they do not dominate this strategy. The faction signal is based on historical voting similarity with Ito Masato, Sato Hiroshi, Tanaka Keiko, Watanabe Shun; faction cohesion is 0.76. Supporting considerations include digital governance, supported by computed faction signal. Although there are tradeoffs involving privacy, supported by Fujita Mika and Constitutional Privacy Protection Bill, the dominant goal pressures point toward voting for. Goal-pressure totals are for=20 and against=4; the leading pressures are following the party line (8), staying aligned with the member's voting faction (8), and responding to official deliberative evidence (4). The prediction is correct.

Trace:
- meta_scores:high_salience_government=9(strong); relational_faction=8(strong); fallback_balancing=4(medium); technical_committee=2(weak); rights_or_constitutional=2(weak); local_impact=2(weak)
- goals:for=20; against=4
- official_evidence:count=20; for=8; against=7; context=5
- meta:high_salience_government
- try:coalition_loyalty
- fail:coalition_loyalty
- try:cabinet_agenda_support
- fail:cabinet_agenda_support
- try:faction_alignment
- success:faction_alignment
```

## Japanese Output

Command:

```bash
python demo.py --member member_mori_ayaka --bill constitutional_privacy_bill --lang ja --enable-japanese
```

Output:

```text
森彩花は「憲法上のプライバシー保護法案」に賛成すると予測されます。 実際の記録投票は「賛成」です。 選択されたメタ戦略は「権利・憲法関連法案」、具体的な戦略は「規範的判断」です。支持理由：森彩花が「市民的自由」に支持の立場を持つ；野党ブロックが「市民的自由」に支持の立場を持つ；野党ブロックが「プライバシー」に支持の立場を持つ。不利益またはトレードオフ：大きな不利益は記録されていません。 予測は実際の投票と一致します。
```

## Evaluation

Command:

```bash
python evaluation.py
```

Output:

```text
Overall: 57/60 = 95.0%

By bill:
  agricultural_resilience_bill     10/10 100.0%
  child_family_support_act         10/10 100.0%
  constitutional_privacy_bill       7/10 70.0%
  digital_governance_act           10/10 100.0%
  nuclear_restart_safety_act       10/10 100.0%
  security_cooperation_act         10/10 100.0%

By party:
  cdp                              12/12 100.0%
  dpfp                              5/6  83.3%
  ishin                             5/6  83.3%
  jcp                               6/6  100.0%
  komeito                          11/12 91.7%
  ldp                              18/18 100.0%

By strategy:
  coalition_loyalty                19/19 100.0%
  committee_deference               2/3  66.7%
  constituency_protection           1/1  100.0%
  faction_alignment                28/29 96.6%
  normative_decision                3/4  75.0%
  party_line                        4/4  100.0%
```
