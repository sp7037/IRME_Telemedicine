import { useEffect } from "react";

const upsertMeta = (selector, createAttrs, content) => {
  let tag = document.head.querySelector(selector);
  if (!tag) {
    tag = document.createElement("meta");
    Object.entries(createAttrs).forEach(([key, value]) => tag.setAttribute(key, value));
    document.head.appendChild(tag);
  }
  tag.setAttribute("content", content);
};

const upsertLink = (rel, href) => {
  let tag = document.head.querySelector(`link[rel="${rel}"]`);
  if (!tag) {
    tag = document.createElement("link");
    tag.setAttribute("rel", rel);
    document.head.appendChild(tag);
  }
  tag.setAttribute("href", href);
};

const Seo = ({ title, description, canonical, keywords, schema }) => {
  useEffect(() => {
    const url = canonical || window.location.href;
    document.title = title;
    upsertMeta('meta[name="description"]', { name: "description" }, description);
    if (keywords) upsertMeta('meta[name="keywords"]', { name: "keywords" }, keywords);
    upsertMeta('meta[property="og:title"]', { property: "og:title" }, title);
    upsertMeta('meta[property="og:description"]', { property: "og:description" }, description);
    upsertMeta('meta[property="og:url"]', { property: "og:url" }, url);
    upsertMeta('meta[property="og:type"]', { property: "og:type" }, "website");
    upsertMeta('meta[name="twitter:card"]', { name: "twitter:card" }, "summary_large_image");
    upsertLink("canonical", url);

    let script = document.head.querySelector('script[data-irme-schema="true"]');
    if (!script) {
      script = document.createElement("script");
      script.type = "application/ld+json";
      script.setAttribute("data-irme-schema", "true");
      document.head.appendChild(script);
    }
    script.textContent = JSON.stringify(schema || {
      "@context": "https://schema.org",
      "@type": "Organization",
      name: "IRME Telemedicine",
      url,
      areaServed: "India",
    });
  }, [title, description, canonical, keywords, schema]);

  return null;
};

export default Seo;

