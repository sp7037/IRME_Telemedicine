# ADR 0006: Direct patient checkout direction and safe testing

Date: 2026-11-21. Status: patient product direction accepted from the owner's instruction; local funding and current-price preflight implemented in this slice. Direct gateway-to-booking checkout remains unimplemented.

## Decision

The target direct-patient experience is: select doctor, review the full consultation price, pay for that consultation, then send/confirm the booking and await doctor acceptance. A separately prefunded patient wallet is not the intended primary flow. TMCs continue to use their owned wallets and existing eligibility rules. Patients need payment/refund history, not a requirement to maintain a spending balance.

This resolves the product direction of P07 for direct checkout. It does not resolve new follow-up pricing, authorize erasing legacy patient balances/history, change the already accepted cancellation rules or make independent doctor payable depend on patient/TMC charges. The owner's example direct price 100 with retention 20 means a total of 100 and payable 80, not a surcharge to 120; the current legacy surcharge remains explicitly visible until the coherent pricing change is implemented.

## Immediate implementation

Make local testing possible with existing permission-checked admin top-ups and an explicit local-only management command. All credits have labelled ledger/audit records; there is no patient self-credit, disabled signature verification or simulated production gateway success. Never change unidentified ordinary users' balances automatically.

Before sending a current wallet-backed booking, show a server-computed fee breakdown, own balance, shortfall and explicit confirmation. Display a patient balance/history shortcut by Profile. Protect the confirmed total as a comparison against server pricing, including rollback on changed actual charge. This improves current safety without presenting wallet funding as direct pay-per-consultation.

## Required next checkout design/implementation

True per-consultation checkout needs a server-priced payment intent bound to doctor/patient/source, stable operation and gateway references, signature/captured amount/currency/order verification, replay-safe posting, and a defined outcome if payment succeeds but availability changes. Page closure and delayed/duplicate webhooks must not lose the payment or create two bookings. Never start clinical service or claim a booking merely because a client-side checkout callback reports success.

Review slot/price expiry and compensation/actual-refund handling within ADR 0002 before enabling the new path. Preserve legacy credits with an explicit transition strategy; do not silently zero, transfer, reinterpret or hide their balances. No automatic wallet recharge plus booking retry is disguised as the final direct checkout design.

Build this as the next reviewed financial work after the necessary dormant operation/posting/quote foundations. The owner has authorised the direction; do not re-ask whether a prefunded patient wallet is desired. Remaining mechanics require their technical and relevant business-rule review. The single-table G1A contract is not expanded by this ADR, and no new table is added here.

## Evidence

See [patient testing guide](../PATIENT_PAYMENT_TESTING.md) and the executed record in [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) for source, verification and recovery. Do not label direct gateway checkout delivered or tested from the current wallet preflight tests.
