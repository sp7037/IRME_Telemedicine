import React, { act } from "react";
import { createRoot } from "react-dom/client";
import PatientBookingReview from "./PatientBookingReview";

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

const preview = {
  base_fee: "100.00",
  platform_fee: "20.00",
  total: "120.00",
  balance: "100.00",
  shortfall: "20.00",
  can_request: false,
};

const doctor = {
  id: 7,
  first_name: "Asha",
  last_name: "Mehta",
  specialty: "Cardiology",
  photo: null,
};

test("low balance shows full price and blocks request while allowing funds navigation", () => {
  const confirm = jest.fn(), funds = jest.fn();
  render(<PatientBookingReview preview={preview} doctor={doctor} onConfirm={confirm} onFunds={funds} />);
  expect(container.querySelector('[role="alert"]').textContent).toContain("Add \u20b920.00");
  expect(container.textContent).toContain("Base fee");
  expect(container.textContent).toContain("\u20b9100.00");
  expect(container.textContent).toContain("Platform charge");
  expect(container.textContent).toContain("\u20b920.00");
  expect(container.textContent).toContain("Total");
  expect(container.textContent).toContain("\u20b9120.00");
  expect(container.textContent).toContain("Current balance");
  expect(container.textContent).toContain("Balance after payment");
  expect(container.textContent).toContain("Dr. Asha Mehta");
  expect(container.textContent).toContain("Cardiology");
  click("Confirm and request consultation");
  expect(confirm).not.toHaveBeenCalled();
  click("Add funds");
  expect(funds).toHaveBeenCalledTimes(1);
});

test("sufficient funds require explicit confirmation and cancellation does not book", () => {
  const confirm = jest.fn(), cancel = jest.fn();
  render(
    <PatientBookingReview
      preview={{ ...preview, can_request: true, balance: "120.00", shortfall: "0.00" }}
      doctor={doctor}
      onConfirm={confirm}
      onCancel={cancel}
    />
  );
  expect(container.textContent).toContain("Doctor acceptance is still required");
  expect(container.textContent).toContain("Balance after payment");
  expect(container.textContent).toContain("\u20b90.00");
  expect(confirm).not.toHaveBeenCalled();
  click("Cancel");
  expect(cancel).toHaveBeenCalledTimes(1);
  expect(confirm).not.toHaveBeenCalled();
  click("Confirm and request consultation");
  expect(confirm).toHaveBeenCalledTimes(1);
});

test("busy state disables all actions and shows processing label", () => {
  const confirm = jest.fn(), cancel = jest.fn(), funds = jest.fn();
  render(
    <PatientBookingReview
      preview={{ ...preview, can_request: true, balance: "120.00", shortfall: "0.00" }}
      doctor={doctor}
      busy
      onConfirm={confirm}
      onCancel={cancel}
      onFunds={funds}
    />
  );
  expect(button("Processing…")).toBeTruthy();
  expect(button("Processing…").disabled).toBe(true);
  expect(button("Add funds").disabled).toBe(true);
  expect(button("Cancel").disabled).toBe(true);
});
