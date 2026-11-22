# ADR 0002: Monthly TMC quota restoration and consultation refunds

Date: 2026-11-20. Status: **Accepted business policy; not implemented.**

2026-11-21 implementation amendment: [ADR 0007](0007-verified-prestart-wallet-returns.md) implements only conservative verified legacy pre-start wallet returns and truthful outcomes, including the reported postponement rejection case. Monthly quota lifecycle, uncertain start/provider cases and the complete new financial engine remain unimplemented/review-scoped. Do not apply a second return to legacy records already carrying a confirmed wallet-return event.

Scope: Phase 2A, policy definition only. No schema, code, payment processing, quota reset or migration is authorised by this document alone. Read alongside [ADR 0001](0001-consultation-pricing-and-ledger.md) and [business rules](../BUSINESS_RULES.md).

## Decision evidence

The owner explicitly confirmed these three choices in this chat on 2026-11-20:

1. Indian calendar months, unused slots expire at month-end; reserve at booking, consume on completion, restore eligible cancellations only to the original month, never as extra allowance in a later month.
2. Before consultation starts, cancellation by patient/TMC, doctor rejection or rejection of a proposed reschedule returns the full platform charge to the original payer and releases the reserved free slot; no doctor earning. Separate TMC patient cash collection is outside that platform refund.
3. No-shows, technical failures after starting, and disputes after completion require admin evidence review and a reasoned refund/doctor-payable adjustment, rather than an automatic penalty or refund.

These decisions resolve the core of P01/P02/P03. Remaining commercial settings and detailed schema/rollout work are still open; do not label all Phase 2 complete.

## Monthly allowance lifecycle

- Use Asia/Kolkata calendar-month boundaries, represented as half-open periods: local month start inclusive, next month start exclusive. Persist timestamps in UTC; do not change the application timezone merely to implement this policy.
- Admin sets optional per-TMC allowance; zero remains the default. This policy introduces no automatic free entitlement, joining bonus, rollover or prorated allocation.
- A successful booking reserves one unit from the allocation for its booking month. Reservation and booking must commit together. A failed booking has no consumed/reserved slot or financial debit.
- Eligible completion converts its reservation to consumption once. The independent doctor payable accrues under the booking snapshot, including free TMC work.
- At month-end, unused available units expire. Existing committed reservations remain attached to their original allocation; a later completion consumes that original reservation. This is fulfilment of an existing booking, not rollover for new bookings.
- An eligible cancellation/rejection releases the original reservation once. If its month is still open, the released unit becomes available there. If that month has closed, record the release but leave the entitlement expired; do not add it to the current month's allocation.
- An ordinary same-consultation postponement retains its original reservation and snapshot; it is not a second booking or a new free entitlement. Doctor substitution/repricing still requires the unresolved P08 policy.
- Period allocation, reservation, consumption, release and expiry must retain auditable references. Do not destructively zero lifetime counters or reassign old bookings to the current period.
- The existing confirmed INR 100 pre-booking wallet eligibility rule applies to free as well as paid new TMC bookings. Releasing a free slot does not credit money to a wallet.

Example: one slot is reserved on 30 November for a consultation on 2 December. Completion consumes the November reservation. Cancellation on 2 December releases that November reservation into an expired period; it does not increase December's allowance. Cancellation on 30 November instead makes the slot available until November ends. In either case, a free consultation has no cash refund because its platform charge was zero.

## Cancellation and exception matrix

“Full charge” means the actual snapshotted platform consultation amount charged, less amounts already refunded or committed to an in-flight refund. It is never the undiscounted reference price or a presumed TMC cash collection.

| Event | Platform charge outcome | Free quota outcome | Doctor payable outcome |
| --- | --- | --- | --- |
| Authorised patient/TMC cancellation before service starts | Full return to original payer | Release reservation to original period | No earning for unperformed consultation |
| Doctor rejects before service starts | Full return to original payer | Release original reservation | No earning |
| Patient/TMC rejects doctor's proposed reschedule before service starts | Full return to original payer | Release original reservation | No earning |
| Same consultation postponed and proposed time accepted | Retain existing booking charge; no duplicate debit | Retain original reservation | Still pending until eligible completion |
| Eligible consultation completed normally | No automatic refund | Consume reserved unit once | Accrue independent snapshotted payable once |
| Patient/TMC or doctor no-show | Admin review; no automatic penalty/refund | Admin determines release/consumption after evidence review | Admin records reasoned outcome |
| Technical failure after service starts | Admin review | Admin determines outcome with references | Admin determines payable adjustment |
| Completed consultation disputed | Admin review, including any partial/full refund | No automatic restoration | Preserve earned/paid history; any adjustment is linked and reasoned |

