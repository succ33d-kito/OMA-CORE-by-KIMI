# CP-7M.0 Economic Accounting Boundary Audit

Status: PREPARATION ONLY
Baseline: 2ab1b9cd2540d735ec2a7ef552eac9c6e4b4453e
Branch: work/post-cp7l-prep-20261009

## Scientific status

EDGE=NOT_DEMONSTRATED
REGIME_VALIDATED=NO
MECHANICS_VALIDATED=NO
POLICY_WINNER=NONE

This document does not establish economic Edge, realized venue performance,
Outcome authority, learning eligibility, Knowledge validation, or Criterion
promotion authority.

CP-7L PaperClosedPosition is not present on this baseline and must not be
reconstructed on this branch.

## Finding 1 - Legacy Trade is not the modern accounting authority

core/schemas/trade_schema.py and core/execution/paper_trading.py belong to the
legacy paper path.

Legacy Trade:

- is mutable;
- may close using caller-supplied or current wall-clock time;
- computes PnL directly;
- does not preserve the modern causal execution lineage;
- does not separate observed, simulated, configured, unknown and unsupported
  economic components.

Legacy PaperTradingEngine also obtains prices through the configurable
SlippageEngine.

Therefore these objects must not become the authoritative accounting boundary
for the modern causal PAPER chain.

## Finding 2 - Legacy slippage is simulation, not evidence

core/execution/slippage.py is a configurable cost simulation model.

Its spread and slippage values are useful for scenario analysis and historical
backtesting only when explicitly labelled as configured assumptions.

They are not:

- observed execution slippage;
- venue fills;
- broker fills;
- factual transaction costs;
- causal post-intent evidence.

Configured slippage must never be relabelled OBSERVED.

## Finding 3 - ExecutionObservation is evidence, not accounting

core/scientific/execution_observation.py correctly exposes evidence primitives
without claiming fills, payments or total cost.

Potential evidence includes:

- bid;
- ask;
- mark price;
- index price;
- latest funding rate;
- maker fee rate;
- taker fee rate.

The contract explicitly does not establish:

- execution fill;
- slippage;
- funding payment;
- total transaction cost;
- PnL;
- Outcome.

This separation should be preserved.

## Finding 4 - Fee evidence support exists but prospective capture is incomplete

The modern evidence contract supports account-scoped USER_FEES receipts.

However, repository search on this baseline found no dedicated prospective
commissionRate capture path equivalent to the premiumIndex capture path.

Therefore:

fee_rate_status = OBSERVED only when a valid causal account-scoped receipt
exists.

Otherwise:

fee_rate_status = UNKNOWN.

A configured exchange fee schedule must not be relabelled as observed evidence.

## Finding 5 - Funding rate is not funding cashflow

Prospective premiumIndex capture exists and can preserve lastFundingRate.

However:

funding rate != funding payment
nextFundingTime != payment evidence

A factual or causally derived funding cashflow requires sufficient evidence of:

- the applicable funding event;
- position exposure at that event;
- position quantity;
- applicable mark/notional basis;
- funding rate used by the venue;
- correct sign convention;
- causal timestamps and provenance.

Until that boundary exists:

funding_cashflow = UNKNOWN.

## Finding 6 - Slippage remains unknown

The modern PAPER fill contracts use causal post-intent quotes.

That does not create observed venue slippage.

The system currently has no factual venue execution against which intended or
simulated price can be compared.

Therefore:

slippage = UNKNOWN.

Spread may be observed independently from bid/ask evidence, but observed spread
must not automatically be renamed slippage.

## Recommended architecture

The execution chain should terminate with CP-7L:

PaperClosedPosition

Economic accounting should begin after that boundary.

Recommended decomposition:

PaperClosedPosition
    ->
PaperGrossEconomicResult
    ->
PaperCostAssessment
    ->
PaperNetEconomicResult

Outcome and learning remain separate later-stage boundaries.

## CP-8A - PaperGrossEconomicResult

Input authority:

PaperClosedPosition only.

Expected derived economic fields may include:

- closed_position_ref;
- instrument;
- entry_side;
- exit_side;
- quantity_base;
- entry_price_usdt_per_base;
- exit_price_usdt_per_base;
- entry_notional_usdt;
- exit_notional_usdt;
- gross_price_pnl_usdt;
- gross_return_fraction;
- opened_at;
- closed_at;
- deterministic result identity.

All values must derive from the frozen closed-position lineage.

No caller may inject price, quantity, PnL or timestamps.

