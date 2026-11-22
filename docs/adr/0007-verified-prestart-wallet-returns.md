# ADR 0007: Correct verified pre-start wallet returns in the legacy flow

Date: 2026-11-21. Status: accepted bounded bug-fix contract under the owner's postponement test report and the previously accepted original-payer/full-return policy in ADR 0002. It does not activate the proposed financial engine.

## Decision

The existing terminal transition only changed status/notes and left a rejected postponed request charged. Implement a conservative legacy return adapter for clearly evidenced initial pre-start wallet-funded cases, in the same transaction/consultation lock as rejection/cancellation. Return the actual original debit once, reverse its platform fee credit, retain historical entries, prohibit a later payment verification from reactivating the returned charge, and expose the recorded outcome to participants.

Use existing REFUND/ADJUSTMENT entry types, consultation foreign keys and structured event metadata linking original/return references. No new schema, financial operation model or gateway refund is included. Record the adapter in the future common-posting writer inventory; it cannot remain an unjournaled writer when a wallet is later activated on the new engine.

Do not guess missing/mixed provider funding, service-start evidence or legacy quota periods. Such cases explicitly require administrator review. Do not reset lifetime usage counters, grant a monthly slot, refund a TMC-assisted patient from the platform, recalculate from current prices or erase doctor settlements. Ambiguous accepted/queued/start evidence remains review-scoped.

Add clear persistent patient/doctor rejection outcomes and viewport notices; accepting a postponement retains the original charge. Lock patient response decisions through schedule and transition updates. Keep existing role checks, state machine, doctor cooldown and availability rules.

## Historical maintenance

Case-specific authority and evidence remain private. No additional historical correction or mass backfill is authorised by this public release.

## Limits

This closes the reported legacy wallet/notification defect for verified cases. It is not complete F/Q/S compliance, a balanced new journal, database-enforced reversal uniqueness, clinical-start attestation, bank/provider refund, monthly quota restoration, commission/payable redesign or direct checkout. Privileged ORM/SQL can still damage legacy references; future schema/write constraints remain necessary.

See [POSTPONEMENT_RETURNS.md](../POSTPONEMENT_RETURNS.md) for eligibility, evidence, lock order, counters, review cases and recovery, and [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) for tests actually run and the specific correction result.
