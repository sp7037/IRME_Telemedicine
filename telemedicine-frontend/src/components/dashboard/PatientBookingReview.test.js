import React, { act } from "react";
import { createRoot } from "react-dom/client";

let container, root;
beforeEach(() => {
  global.IS_REACT_ACT_ENVIRONMENT = true;
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
  delete global.IS_REACT_ACT_ENVIRONMENT;
});
const render = (element) => act(() => root.render(element));
const button = (name) => Array.from(container.querySelectorAll("button")).find((el) => el.textContent === name);
const click = (name) => act(() => button(name).click());
import PatientBookingReview from "./PatientBookingReview";

const preview = { base_fee: "100.00", platform_fee: "20.00", total: "120.00", balance: "100.00", shortfall: "20.00", can_request: false };

test("low balance shows full price and blocks request while allowing funds navigation", () => {
  const confirm = jest.fn(), funds = jest.fn();
  render(<PatientBookingReview preview={preview} onConfirm={confirm} onFunds={funds} />);
  expect(container.querySelector('[role="alert"]').textContent).toContain("Add \u20b920.00");
  expect(container.textContent).toContain("Platform charge: \u20b920.00");
  click("Confirm and request consultation");
  expect(confirm).not.toHaveBeenCalled();
  click("Balance / add funds");
  expect(funds).toHaveBeenCalledTimes(1);
});

test("sufficient funds require explicit confirmation and cancellation does not book", () => {
  const confirm = jest.fn(), cancel = jest.fn();
  render(<PatientBookingReview preview={{ ...preview, can_request: true, balance: "120.00", shortfall: "0.00" }} onConfirm={confirm} onCancel={cancel} />);
  expect(confirm).not.toHaveBeenCalled();
  click("Cancel");
  expect(cancel).toHaveBeenCalledTimes(1);
  expect(confirm).not.toHaveBeenCalled();
  click("Confirm and request consultation");
  expect(confirm).toHaveBeenCalledTimes(1);
});
