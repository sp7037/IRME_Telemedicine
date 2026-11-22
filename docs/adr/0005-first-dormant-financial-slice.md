# ADR 0005: Start dormant schema with immutable operation identity

Date: 2026-11-20. Status: technical review complete; proposed implementation contract. No model/table/migration implemented or rollout authorised in this task.

## Decision

Narrow the first G1 slice to one dormant `FinancialOperation` identity table, protected actor-scope reference, scoped unique key, request fingerprint, read-only admin and PostgreSQL UPDATE/DELETE protection. Add no money fields, policies, legacy version markers, data backfill or runtime caller.

Amend the broad operation sketch in ADR 0003's schema specification: operation identity and request fingerprint are immutable; future execution state, resource bindings, result references and attempts belong to separate records/services. Do not add these to G1A or weaken identity immutability to make retries work. Resource-level uniqueness and atomic business execution remain later requirements; a request key alone cannot prevent duplicate charges made with different keys.

The [first-slice review](../DORMANT_FINANCIAL_SLICE_REVIEW.md) supplies exact proposed fields, named constraints/indexes, migration dependencies/reverse guard, role boundaries, compatibility and D01-D12 implementation checks. It is the detailed contract for a separately authorised implementation. PostgreSQL enforcement must be tested there; documentation does not prove it works.

## Why this slice

Operation identity is independent of open discount precedence, quota amendments, start evidence, direct-checkout, payout-calendar and legacy mapping decisions. Policy publication and a full posting journal would bring those dependencies into the first change. One dormant identity record provides a small, testable foundation without rewriting existing behaviour or implying that financial correctness is already delivered.

## Boundaries and consequences

- Preserve confirmed commission-as-discount, independent doctor payable, monthly rules and pre-booking INR 100 eligibility. No financial behaviour changes here.
- Protect new identity fields against ordinary ORM/queryset/SQL UPDATE/DELETE; preserve its user scope with a restrictive FK. Admin/API protections from ADR 0004 remain. Privileged schema operations/TRUNCATE and legacy cascade chains require their separately documented operational/schema gates.
- No default policy, entitlement, observed legacy operation, actor substitution or normal-account permission grant. New table must remain empty in the normal environment until a later writer is reviewed and authorised.
- Reverse only an empty table under exclusive maintenance. Retain populated evidence and fix forward.
- G1A is one part of G1. Common posting, account reconciliation, coherent quota/refund/payable processing and rollout gates remain mandatory before new-engine use.

## Verification and preservation

This review changes repository documentation/agent handoff only. Evidence and next step are recorded in [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md). D01-D12 are unexecuted specifications; the previous 103/103 backend baseline remains historical evidence, not a passing result for this schema.
