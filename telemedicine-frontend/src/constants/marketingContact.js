export const SUPPORT_EMAIL = "support@irme.in";
export const WHATSAPP_NUMBER = "917037444888";
export const DISPLAY_PHONE = "+91 70374 44888";

export const whatsappUrl = (message) =>
  `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(message)}`;

