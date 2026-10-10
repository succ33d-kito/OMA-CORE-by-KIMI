# 48I.2 — exact-plan activation

Use `scripts/activate_metrics_h1.py plan --state <absolute external metrics-h1-v1>
--role PILOT` to obtain a read-only JSON envelope. Save the entire envelope as
UTF-8 JSON outside the repository. Review its path, role, repository identity,
frozen hashes, activation hour and capture window. No paths are auto-created.

Within 60 seconds, `activate --plan <envelope file> --confirm <exact token>`
rechecks the envelope against the current repository, frozen design and filesystem.
Dirty code, changed identity, stale plan, clock regression, changed activation
boundary, existing state or staging residue block publication. Re-plan rather than
editing an old plan. The minimum lead remains the frozen 600 seconds.

The token binds the reviewed plan; it is not a signature or access-control secret.
Activation creates only immutable config via the existing atomic transaction.
It neither captures nor schedules. Then use the execution wrapper's `check`.
No automatic invocation of `run` follows activation.

Qualification uses isolated fixtures only. Real activation, task registration and
first-slot verification remain outstanding. No Price/Funding artifacts are touched.