This result remains simulated PAPER economics.

It is not:

- factual account PnL;
- broker statement PnL;
- venue settlement;
- economic Edge proof;
- Outcome;
- LearningSignal.

## CP-8B - PaperCostAssessment

Cost components must preserve explicit epistemic status.

At minimum:

### Fees

fee_rate:
OBSERVED or UNKNOWN

fee_cash_amount:
DERIVED only when the required factual fee-rate evidence and applicable
simulated notional are present.

Configured fee schedules may be represented separately as CONFIGURED scenario
inputs but never as OBSERVED.

### Funding

funding_rate:
OBSERVED or UNKNOWN

funding_cashflow:
DERIVED only when complete causal funding-event and exposure evidence exists.

Otherwise UNKNOWN.

### Slippage

slippage:
UNKNOWN on the current PAPER evidence model.

Configured slippage scenarios may exist separately but cannot become factual
execution evidence.

### Spread

spread:
may be OBSERVED from causal bid/ask evidence.

Spread is not automatically a separate realized cost because the simulated
entry and exit prices already select the executable side of the book.

Any additional spread-cost decomposition must avoid double counting.

### Other costs

other_costs:
UNKNOWN unless explicitly evidenced and modelled.

## CP-8C - PaperNetEconomicResult

Net economics must fail closed.

If any mandatory cost component required by the frozen protocol remains
UNKNOWN, the system must not silently substitute zero.

Therefore:

net_pnl_usdt = UNKNOWN
net_return_fraction = UNKNOWN

until the protocol-defined required cost set is resolved.

Gross economics may still remain valid independently.

## Epistemic classification

| Component | Current allowed status |
|---|---|
| Entry simulated price | SIMULATED |
| Exit simulated price | SIMULATED |
| Filled base quantity | SIMULATED |
| Gross price PnL | DERIVED |
| Gross return | DERIVED |
| Bid / ask | OBSERVED when causal receipt exists |
| Spread | DERIVED from observed bid / ask |
| Maker fee rate | OBSERVED or UNKNOWN |
| Taker fee rate | OBSERVED or UNKNOWN |
| Fee cash amount | DERIVED or UNKNOWN |
| Funding rate | OBSERVED or UNKNOWN |
| Funding cashflow | DERIVED only with complete funding evidence; otherwise UNKNOWN |
| Slippage | UNKNOWN |
| Configured slippage scenario | CONFIGURED |
| Other costs | UNKNOWN |
| Net PnL | DERIVED only when mandatory costs resolved; otherwise UNKNOWN |
| Net return | DERIVED only when mandatory costs resolved; otherwise UNKNOWN |

## Attribution boundary

AttributionSchema and AttributionComponent in execution_position_plane.py are
not the primary accounting engine.

Their current semantics are unverified decomposition declarations.

They may consume or reference later economic results but must not manufacture
the primary gross or net economic truth.

Attribution remains separate from accounting.

## Outcome boundary

Current OutcomeComparison infrastructure must not be fed directly from
PaperClosedPosition.

Existing outcome logic is hypothesis/outcome comparison infrastructure and is
not itself the modern PAPER economic accounting authority.

The future boundary should remain conceptually:

PaperNetEconomicResult
    ->
Outcome / Attribution boundary
    ->
quarantined research candidate
    ->
independent scientific promotion gates

No PnL value may directly update Knowledge, Criterion, ranking, policy or future
decision formation.

## Learning integrity

Existing learning_integrity.py remains authoritative.

Incomplete verified decision/hypothesis/evidence/outcome lineage means:

NO LEARNING

Knowledge validation remains disabled without promotion authority.

Criterion application remains disabled without promotion authority.

## Explicit non-goals

This audit does not:

- implement CP-7L;
- calculate any PnL;
- inspect sealed confirmation outcomes;
- open holdouts;
- create a policy winner;
- validate Regime;
- validate Mechanics;
- demonstrate Edge;
- alter Knowledge;
- alter Criterion;
- change any existing execution contract.

## Recommended next sequence

1. Publish and audit CP-7L from the home laptop.
2. Rebase this preparation branch onto the CP-7L baseline.
3. Implement CP-8A PaperGrossEconomicResult.
4. Freeze mandatory cost policy.
5. Implement CP-8B PaperCostAssessment.
6. Implement CP-8C PaperNetEconomicResult.
7. Keep Outcome and Attribution scientifically separate.
8. Preserve learning quarantine until independent promotion gates exist.
