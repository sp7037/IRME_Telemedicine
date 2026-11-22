# ADR 0004: Financial admin writes and deletion boundaries

Date: 2026-11-20. Status: accepted and implemented for the existing admin/API boundary in this maintenance task. New financial schema and database enforcement remain separate.

## Context

Default Django model administration allowed direct edits to balances, payment/earning statuses, consultation financial relationships and recharge evidence. Deleting a user/profile/consultation could cascade into financial history or remove its references. Recharge status edits invoked reconciliation instead of the locked processing service. Staff API writes depended only on `is_staff`, allowing a user with view-only model permissions to bypass the admin interface.

## Decision

1. Make existing financial records and financially significant consultation/follow-up records view-only in Django admin, including for superusers. Disable generic add/change/delete and the finance inline's mutations. Use existing authorised consultation and finance services for business transitions.
2. Disable admin single/bulk deletion of users, doctor/patient/TMC profiles and fee settings as well as financial records. Keep account deactivation and approval workflows. Freeze an existing profile's user relationship and TMC usage counters in admin forms. Counter corrections require a future audited adjustment path; do not reset them to manufacture entitlement.
3. Replace recharge status editing with explicit pending manual approval/rejection actions. Use the existing locked service and record actor/time/request status plus Django admin log in the same per-request transaction. Require the corresponding recharge change permission; view-only access cannot process funding.
4. Match financial staff API writes to existing Django model permissions, listed in the [audit report](../FINANCIAL_ADMIN_AUDIT.md). Active superusers retain access; other staff must receive the specific permissions from a superuser. Do not automatically grant permissions or alter normal accounts during this task. Existing staff reports/read access and doctor approval controls remain unchanged.
5. Reject manual processing of provider-backed funding at the service boundary. Legacy manual reconciliation skips all provider-backed requests and requests with gateway evidence, preventing a second credit under a different description. Keep once-only legacy manual recovery for compatibility; do not reverse or repair historical balances automatically.
6. Validate staff fee/offer input before writes, reject direct usage-counter updates, and retain actor evidence for manual top-ups, configuration and recharge decisions. Future versioned commercial policies remain unimplemented.

## Limits and consequences

These are Django admin and API permissions, not database immutability constraints. Privileged ORM/queryset/SQL maintenance can still modify/delete legacy rows; legacy cascade/SET_NULL definitions remain unchanged. Proposed protected references and journal constraints require a separately reviewed additive migration and legacy analysis. Do not claim S04/S12 fully implemented for the future journal.

The legacy description-based reconciliation mechanism remains a compatibility risk until the planned posting adapter supplies durable unique financial references. This change does not assert end-to-end gateway idempotency, new refund/settlement correctness or serialised monthly quota allocation. Superuser access to database tools remains operationally privileged.

Non-superuser staff may receive HTTP 403 on financial writes until granted the mapped permission. API read access remains the existing coarse staff contract. Django admin cannot manually mark an earning settled, refund a payment or repair a balance: those operations require a referenced workflow, not a generic edit.

## Verification and preservation

See [FINANCIAL_ADMIN_AUDIT.md](../FINANCIAL_ADMIN_AUDIT.md) and the executed maintenance record in [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) for actual test results, files, recovery artifacts and remaining gates. No application data migration, ordinary database write or automatic permission grant is part of this decision.
