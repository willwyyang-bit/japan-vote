(Note: The full report has not been uploaded online yet but is in the gradescope submission. This is a succinct README document for instruction to run the code.)

Japan-VOTE is a Python decision system that predicts and explains Japanese legislative votes using symbolic strategies, metastrategies, goal pressures, coalition/faction reasoning, and curated vote data.

The project uses only the Python standard library.

## How to Run

```bash
python3 demo.py --list
```

This lists available member IDs and bill IDs.

Run a basic English prediction:

```bash
python3 demo.py --member member_sato_hiroshi --bill digital_governance_act
```

Run with strategy trace:

```bash
python3 demo.py --member member_sato_hiroshi --bill digital_governance_act --trace
```

Run a local-interest example:

```bash
python3 demo.py --member member_yamamoto_daichi --bill nuclear_restart_safety_act --trace
```

Run a faction-alignment example:

```bash
python3 demo.py --member member_fujita_mika --bill digital_governance_act --trace
```

Japanese output is disabled by default to avoid encoding issues. Enable it explicitly:

```bash
python3 demo.py --member member_mori_ayaka --bill constitutional_privacy_bill --lang ja --enable-japanese
```

## Evaluation

Evaluate all curated recorded votes:

```bash
python3 evaluation.py
```

Current result:

```text
Overall: 57/60 = 95.0%
```

## Tests

Run the unit tests:

```bash
python3 -m unittest tests.py
```

Current suite:

```text
Ran 15 tests ... OK
```

## Optional Data Scripts

Generate a faction report:

```bash
python3 faction_analysis.py --write faction_report.md
```

Pull a small official National Diet Library speech-evidence sample:

```bash
python3 ndl_ingest.py --limit 5 --keywords-per-issue 2 --sleep 1 --output-json ndl_sample_evidence.json --output-md ndl_sample_evidence.md
```

Fold generated NDL evidence into the dataset:

```bash
python3 enrich_dataset.py
```

## Main Files

- `demo.py`: command-line demo.
- `evaluation.py`: evaluates predictions against recorded votes.
- `tests.py`: unit tests.
- `japan_vote_data.json`: curated and enriched dataset.
- `models.py`: symbolic objects.
- `reasoner.py`: main decision loop.
- `strategies.py`: concrete voting strategies.
- `meta_strategies.py`: metastrategy selection.
- `qualitative.py`: qualitative arithmetic for metastrategies.
- `goals.py`: goal-pressure reasoning.
- `factions.py`: computed faction logic.
- `explanations.py`: English/Japanese explanation templates.
- `example_outputs.md`: sample command outputs.
- `README.md`: full project report/write-up.
