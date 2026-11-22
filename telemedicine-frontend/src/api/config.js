const LOCAL_HOSTNAMES = new Set(["localhost", "127.0.0.1", "::1"]);

const DEFAULT_API_BASE = LOCAL_HOSTNAMES.has(window.location.hostname)
  ? "http://127.0.0.1:8000"
  : window.location.origin;

export const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL?.replace(/\/$/, "") || DEFAULT_API_BASE;

export const MEDIA_BASE_URL =
  process.env.REACT_APP_MEDIA_BASE_URL?.replace(/\/$/, "") || API_BASE_URL;
