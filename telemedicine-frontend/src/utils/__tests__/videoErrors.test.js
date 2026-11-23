import {
  VIDEO_UNAVAILABLE_MESSAGE,
  getFriendlyVideoError,
  containsRawVideoConfigKeys,
} from "../videoErrors";

describe("getFriendlyVideoError", () => {
  test("hides raw Cloudflare config keys from API config.missing", () => {
    const err = {
      response: {
        data: {
          error: "cloudflare video is not configured. Missing or invalid: CLOUDFLARE_ACCOUNT_ID.",
          config: { missing: ["CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"] },
        },
      },
    };
    const message = getFriendlyVideoError(err);
    expect(message).toBe(VIDEO_UNAVAILABLE_MESSAGE);
    expect(containsRawVideoConfigKeys(message)).toBe(false);
    expect(message).not.toContain("CLOUDFLARE_");
  });

  test("hides raw keys embedded in error.message", () => {
    const err = new Error("Missing or invalid: CLOUDFLARE_CALLS_APP_ID");
    expect(getFriendlyVideoError(err)).toBe(VIDEO_UNAVAILABLE_MESSAGE);
  });

  test("passes through ordinary participant errors", () => {
    const err = { response: { data: { error: "There is no active video request to respond to." } } };
    expect(getFriendlyVideoError(err)).toBe("There is no active video request to respond to.");
  });
});
