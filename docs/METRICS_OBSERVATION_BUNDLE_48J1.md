# 48J.1 — verified bundle projection, not admission

`load_verified_bundle` reuses the full continuity verifier and returns an immutable
canonical envelope with six factual values, component provenance, source interval,
role, capture availability, attempt/result/receipt identities and commitments.
Identity is deterministic and independent of verification time. Missing, invalid,
future or changing artifacts cannot yield a partial projection. No source writes.

The envelope explicitly says NOT_ADMITTED and ledger_available_at=null.
Capture availability must not be substituted for future ledger admission time.
The dataclass constructor/hash is not an authority or signature; trusted consumers
must invoke the loader. Local hashes do not defend against full evidence forgery.

Next integration requirement: observations_v2 currently inserts individual rows
and only assigns raw causal availability to Price and Funding. Metrics needs a
single atomic six-member transaction, full provenance validation (not merely a
feature whitelist), immutable role/conflict handling, and causal snapshot checks.
Do not call append_observation six times and claim atomic bundle admission.

This checkpoint performs no ledger admission, HTTP, live activation, outcomes or
research promotion. Tests use synthetic captured bundles only. 81H remains
unverified for real Metrics data; Edge remains not demonstrated.
