import { postponementOutcome } from "./PostponementOutcome";

test("patient rejection explains next steps and reports only a confirmed original-payer return", () => {
  const outcome = postponementOutcome({ status: "REJECTED_BY_PATIENT", wallet_return: {
    status: "RETURNED", amount: "120.00", destination: "patient wallet", reference: "PWR-1",
  } });
  expect(outcome.body).toContain("another doctor");
  expect(outcome.body).toContain("120.00 returned");
  expect(outcome.body).toContain("PWR-1");
});

test("doctor sees patient decision and a TMC return is not described as patient credit", () => {
  const outcome = postponementOutcome({ status: "REJECTED_BY_PATIENT", wallet_return: {
    status: "RETURNED", amount: "90.00", destination: "TMC wallet", reference: "TWR-1",
  } }, "doctor");
  expect(outcome.title).toContain("Patient declined");
  expect(outcome.body).toContain("TMC wallet");
});

test("unconfirmed historical or review cases never promise a completed refund", () => {
  for (const wallet_return of [{}, { status: "REVIEW_REQUIRED" }]) {
    expect(postponementOutcome({ status: "REJECTED_BY_PATIENT", wallet_return }).body).toContain("has not been confirmed");
  }
  expect(postponementOutcome({ status: "PENDING" })).toBeNull();
});
