/**
 * African country flags lookup table
 */
export const AFRICAN_FLAGS = {
  "algeria": "🇩🇿", "angola": "🇦🇴", "benin": "🇧🇯", "botswana": "🇧🇼", "burkina-faso": "🇧🇫",
  "burundi": "🇧🇮", "cabo-verde": "🇨🇻", "cameroon": "🇨🇲", "central-african-republic": "🇨🇫",
  "chad": "🇹🇩", "comoros": "🇰🇲", "congo-brazzaville": "🇨🇬", "congo-kinshasa": "🇨🇩",
  "drc": "🇨🇩", "drc-(congo)": "🇨🇩", "djibouti": "🇩🇯", "egypt": "🇪🇬", "equatorial-guinea": "🇬🇶",
  "eritrea": "🇪🇷", "eswatini": "🇸🇿", "ethiopia": "🇪🇹", "gabon": "🇬🇦", "gambia": "🇬🇲",
  "ghana": "🇬🇭", "guinea": "🇬🇳", "guinea-bissau": "🇬🇼", "ivory-coast": "🇨🇮", "kenya": "🇰🇪",
  "lesotho": "🇱🇸", "liberia": "🇱🇷", "libya": "🇱🇾", "madagascar": "🇲🇬", "malawi": "🇲🇼",
  "mali": "🇲🇱", "mauritania": "🇲🇷", "mauritius": "🇲🇺", "morocco": "🇲🇦", "mozambique": "🇲🇿",
  "namibia": "🇳🇦", "niger": "🇳🇪", "nigeria": "🇳🇬", "rwanda": "🇷🇼", "sao-tome-and-principe": "🇸🇹",
  "senegal": "🇸🇳", "seychelles": "🇸🇨", "sierra-leone": "🇸🇱", "somalia": "🇸🇴", "south-africa": "🇿🇦",
  "south-sudan": "🇸🇸", "sudan": "🇸🇩", "tanzania": "🇹🇿", "togo": "🇹🇬", "tunisia": "🇹🇳",
  "uganda": "🇺🇬", "zambia": "🇿🇲", "zimbabwe": "🇿🇼"
};

/**
 * Safely parse JSON strings
 */
export function safeJsonParse(jsonString, fallback) {
  if (!jsonString) return fallback;
  try {
    return JSON.parse(jsonString);
  } catch (e) {
    return fallback;
  }
}

/**
 * Format Plot entity for API responses
 */
export function serializePlot(p) {
  if (!p) return null;
  return {
    id: p.id,
    title: p.title,
    size: p.size,
    price: Number(p.price),
    neighborhood: p.neighborhood,
    owner_username: p.owner_username,
    country_id: p.country_id,
    photos: safeJsonParse(p.photos, []),
    isVisible: Boolean(p.is_visible)
  };
}

/**
 * Format Country entity with nested plots
 */
export function serializeCountry(c, plots = []) {
  if (!c) return null;
  return {
    id: c.id,
    name: c.name,
    flag: c.flag || "🌍",
    motto: c.motto || "",
    accent: c.accent || "#1A3E26",
    desc: c.desc || "",
    videoUrl: c.video_url || "",
    highlights: safeJsonParse(c.highlights, []),
    potentialNeighborhoods: safeJsonParse(c.potential_neighborhoods, []),
    cultureInfo: safeJsonParse(c.culture_info, {}),
    plots: plots.map(serializePlot),
    isVisible: Boolean(c.is_visible)
  };
}

/**
 * Format Inquiry entity
 */
export function serializeInquiry(inq, plotTitle = "Unknown Plot", countryName = "Unknown") {
  if (!inq) return null;
  return {
    id: inq.id,
    plot_id: inq.plot_id,
    plotTitle: plotTitle,
    fullName: inq.full_name,
    email: inq.email,
    phone: inq.phone,
    currentCity: inq.current_city,
    message: inq.message,
    type: inq.type,
    timestamp: inq.timestamp,
    countryName: countryName
  };
}
