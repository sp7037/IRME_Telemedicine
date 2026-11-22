const AUTH_KEYS = ["token", "refresh_token", "userType", "doctorOnboarding"];

function safeStorage(storage) {
  try {
    const probe = "__irme_probe__";
    storage.setItem(probe, "1");
    storage.removeItem(probe);
    return storage;
  } catch (error) {
    return null;
  }
}

const session = typeof window !== "undefined" ? safeStorage(window.sessionStorage) : null;
const local = typeof window !== "undefined" ? safeStorage(window.localStorage) : null;

export function getAuthItem(key) {
  return session?.getItem(key) || local?.getItem(key) || "";
}

export function setAuthItem(key, value) {
  if (value == null) {
    removeAuthItem(key);
    return;
  }
  session?.setItem(key, value);
  local?.removeItem(key);
}

export function removeAuthItem(key) {
  session?.removeItem(key);
  local?.removeItem(key);
}

export function clearAuthSession() {
  AUTH_KEYS.forEach(removeAuthItem);
}

export function getAccessToken() {
  return getAuthItem("token").trim();
}

export function getRefreshToken() {
  return getAuthItem("refresh_token").trim();
}

export function getUserType() {
  return getAuthItem("userType");
}

export function getDoctorOnboarding() {
  try {
    return JSON.parse(getAuthItem("doctorOnboarding") || "{}");
  } catch (error) {
    return {};
  }
}

export function isJwtExpired(token) {
  if (!token || token.split(".").length < 2) return true;
  try {
    const payload = JSON.parse(window.atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    if (!payload.exp) return false;
    return payload.exp * 1000 <= Date.now();
  } catch (error) {
    return true;
  }
}
