function comparable(value) {
  if (Array.isArray(value)) return JSON.stringify([...value].sort());
  return String(value ?? "").trim();
}

export function changedDoctorProfileFields(form, initialForm) {
  return Object.fromEntries(
    Object.entries(form).filter(([key, value]) => comparable(value) !== comparable(initialForm?.[key]))
  );
}

export function doctorProfileErrorMessages(value, path = "") {
  if (Array.isArray(value)) {
    return value.flatMap((item) => doctorProfileErrorMessages(item, path));
  }
  if (value && typeof value === "object") {
    return Object.entries(value).flatMap(([key, item]) => {
      const nextPath = /^\d+$/.test(key)
        ? `${path}[${Number(key) + 1}]`
        : [path, key].filter(Boolean).join(".");
      return doctorProfileErrorMessages(item, nextPath);
    });
  }
  if (value == null || value === "") return [];
  return [path ? `${path}: ${String(value)}` : String(value)];
}
