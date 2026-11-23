import React, { act } from "react";
import { createRoot } from "react-dom/client";
import ConsultationPromptModal from "./ConsultationPromptModal";

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
const click = (name) =>
  act(() => {
    const btn = Array.from(container.querySelectorAll("button")).find((el) => el.textContent === name);
    btn.click();
  });

test("doctor acceptance modal stays until an action is chosen", () => {
  const openChat = jest.fn();
  const startVideo = jest.fn();
  const onClose = jest.fn();
  render(
    <ConsultationPromptModal
      open
      title="Consultation request accepted"
      message="Patient is ready."
      actions={[
        { key: "chat", label: "Open chat", variant: "primary", onClick: openChat },
        { key: "video", label: "Start video", variant: "secondary", onClick: startVideo },
      ]}
      onClose={onClose}
    />
  );
  expect(container.textContent).toContain("Consultation request accepted");
  expect(container.querySelector('[role="alertdialog"]')).toBeTruthy();
  click("Open chat");
  expect(openChat).toHaveBeenCalledTimes(1);
  click("Start video");
  expect(startVideo).toHaveBeenCalledTimes(1);
  click("Close");
  expect(onClose).toHaveBeenCalledTimes(1);
});

test("patient acceptance prompt shows waiting copy", () => {
  render(
    <ConsultationPromptModal
      open
      title="Dr Asha accepted your request. Waiting for the doctor to start the consultation."
      message="You can open the chat at any time."
      actions={[{ key: "chat", label: "Open chat", variant: "primary", onClick: jest.fn() }]}
      onClose={jest.fn()}
    />
  );
  expect(container.textContent).toContain("Waiting for the doctor to start the consultation");
  expect(container.textContent).toContain("Open chat");
});

test("chat-started prompt shows message preview and Reply", () => {
  const reply = jest.fn();
  render(
    <ConsultationPromptModal
      open
      title="Doctor started the chat, please reply"
      message="A new message from your doctor is waiting."
      preview="Please share your symptoms."
      actions={[{ key: "reply", label: "Reply", variant: "primary", onClick: reply }]}
      onClose={jest.fn()}
    />
  );
  expect(container.textContent).toContain("Please share your symptoms.");
  expect(container.textContent).toContain("Latest message");
  click("Reply");
  expect(reply).toHaveBeenCalledTimes(1);
});

test("video request modal requires Join video or Continue in chat", () => {
  const join = jest.fn();
  const chat = jest.fn();
  render(
    <ConsultationPromptModal
      open
      title="Doctor requested video"
      message="Join video when you are ready, or continue in chat."
      pulse
      actions={[
        { key: "join", label: "Join video", variant: "primary", onClick: join },
        { key: "chat", label: "Continue in chat", variant: "secondary", onClick: chat },
      ]}
    />
  );
  expect(container.textContent).toContain("Doctor requested video");
  expect(Array.from(container.querySelectorAll("button")).map((b) => b.textContent)).toEqual([
    "Join video",
    "Continue in chat",
  ]);
  click("Continue in chat");
  expect(chat).toHaveBeenCalledTimes(1);
});

test("doctor decline notice offers chat and request again", () => {
  const openChat = jest.fn();
  const again = jest.fn();
  render(
    <ConsultationPromptModal
      open
      title="Patient chose to continue in chat"
      message="Patient declined video. Chat remains available."
      actions={[
        { key: "chat", label: "Open chat", variant: "primary", onClick: openChat },
        { key: "again", label: "Request video again", variant: "secondary", onClick: again },
      ]}
      onClose={jest.fn()}
    />
  );
  expect(container.textContent).toContain("Patient chose to continue in chat");
  click("Request video again");
  expect(again).toHaveBeenCalledTimes(1);
});
