# BEFORE -> AFTER closure: KEEP_WITH_LIMITATIONS

Starting checkpoint: `906ec0c4eb02fa7bd0fedadea301642cd13b6596`.
One intervention only: negation exclusion and clause-local security/context
matching, including financial context for generic strong/weak sentiment words.
No further rule adjustment after observing AFTER. Assets/entities unchanged.

BEFORE was executed before editing the classifier and its complete METRICS.json
equals the frozen baseline_v1 report. BEFORE and AFTER have identical reference
and evaluator hashes. baseline_v1 and HUMAN_GOLD are unchanged. The existing
`baseline_commit` report field names the original reference classifier checkpoint;
the classifier hash distinguishes BEFORE from AFTER.

| Dimension / evaluator metric | BEFORE | AFTER |
|---|---:|---:|
| Event types precision | .875000 | 1.000000 |
| Event types recall | .807692 | .923077 |
| Event types micro_f1 | .840000 | .960000 |
| Event types exact_match | .791667 | .916667 |
| Assets precision | .944444 | .944444 |
| Assets recall | .850000 | .850000 |
| Assets micro_f1 | .894737 | .894737 |
| Assets exact_match | .875000 | .875000 |
| Sentiment macro_f1 | .453102 | .738095 |
| Sentiment accuracy | .681818 | .863636 |

Event set FP: 3 -> 0; FN: 5 -> 2. Sentiment categorical errors: 7 -> 3.
Assets FP/FN remain 1/3. Full confusion matrices, class supports and per-case
errors remain in `before/METRICS.json` and `after/METRICS.json`; predictions are
stored separately. Same 24 cases; sentiment has the same 22 scorable cases and
two predefined mixed exclusions. Entity recall remains zero (unimplemented).

## Case comparison

- Corrected event types: N03 (not hacked), N05 (no ransomware), M01 (physical
  attack plus unrelated wallet update). All hack false positives become NEWS.
- Corrected sentiment: N01 (not surge), N02 (not crash), N06 (not bullish,
  explicitly bearish), M05 (strong speech, unchanged Bitcoin).
- Regressed: none on any scored dimension of the fixed set.
- Unchanged event-type failures: M02, M04 (two event topics, single output).
- Unchanged asset failures: A02, A03, A04 (case/aliases/polysemy).
- Unchanged entity failures: C03, C06, N04, M02, A03, A04.
- Unchanged sentiment failures: C05, A05, A06 (implicit valence/inflections).

Seven unique cases changed, each improving its affected dimension. The other
17 predictions are identical, including the two unscored mixed-sentiment cases.
The existing pipeline regression test was updated transparently: the political
"strong pipeline" example now has neutral sentiment and generates no opportunity,
instead of asserting the type of a previously generated opportunity. This is an
intended downstream consequence, not a baseline reference-label change.

## Evidence and limitations

38 tests pass across exactly `test_rss_negation_scope.py`,
`test_event_semantics_evaluation.py`, `test_rss_semantic_integrity.py`.
The evaluator AFTER completed successfully; no full suite was run.

The deterministic paired run attributes these output differences to this localized
intervention, not to separate contributions of its individual guards. It does not
establish production accuracy: the small diagnostic set was known when designing
the change and labels remain assistant-proposed, with no human adjudication.
Zero observed regressions does not mean zero possible regressions. Lexical scope
can over-mask later affirmative content, punctuation can split genuine context,
and implicit subjects, same-clause unrelated terms and complex negation remain
unresolved. Single-event/scalar sentiment limitations and entity extraction remain.

Decision: KEEP_WITH_LIMITATIONS; freeze Event Intelligence v1.1 provisionally,
without more NLP iteration in this session. No Edge or Knowledge/Criterion claim.
Protected capture, receipts, holdouts and scientific gates were not touched.
Changes remain local and uncommitted at the user's explicit request. STOP.
