jest.mock("axios", () => {
  const client = {
    patch: jest.fn(),
    interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
  };
  return { __esModule: true, default: { create: jest.fn(() => client) } };
});

import axios from "axios";
import { updateDoctorProfile } from "./users";
import { changedDoctorProfileFields } from "../utils/doctorProfileForm";

const client = axios.create.mock.results[0].value;
let errorLog;

beforeEach(() => {
  client.patch.mockReset();
  errorLog = jest.spyOn(console, "error").mockImplementation(() => {});
});

afterEach(() => errorLog.mockRestore());

test("photo-only edit omits unchanged modes and all untouched profile fields", async () => {
  const original = { specialty: "Demo", consultation_modes: ["online"], consultation_fee: "100.00" };
  const changes = changedDoctorProfileFields({ ...original }, original);
  const photo = new File(["test photo"], "portrait.png", { type: "image/png" });
  client.patch.mockResolvedValueOnce({ data: { change_request_created: true } });

  const result = await updateDoctorProfile({ ...changes, photo });

  expect(result.change_request_created).toBe(true);
  const [url, formData, options] = client.patch.mock.calls[0];
  expect(url).toBe("/consultations/doctor/profile/");
  expect([...formData.keys()]).toEqual(["photo"]);
  expect(formData.get("photo")).toBe(photo);
  expect(options.headers).toBeUndefined(); // Browser owns the multipart boundary.
});

test("edited consultation modes retain repeated multipart values alongside the photo", async () => {
  client.patch.mockResolvedValueOnce({ data: {} });
  await updateDoctorProfile({ consultation_modes: ["VIDEO", "CHAT"], photo: new File(["x"], "p.png") });
  const data = client.patch.mock.calls[0][1];
  expect(data.getAll("consultation_modes")).toEqual(["VIDEO", "CHAT"]);
  expect(data.has("photo")).toBe(true);
});

test("unchanged number formats and mode order do not become profile edits", () => {
  expect(changedDoctorProfileFields(
    { passing_year: "2011", consultation_modes: ["CHAT", "VIDEO"], specialty: "New specialty" },
    { passing_year: 2011, consultation_modes: ["VIDEO", "CHAT"], specialty: "Old specialty" }
  )).toEqual({ specialty: "New specialty" });
});

test("nested mode validation renders the actual message rather than object Object", async () => {
  client.patch.mockRejectedValueOnce({ response: {
    status: 400, data: { error: { consultation_modes: { 0: ['"online" is not a valid choice.'] } } },
  } });
  await expect(updateDoctorProfile({ consultation_modes: ["online"] }))
    .rejects.toThrow('consultation_modes[1]: "online" is not a valid choice.');
});

test("clearing all modes is rejected explicitly rather than silently omitted", async () => {
  await expect(updateDoctorProfile({ consultation_modes: [] })).rejects.toThrow("Select at least one consultation mode");
  expect(client.patch).not.toHaveBeenCalled();
});
