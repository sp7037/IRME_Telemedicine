import React from "react";
import { useTranslation } from "react-i18next";
import theme from "../theme/tokens";

/**
 * Language switcher component
 * Allows users to change the application language
 */
const LanguageSwitcher = ({ style = {}, compact = false }) => {
  const { i18n, t } = useTranslation();

  const languages = [
    { code: "en", label: "English", nativeLabel: "English" },
    { code: "hi", label: "Hindi", nativeLabel: "हिंदी" },
    { code: "mr", label: "Marathi", nativeLabel: "मराठी" },
  ];

  const handleLanguageChange = (e) => {
    const newLang = e.target.value;
    i18n.changeLanguage(newLang);
  };

  const selectStyles = {
    padding: compact ? `${theme.spacing[1]} ${theme.spacing[2]}` : `${theme.spacing[2]} ${theme.spacing[3]}`,
    borderRadius: theme.radii.md,
    border: `1px solid ${theme.colors.border.medium}`,
    backgroundColor: theme.colors.background.primary,
    color: theme.colors.text.primary,
    fontSize: compact ? theme.typography.fontSize.sm : theme.typography.fontSize.base,
    cursor: "pointer",
    transition: `border-color ${theme.transitions.fast}`,
    fontFamily: theme.typography.fontFamily.base,
    ...style,
  };

  return (
    <select
      value={i18n.language}
      onChange={handleLanguageChange}
      style={selectStyles}
      onFocus={(e) => {
        e.target.style.outline = "none";
        e.target.style.borderColor = theme.colors.border.focus;
      }}
      onBlur={(e) => {
        e.target.style.borderColor = theme.colors.border.medium;
      }}
      aria-label={t("language.selectLanguage")}
    >
      {languages.map((lang) => (
        <option key={lang.code} value={lang.code}>
          {compact ? lang.code.toUpperCase() : lang.nativeLabel}
        </option>
      ))}
    </select>
  );
};

export default LanguageSwitcher;
