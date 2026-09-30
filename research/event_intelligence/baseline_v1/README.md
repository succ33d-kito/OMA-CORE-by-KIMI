# Event Intelligence diagnostic baseline v1

Baseline classifier: `63dcb70a45b632f97fea20525117e1dc0d4c8d6c`.
Rules were **not changed**. This directory contains no prospective observations,
market outcomes or holdout data. No learning or trading promotion follows.

## Reference and annotation policy

24 fixed English contrast cases: six previous-failure/control cases, six negation
cases, six multi-topic cases, six alias/polysemy/morphology cases. They are authored
diagnostic examples inspired by the preceding sprint, not a random news sample.
Some controls overlap earlier regression examples; they are not unseen validation.
No live source/database is required to reproduce the evaluation.

`REFERENCE.json` contains text, independently authored reference labels, tags and
per-case rationale, written before running predictions in this session. The author
is the assistant, not a human annotator. `human_reviewed=false` is intentional.
`HUMAN_GOLD.json` is empty: **zero human-adjudicated gold cases exist**. Do not
rename these provisional labels human gold or use metrics as release certification.
Human review should examine the reference without predictions first, record a
reviewer and reference hash, and version disagreements instead of silently editing
the baseline. This evaluator does not call an LLM or generate its own labels.

Policies fixed for this evaluation:

- Event types: asserted primary topics under the existing enum. A denied cyber
  incident is NEWS; a pending regulatory decision remains REGULATORY. Two explicit
  event topics receive a set, not an arbitrary dominant topic. Price-related RSS
  news uses NEWS; structured quote-derived PRICE_MOVEMENT is outside this test.
- Assets: canonical explicitly mentioned financial instruments/issuers, including
  lowercase tickers and company names when context identifies them. Mentions are
  counted even under negation. Contextual ADA accessibility law is not Cardano.
- Entities: named organizations, companies, countries and laws. Asset aliases
  alone are not an additional entity; unnamed roles such as president are excluded.
  Entity names use exact documented surface forms (SEC, Fed, Apple Inc., etc.).
- Sentiment: stated market/asset directional stance or explicitly adverse incident
  content, not general positive prose or predicted returns. Opposite asset directions
  are `null` (unscorable as one scalar), **not neutral**. No numeric score gold is
  invented, so no MAE or calibration claim is reported. C05's adverse theft label
  is an annotation-policy judgment that particularly warrants human review.

The same author chose examples and proposed labels with knowledge of the rules.
There is no blinded inter-annotator agreement, prevalence estimate or independent
test set. Small selected slices are descriptive; no statistical/generalization or
production-sufficiency threshold was established after seeing results.

## Reproduction and measurement

From repository root, with the existing project Python dependencies:

```powershell
python scripts/evaluate_event_semantics.py --output research/event_intelligence/baseline_v1/results
python -m pytest tests/test_event_semantics_evaluation.py tests/test_rss_semantic_integrity.py -q -p no:cacheprovider
```

The adapter supplies only ID/title/summary to the production RSS feed parser via
an in-memory feed. No network, database writes or environment modifications.
Real Event fields are measured, including the empty default `entities`. Random
event IDs and processing timestamps are excluded, making outputs deterministic.
`PREDICTIONS.json` is separate from annotations. `METRICS.json` includes hashes of
reference, classifier and evaluator, confusion matrices, class support, per-class
precision/recall/F1. Hashes normalize text line endings to LF for Windows/Git
portability. Reports also contain
tagged slices and per-case FP/FN. Retain this baseline when
testing future revisions in a different output directory.

Set extraction uses micro TP/FP/FN, precision, recall, F1 and exact match. Empty
prediction denominators give null precision, not perfect precision. Event type is
also scored as single-label accuracy/macro-F1 on the 22 single-topic cases. The two
multi-event cases remain in set metrics, exposing the single-output limitation.
Sentiment excludes only the two predeclared mixed cases and reports 22/24 coverage.
Macro-F1 averages reference-supported classes; per-class tables retain unsupported
predicted labels. Sentiment is categorical, not a calibrated probability.

## Baseline results (provisional reference)

| Dimension | n | Precision | Recall | F1 | Exact match / accuracy |
|---|---:|---:|---:|---:|---:|
| Event types, sets | 24 | .8750 | .8077 | .8400 micro | .7917 |
| Event type, single-topic only | 22 | — | — | .8578 macro | .8636 |
| Assets | 24 | .9444 | .8500 | .8947 micro | .8750 |
| Entities | 24 | undefined | .0000 | .0000 micro | .7500 |
| Sentiment | 22 | per-class in JSON | per-class in JSON | .4531 macro | .6818 |

Entity exact match is misleading on its own: 18 cases have empty references;
all seven entity mentions in the other six cases are missed. RSS has **no entity
extractor**, rather than a measured competent extractor with 75% accuracy.
Sentiment coverage is 91.67%; negation-slice sentiment accuracy is 3/6. Previous
substring/HTML/physical-attack controls pass; this does not eliminate contextual
errors. No classifier tuning or repeated threshold search was performed.

## Compact error taxonomy and concrete examples

| Mechanism | IDs | Observed error | Smallest candidate response |
|---|---|---|---|
| Negation/assertion scope | N01–N03, N05–N06 | "did not surge" -> bullish; "not hacked" -> hack FP; negated bullish cancels bearish | Clause-scoped negation with conservative abstention |
| Cross-topic binding | M01, M05 | Physical attack + unrelated wallet -> hack FP; "strong speech" -> bullish FP | Restrict evidence to the same clause and subject |
| Single-event output | M02, M04 | Missing macro_event / earnings in two-topic headlines | Flag ambiguous multi-topic input before considering richer representation |
| Scalar sentiment mismatch | M03, M06 | Opposite asset directions cannot be evaluated as one stance | Preserve unscorable/mixed status; do not call it neutral |
| Alias/case coverage | A02, A03 | BTC/ETH lowercase and Apple -> missing assets | Explicit contextual alias support, evaluated separately |
| Symbol polysemy | A04 | Accessibility ADA -> Cardano asset FP | Require financial context for ambiguous symbols |
| Morphology / implicit valence | A05, A06, C05 | surges/crashes and theft -> neutral FN | Small inflection/valence coverage after annotation agreement |
| Missing capability | C03, C06, N04, M02, A03, A04 | Named entities absent | Report unsupported; do not conflate assets and entities |

## Conclusion and next intervention

This is enough to falsify unrestricted semantic sufficiency on the specified
contrast cases, conditional on the proposed label policy. Document-wide keyword
co-occurrence lacks assertion/negation, subject and clause scope. A single type
and scalar sentiment also lose information for multi-topic input. This does not
prove an LLM, embeddings or broad new architecture are needed.

First obtain human adjudication of this fixed reference (especially denied
incidents, C05 and mixed-topic policy). The next smallest implementation experiment
recommended by the observed errors is a **clause-scoped negation/context guard**,
evaluated against this unchanged set plus fresh counterexamples. Do not broaden
keyword lists first: that would not repair the observed binding failures.
No implementation of that mechanism is part of this checkpoint.

Validation: 24 relevant tests passed, including known-count metric checks, missing
ID rejection, deterministic predictions, label/input separation and prior RSS
regressions. Capture, receipts, holdouts, Mechanics gates, Knowledge and Criterion
were not accessed or modified.
