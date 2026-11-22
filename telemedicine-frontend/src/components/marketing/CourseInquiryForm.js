import React, { useState } from "react";
import { m } from "../../constants/marketingLayout";

const SUPPORT_EMAIL = "support@irme.in";

const CourseInquiryForm = () => {
  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    district: "",
    message: "",
  });
  const [submitted, setSubmitted] = useState(false);

  const onChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const onSubmit = (e) => {
    e.preventDefault();
    const body = `Name: ${form.name}\nPhone: ${form.phone}\nEmail: ${form.email}\nDistrict/State: ${form.district}\n\nMessage:\n${form.message}`;
    const href = `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(
      "Telemedicine Support Program — Inquiry"
    )}&body=${encodeURIComponent(body)}`;
    window.location.href = href;
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <p style={m.sectionBody}>
        Thank you. If your mail app did not open, please email{" "}
        <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a> with your name and contact
        details.
      </p>
    );
  }

  return (
    <form
      onSubmit={onSubmit}
      style={{
        marginTop: "18px",
        display: "grid",
        gap: "14px",
        maxWidth: "520px",
      }}
    >
      <input
        name="name"
        required
        placeholder="Full name"
        value={form.name}
        onChange={onChange}
        className="auth-input"
      />
      <input
        name="phone"
        required
        placeholder="Mobile number"
        value={form.phone}
        onChange={onChange}
        className="auth-input"
      />
      <input
        name="email"
        type="email"
        placeholder="Email (optional)"
        value={form.email}
        onChange={onChange}
        className="auth-input"
      />
      <input
        name="district"
        placeholder="District / State"
        value={form.district}
        onChange={onChange}
        className="auth-input"
      />
      <textarea
        name="message"
        placeholder="Tell us about your background and what you hope to learn"
        value={form.message}
        onChange={onChange}
        rows={4}
        className="auth-input"
        style={{ height: "auto", paddingTop: "10px", paddingBottom: "10px" }}
      />
      <button type="submit" className="site-cta-green" style={m.btnPrimary}>
        Submit inquiry
      </button>
    </form>
  );
};

export default CourseInquiryForm;