No-show/technical/dispute cases take the exception-review route, even if a no-show occurred without a service-start event. Do not infer a no-show solely from a scheduled time passing. A normal pre-start cancellation must not be reclassified as a no-show simply to withhold its full return.

## Service-start evidence and existing workflow compatibility

The refund cutoff is the start of the consultation, not merely its scheduled time. Existing code can move directly from doctor acceptance into `IN_PROGRESS`. That status alone must not be assumed to prove that clinical interaction occurred when adjudicating a dispute.

Before implementation, specify and review how an authoritative start event is recorded and explained to users across acceptance/queue/chat/video workflows. Preserve current functionality while designing that evidence; do not silently change the state machine in a refund patch. If records conflict or evidence is missing, route the case to admin rather than fabricate a start time or automatically deny a return.

## Refund destination and accounting safeguards

These safeguards carry out the accepted original-payer/full-charge rule; they do not introduce a new commission or fee policy.

- TMC wallet debit: return to that TMC wallet. Do not pay the TMC-assisted patient from the platform for cash the platform did not collect. The TMC remains responsible for its separate patient collection/refund arrangements.
- Direct patient wallet debit: return to that patient wallet. A prior wallet top-up is a separate funding event; do not also reverse the top-up when returning a consultation debit.
- Future direct gateway consultation payment: refund the original verified payment through the provider. Do not also create a wallet credit for the same returned amount.
- If legacy/mixed funding cannot be mapped confidently to original debit/payment references, require reconciliation/admin review before posting. Do not guess a payer or destination.
- A confirmed automatic pre-start entitlement may still need asynchronous processing. Distinguish eligibility/approval, pending processing, failure and confirmed return; never display a refund as completed before its wallet posting or provider confirmation.
- Limit combined confirmed and pending refunds to the original amount. Free bookings produce a quota release/event, not an artificial cash credit.
- Use original transaction links, reasons, actors, timestamps and idempotency keys. Repeated cancellations, callbacks, retries or admin clicks cannot refund/release/adjust earnings twice.
- Completion and cancellation must serialize under appropriate locks. If completion wins, follow the dispute-review route; if eligible cancellation wins, prevent later duplicate completion earnings.
- Do not delete financial entries or mark an actual doctor settlement as undone. Admin adjustments after settlement need separate recovery/offset/payment evidence and the later settlement-policy design; no automatic bank clawback is authorised here.
- Cancellation does not require the TMC to top up to INR 100 to receive a return. The threshold applies when initiating a new booking.

## Unresolved details and implementation gate

Accepted policies above must not be conflated with unanswered design/commercial decisions:

- Evidence/permissions/UI for the authoritative service start; legacy records without evidence.
- Admin quota amendments mid-month, allowance generation/retry strategy and protection of existing reservations.
- Gateway refund processing/reconciliation and mixed-funding legacy treatment.
- P04 discount override precedence; P06 settlement cutoffs/partial settlement and adjustment execution; P07 direct checkout/follow-up rules; P08 doctor substitution; P09 collection evidence; P10 migration/admin subsidy account semantics.

Next task is a bounded financial schema/compatibility design, with the above uncertainties explicit. No live automatic refunding, quota reset job, settlement or historic repricing until the relevant design, tests and rollout are reviewed. Existing baseline failures and migration drift remain separate maintenance work.

Phase 2B follow-up: that design is now recorded in [ADR 0003](0003-financial-schema-and-compatibility.md) and its linked specifications. Service-start UX and other open business choices remain review gates; this follow-up does not change the accepted policy or claim implementation.

## Verification and recovery

New specifications Q01-Q12 in [acceptance scenarios](../ACCEPTANCE_SCENARIOS.md) define required future tests. They are not executed tests.

Before this documentation change, nine existing project documents were ZIP/hash verified into `.local-recovery/phase2a-policy-20261120/documents-before.zip`; status and original HEAD were recorded there. This local ignored archive is documentation recovery, not a database/media backup. Restore individual documents for review rather than overwriting later decisions. Accepted policy can only be superseded by a documented owner decision, not by silently restoring an old draft.
