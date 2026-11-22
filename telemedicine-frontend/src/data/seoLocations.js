export const seoStates = [
  { name: "Uttar Pradesh", slug: "uttar-pradesh", short: "UP" },
  { name: "Bihar", slug: "bihar" },
  { name: "Delhi", slug: "delhi" },
  { name: "Haryana", slug: "haryana" },
  { name: "Rajasthan", slug: "rajasthan" },
  { name: "Uttarakhand", slug: "uttarakhand" },
  { name: "Madhya Pradesh", slug: "madhya-pradesh", short: "MP" },
];

export const seoCities = [
  { name: "Muzaffarnagar", slug: "muzaffarnagar", stateSlug: "uttar-pradesh" },
  { name: "Saharanpur", slug: "saharanpur", stateSlug: "uttar-pradesh" },
  { name: "Meerut", slug: "meerut", stateSlug: "uttar-pradesh" },
  { name: "Ghaziabad", slug: "ghaziabad", stateSlug: "uttar-pradesh" },
  { name: "Noida", slug: "noida", stateSlug: "uttar-pradesh" },
  { name: "Lucknow", slug: "lucknow", stateSlug: "uttar-pradesh" },
  { name: "Kanpur", slug: "kanpur", stateSlug: "uttar-pradesh" },
  { name: "Prayagraj", slug: "prayagraj", stateSlug: "uttar-pradesh" },
  { name: "Varanasi", slug: "varanasi", stateSlug: "uttar-pradesh" },
  { name: "Gorakhpur", slug: "gorakhpur", stateSlug: "uttar-pradesh" },
  { name: "Bareilly", slug: "bareilly", stateSlug: "uttar-pradesh" },
  { name: "Agra", slug: "agra", stateSlug: "uttar-pradesh" },
  { name: "Aligarh", slug: "aligarh", stateSlug: "uttar-pradesh" },
  { name: "Patna", slug: "patna", stateSlug: "bihar" },
  { name: "Gaya", slug: "gaya", stateSlug: "bihar" },
  { name: "Delhi", slug: "delhi", stateSlug: "delhi" },
  { name: "Gurugram", slug: "gurugram", stateSlug: "haryana" },
  { name: "Faridabad", slug: "faridabad", stateSlug: "haryana" },
  { name: "Jaipur", slug: "jaipur", stateSlug: "rajasthan" },
  { name: "Dehradun", slug: "dehradun", stateSlug: "uttarakhand" },
  { name: "Bhopal", slug: "bhopal", stateSlug: "madhya-pradesh" },
  { name: "Indore", slug: "indore", stateSlug: "madhya-pradesh" },
];

export const getStateBySlug = (slug) => seoStates.find((state) => state.slug === slug);
export const getCityBySlug = (stateSlug, citySlug) =>
  seoCities.find((city) => city.stateSlug === stateSlug && city.slug === citySlug);
export const citiesForState = (stateSlug) => seoCities.filter((city) => city.stateSlug === stateSlug);

export const seoPageUrls = [
  "/",
  "/tmc",
  "/telemedicine-centers/join",
  "/telemedicine-course",
  ...seoStates.flatMap((state) => [
    `/telemedicine-center/${state.slug}`,
    `/telemedicine-assistant-course/${state.slug}`,
  ]),
  ...seoCities.flatMap((city) => [
    `/telemedicine-center/${city.stateSlug}/${city.slug}`,
    `/telemedicine-assistant-course/${city.stateSlug}/${city.slug}`,
  ]),
];

