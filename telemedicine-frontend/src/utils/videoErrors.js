/**
 * Friendly video error messages for participants.
 * Never surface raw env/config keys (CLOUDFLARE_*, etc.) in the UI.
 */

const CONFIG_KEY_PATTERN = /CLOUDFLARE_[A-Z0-9_]+|video is not configured|Missing or invalid:/i;

export const VIDEO_UNAVAILABLE_MESSAGE =
  "Video is temporarily unavailable. Please continue in chat.";

/**
 * @param {unknown} err - axios/API error or Error
 * @param {string} [fallback]
 * @returns {string}
 */
export function getFriendlyVideoError(err, fallback = VIDEO_UNAVAILABLE_MESSAGE) {
  const data = err?.response?.data;
  const raw = data?.error || err?.message || "";
  const missing = Array.isArray(data?.config?.missing) ? data.config.missing : [];

  if (missing.length > 0 || CONFIG_KEY_PATTERN.test(String(raw))) {
    return VIDEO_UNAVAILABLE_MESSAGE;
  }

  if (raw && !CONFIG_KEY_PATTERN.test(String(raw))) {
    return String(raw);
  }

  return fallback;
}

/**
 * True when a message string still contains raw config/env keys (for tests/guards).
 */
export function containsRawVideoConfigKeys(text) {
  return CONFIG_KEY_PATTERN.test(String(text || ""));
}
