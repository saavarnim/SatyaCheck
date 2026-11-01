// web/heatmap.js – Leaflet Heatmap Layer & Fallback Renderer for SatyaCheck
// Implements Task F3 per specs:
// - Leaflet.heat 0.2.0 integration with gradient: yellow -> orange -> red
// - Weight = count / maxCount in view
// - Fallback: 3 concentric translucent circles per cluster (r, 0.6r, 0.3r) in severity colour
// - Colours: MED amber #F2B01E, HIGH orange #F57C00, CRIT red #D32F2F
// - Areas with no reports in window: faint green dots with popup and legend explanation
// - Numbered marker on every cluster + text badges (A few reports / Many / Very many)
// - Legend in bottom-left in EN & HI with config thresholds
// - Tap popup with area, count, top scam in plain words, one-line safety advice, "Check a number" link
// - Sorted list under map by severity (CRIT -> HIGH -> MED)

import { t, getLanguage } from "./i18n.js";

// Specific severity colors required by specification
export const SEV_COLORS = {
  CRIT: "#D32F2F", // Red (10 or more)
  HIGH: "#F57C00", // Orange (5-9)
  MED: "#F2B01E",  // Amber (below 5)
  ZERO: "#10b981", // Faint green for areas with no reports
};

// Plain-words naming & actionable safety advice for each scam type
export const SCAM_DETAILS = {
  "digital-arrest": {
    en: "Digital Arrest",
    hi: "डिजिटल अरेस्ट",
    advice_en: "Police or CBI never conduct court trials or make arrests over video calls.",
    advice_hi: "पुलिस या जांच एजेंसियां कभी वीडियो कॉल पर कोर्ट या गिरफ्तारी नहीं करती हैं।",
  },
  "fake-kyc-link": {
    en: "Fake KYC Link",
    hi: "फर्जी केवाईसी लिंक",
    advice_en: "Banks never ask you to update KYC via SMS or WhatsApp links.",
    advice_hi: "बैंक कभी भी एसएमएस या व्हाट्सएप लिंक से केवाईसी अपडेट नहीं मांगते।",
  },
  "upi-refund-qr": {
    en: "UPI Refund QR",
    hi: "यूपीआई रिफंड क्यूआर",
    advice_en: "You never need to enter your UPI PIN or scan a QR code to receive money.",
    advice_hi: "पैसे प्राप्त करने के लिए कभी भी पिन दर्ज करने या क्यूआर स्कैन करने की आवश्यकता नहीं होती।",
  },
  "investment-group": {
    en: "Investment Scam",
    hi: "फर्जी निवेश ग्रुप",
    advice_en: "Beware of WhatsApp or Telegram groups promising guaranteed stock returns.",
    advice_hi: "व्हाट्सएप या टेलीग्राम पर भारी मुनाफे का दावा करने वाले ग्रुपों से सावधान रहें।",
  },
  "courier-customs": {
    en: "Courier / Customs",
    hi: "कूरियर / कस्टम्स",
    advice_en: "Customs officers never demand parcel clearance fees into personal bank accounts.",
    advice_hi: "कस्टम अधिकारी कभी भी व्यक्तिगत बैंक खातों में पार्सल शुल्क नहीं मांगते।",
  },
  "job-offer": {
    en: "Job Offer Scam",
    hi: "फर्जी नौकरी का झांसा",
    advice_en: "Legitimate employers never demand registration fees or paid task deposits.",
    advice_hi: "वास्तविक कंपनियां कभी नौकरी के बदले कोई शुल्क या टास्क डिपॉजिट नहीं मांगतीं।",
  },
  "lottery-prize": {
    en: "Lottery / Prize",
    hi: "लॉटरी / इनाम स्कैम",
    advice_en: "You cannot win a lottery you never entered; never pay fees to claim prizes.",
    advice_hi: "जिस लॉटरी का टिकट नहीं खरीदा वह नहीं जीती जा सकती; इनाम के लिए कोई शुल्क न दें।",
  },
  "loan-app-harassment": {
    en: "Loan App Harassment",
    hi: "लोन ऐप उत्पीड़न",
    advice_en: "Borrow only from RBI-registered lenders; report blackmail to helpline 1930.",
    advice_hi: "केवल आरबीआई-मान्यता प्राप्त ऐप से ही ऋण लें; उत्पीड़न की तुरंत 1930 पर शिकायत करें।",
  },
  "electricity-disconnection": {
    en: "Electricity Threat",
    hi: "बिजली बिल डिस्कनेक्शन",
    advice_en: "Power boards never send disconnection threats from personal 10-digit mobile numbers.",
    advice_hi: "बिजली विभाग व्यक्तिगत मोबाइल नंबरों से कनेक्शन काटने की धमकी नहीं भेजता।",
  },
  "fake-customer-care": {
    en: "Fake Customer Care",
    hi: "फर्जी कस्टमर केयर",
    advice_en: "Always find customer support numbers on official apps or websites, not search ads.",
    advice_hi: "हेल्पलाइन नंबर हमेशा आधिकारिक ऐप या वेबसाइट से ही लें, सर्च विज्ञापनों से नहीं।",
  },
  "otp-call": {
    en: "OTP / PIN Call",
    hi: "ओटीपी / पिन कॉल",
    advice_en: "Never share OTPs, CVV, or passwords with anyone over a call or message.",
    advice_hi: "कॉल या मैसेज पर कभी भी अपना ओटीपी, पासवर्ड या पिन किसी से साझा न करें।",
  },
  "sextortion": {
    en: "Video Call Blackmail",
    hi: "वीडियो कॉल ब्लैकमेल",
    advice_en: "Do not transfer money; preserve evidence and contact cyber helpline 1930 immediately.",
    advice_hi: "पैसे न भेजें; सबूत सुरक्षित रखें और तुरंत साइबर हेल्पलाइन 1930 पर संपर्क करें।",
  },
  "other": {
    en: "Suspicious Activity",
    hi: "संदेहास्पद गतिविधि",
    advice_en: "Never transfer money or share private details with unverified contacts.",
    advice_hi: "अज्ञात संपर्कों को कभी पैसे न भेजें और न ही निजी जानकारी साझा करें।",
  },
};

/**
 * Escape HTML utility to avoid XSS in dynamically injected templates
 */
function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Return severity metadata (CRIT, HIGH, MED) with config thresholds and bilingual badges
 */
export function getSeverityInfo(count, severity, lang = getLanguage()) {
  const isHi = lang === "hi";
  let sev = severity;
  if (!sev) {
    if (count >= 10) sev = "CRIT";
    else if (count >= 5) sev = "HIGH";
    else sev = "MED";
  }

  if (sev === "CRIT") {
    return {
      severity: "CRIT",
      color: SEV_COLORS.CRIT,
      badge: isHi ? "अत्यधिक रिपोर्टें" : "Very many",
      threshold: isHi ? "10 या अधिक" : "10 or more",
      label: isHi ? "गंभीर गतिविधि" : "Critical Activity",
    };
  }
  if (sev === "HIGH") {
    return {
      severity: "HIGH",
      color: SEV_COLORS.HIGH,
      badge: isHi ? "कई रिपोर्टें" : "Many",
      threshold: isHi ? "5–9" : "5–9",
      label: isHi ? "उच्च गतिविधि" : "High Activity",
    };
  }
  return {
    severity: "MED",
    color: SEV_COLORS.MED,
    badge: isHi ? "कुछ रिपोर्टें" : "A few reports",
    threshold: isHi ? "5 से कम" : "below 5",
    label: isHi ? "मध्यम गतिविधि" : "Moderate Activity",
  };
}

/**
 * Return human-friendly scam name & safety advice
 */
export function getScamInfo(scamType, lang = getLanguage()) {
  const isHi = lang === "hi";
  const key = scamType || "other";
  const detail = SCAM_DETAILS[key];
  if (detail) {
    return {
      name: isHi ? detail.hi : detail.en,
      advice: isHi ? detail.advice_hi : detail.advice_en,
    };
  }
  // Fallback for custom or unknown types
  const readable = key
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
  return {
    name: readable,
    advice: isHi
      ? "अज्ञात संपर्कों को कभी पैसे न भेजें और न ही निजी जानकारी साझा करें।"
      : "Never transfer money or share private details with unverified contacts.",
  };
}

/**
 * Build rich tap popup for an active cluster
 */
export function buildClusterPopup(cluster, lang = getLanguage()) {
  const isHi = lang === "hi";
  const sevInfo = getSeverityInfo(cluster.count, cluster.severity, lang);
  const scamInfo = getScamInfo(cluster.top_scam_type, lang);

  const areaName = `${escapeHtml(cluster.locality || "")}, ${escapeHtml(cluster.city || "")}`;
  const pincodeStr = cluster.pincode ? ` (${cluster.pincode})` : "";
  const reportsLabel = isHi ? "स्वतंत्र रिपोर्टें" : "independent reports";
  const scamLabel = isHi ? "शीर्ष स्कैम प्रकार" : "Top scam type";
  const checkLinkText = isHi ? "🔍 नंबर या खाता चेक करें" : "🔍 Check a number";

  return `
    <div class="map-popup-card">
      <div class="popup-header">
        <div class="popup-title">${areaName}${pincodeStr}</div>
        <span class="popup-badge badge-${sevInfo.severity}">
          ${sevInfo.severity} • ${sevInfo.badge}
        </span>
      </div>
      <div class="popup-count-box">
        <span class="popup-count-number">${cluster.count}</span>
        <span class="popup-count-desc">${reportsLabel}</span>
      </div>
      <div class="popup-info-row">
        <span class="popup-label">${scamLabel}:</span>
        <span class="popup-value"><strong>${escapeHtml(scamInfo.name)}</strong></span>
      </div>
      <div class="popup-advice-box">
        <span class="popup-advice-icon">💡</span>
        <span class="popup-advice-text">${escapeHtml(scamInfo.advice)}</span>
      </div>
      <div class="popup-footer">
        <a href="#/check" class="popup-check-link">${checkLinkText}</a>
      </div>
    </div>
  `;
}

/**
 * Build tap popup for areas with no reports in current window
 */
export function buildZeroClusterPopup(area, lang = getLanguage()) {
  const isHi = lang === "hi";
  const areaName = `${escapeHtml(area.locality || "")}, ${escapeHtml(area.city || "")}`;
  const pincodeStr = area.pincode ? ` (${area.pincode})` : "";
  const zeroStatusText = isHi
    ? "इस अवधि में कोई रिपोर्ट दर्ज नहीं हुई"
    : "No reports in this period";
  const reportLinkText = isHi ? "📢 कोई घटना रिपोर्ट करें" : "📢 Report a sighting";

  return `
    <div class="map-popup-card">
      <div class="popup-header">
        <div class="popup-title">${areaName}${pincodeStr}</div>
        <span class="popup-badge badge-ZERO">0</span>
      </div>
      <div class="popup-zero-status">
        <span style="color:#10b981; font-size:1.1rem;">🟢</span>
        <span style="color:#10b981; font-weight:600; font-size:0.88rem;">${zeroStatusText}</span>
      </div>
      <div class="popup-footer" style="margin-top:10px;">
        <a href="#/report" class="popup-check-link popup-report-link">${reportLinkText}</a>
      </div>
    </div>
  `;
}

// Global reference to bottom-left legend control
let legendControl = null;

/**
 * Render or update bilingual legend in bottom-left corner with config thresholds
 */
export function updateMapLegend(map, lang = getLanguage()) {
  if (!map || !window.L) return;

  if (legendControl) {
    map.removeControl(legendControl);
    legendControl = null;
  }

  legendControl = L.control({ position: "bottomleft" });
  legendControl.onAdd = function () {
    const div = L.DomUtil.create("div", "heatmap-legend");
    const isHi = lang === "hi";

    div.innerHTML = `
      <div class="legend-header">
        <span class="legend-title">${isHi ? "स्कैम गतिविधि स्तर" : "Scam Activity Level"}</span>
      </div>
      <div class="legend-items">
        <div class="legend-row">
          <span class="legend-dot" style="background:${SEV_COLORS.CRIT};"></span>
          <span class="legend-label"><strong>CRIT (10+)</strong>: ${isHi ? "अत्यधिक रिपोर्टें (10 या अधिक)" : "Very many (10 or more)"}</span>
        </div>
        <div class="legend-row">
          <span class="legend-dot" style="background:${SEV_COLORS.HIGH};"></span>
          <span class="legend-label"><strong>HIGH (5–9)</strong>: ${isHi ? "कई रिपोर्टें (5–9)" : "Many (5–9)"}</span>
        </div>
        <div class="legend-row">
          <span class="legend-dot" style="background:${SEV_COLORS.MED};"></span>
          <span class="legend-label"><strong>MED (&lt;5)</strong>: ${isHi ? "कुछ रिपोर्टें (5 से कम)" : "A few reports (below 5)"}</span>
        </div>
        <div class="legend-row">
          <span class="legend-dot legend-dot-green"></span>
          <span class="legend-label">${isHi ? "हरा: इस अवधि में कोई रिपोर्ट नहीं" : "Green: no reports in this period"}</span>
        </div>
      </div>
    `;
    return div;
  };

  legendControl.addTo(map);
}

// Keep track of active map layers to cleanly replace on each fetch
let activeHeatLayer = null;
let activeGlowLayer = null;
let activeMarkersLayer = null;
let activeDotsLayer = null;

/**
 * Main map renderer for Task F3
 * - Renders leaflet.heat heatLayer if plugin is available
 * - Otherwise falls back to 3 concentric circles (r, 0.6r, 0.3r) per cluster
 * - Renders faint green dots for areas with no reports
 * - Places numbered markers with popups on every cluster
 * - Renders sorted cluster list under the map by severity
 */
export function renderHeatmapView(map, clusters = [], allAreas = [], lang = getLanguage()) {
  const isHi = lang === "hi";

  // Always update the bottom-left legend
  if (map) {
    updateMapLegend(map, lang);
  }

  // Clear previous layers
  if (map) {
    if (activeHeatLayer) {
      map.removeLayer(activeHeatLayer);
      activeHeatLayer = null;
    }
    if (activeGlowLayer) {
      map.removeLayer(activeGlowLayer);
      activeGlowLayer = null;
    }
    if (activeMarkersLayer) {
      map.removeLayer(activeMarkersLayer);
      activeMarkersLayer = null;
    }
    if (activeDotsLayer) {
      map.removeLayer(activeDotsLayer);
      activeDotsLayer = null;
    }
  }

  const bounds = [];
  const reportedPincodes = new Set();

  // Valid clusters with coordinates
  const validClusters = clusters.filter(
    (c) => c.lat != null && c.lng != null && typeof c.lat === "number" && typeof c.lng === "number"
  );

  validClusters.forEach((c) => {
    if (c.pincode) reportedPincodes.add(c.pincode);
    bounds.push([c.lat, c.lng]);
  });

  // 1. Heatmap layer or fallback concentric circles
  if (map && validClusters.length > 0) {
    const maxCount = Math.max(...validClusters.map((c) => c.count), 1);
    const heatPoints = validClusters.map((c) => [c.lat, c.lng, c.count / maxCount]);

    let heatPluginLoaded = false;
    if (typeof L !== "undefined" && typeof L.heatLayer === "function") {
      try {
        activeHeatLayer = L.heatLayer(heatPoints, {
          radius: 38,
          blur: 24,
          maxZoom: 14,
          minOpacity: 0.35,
          gradient: {
            0.2: SEV_COLORS.MED,  // yellow / amber #F2B01E
            0.6: SEV_COLORS.HIGH, // orange #F57C00
            1.0: SEV_COLORS.CRIT, // red #D32F2F
          },
        }).addTo(map);
        heatPluginLoaded = true;
      } catch (err) {
        console.warn("Leaflet.heat render error; using concentric circle fallback:", err);
        heatPluginLoaded = false;
      }
    }

    // Fallback if plugin fails to load:
    // Draw 3 concentric translucent circles per cluster in the severity colour (radius r, 0.6r, 0.3r)
    if (!heatPluginLoaded) {
      activeGlowLayer = L.layerGroup().addTo(map);
      validClusters.forEach((c) => {
        const sevInfo = getSeverityInfo(c.count, c.severity, lang);
        const color = sevInfo.color;
        // Radius r proportional to count in meters
        const r = 600 + Math.min(c.count * 120, 1800);

        // 1. Outer circle (radius r)
        L.circle([c.lat, c.lng], {
          radius: r,
          fillColor: color,
          fillOpacity: 0.15,
          stroke: false,
          interactive: false,
        }).addTo(activeGlowLayer);

        // 2. Middle circle (radius 0.6r)
        L.circle([c.lat, c.lng], {
          radius: r * 0.6,
          fillColor: color,
          fillOpacity: 0.30,
          stroke: false,
          interactive: false,
        }).addTo(activeGlowLayer);

        // 3. Inner circle (radius 0.3r)
        L.circle([c.lat, c.lng], {
          radius: r * 0.3,
          fillColor: color,
          fillOpacity: 0.55,
          stroke: false,
          interactive: false,
        }).addTo(activeGlowLayer);
      });
    }

    // 2. Numbered marker on every cluster + Tap popup
    activeMarkersLayer = L.layerGroup().addTo(map);
    validClusters.forEach((c) => {
      const sevInfo = getSeverityInfo(c.count, c.severity, lang);
      const markerIcon = L.divIcon({
        className: "cluster-numbered-marker-wrapper",
        html: `
          <div class="cluster-num-marker marker-${sevInfo.severity}" 
               role="button"
               tabindex="0"
               aria-label="${c.locality || "Area"}: ${c.count} ${isHi ? "रिपोर्टें" : "reports"}, ${sevInfo.severity} (${sevInfo.badge})">
            <span class="marker-count">${c.count}</span>
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -18],
      });

      const marker = L.marker([c.lat, c.lng], { icon: markerIcon }).addTo(activeMarkersLayer);
      marker.bindPopup(buildClusterPopup(c, lang), { maxWidth: 320 });
    });
  }

  // 3. Faint green dots for areas with no reports in this window
  if (map && Array.isArray(allAreas)) {
    activeDotsLayer = L.layerGroup().addTo(map);
    allAreas.forEach((area) => {
      if (area.lat != null && area.lng != null && !reportedPincodes.has(area.pincode)) {
        bounds.push([area.lat, area.lng]);
        const dot = L.circleMarker([area.lat, area.lng], {
          radius: 5,
          color: SEV_COLORS.ZERO,
          fillColor: SEV_COLORS.ZERO,
          fillOpacity: 0.35,
          weight: 1.5,
        }).addTo(activeDotsLayer);

        dot.bindPopup(buildZeroClusterPopup(area, lang), { maxWidth: 280 });
      }
    });
  }

  // Fit bounds if any points present
  if (map && bounds.length > 0) {
    try {
      map.fitBounds(bounds, { padding: [35, 35], maxZoom: 13 });
    } catch (e) {
      // Map may not be in DOM yet
    }
  }

  // 4. Render the list under the map sorted by severity (CRIT -> HIGH -> MED)
  renderClustersList(clusters, lang, map);
}

/**
 * Render the list under the map sorted by severity (CRIT -> HIGH -> MED)
 */
export function renderClustersList(clusters = [], lang = getLanguage(), map = null) {
  const isHi = lang === "hi";
  const listContainer = document.getElementById("map-clusters-list");
  if (!listContainer) return;

  if (!clusters || clusters.length === 0) {
    listContainer.innerHTML = `
      <div class="clusters-empty-state">
        <p style="color: var(--text-muted); font-size: 0.9rem;">
          ${isHi ? "इस समय सीमा में कोई सक्रिय क्लस्टर नहीं मिला।" : "No active clusters found for this time window."}
        </p>
      </div>
    `;
    return;
  }

  // Sort clusters strictly by severity: CRIT (3) -> HIGH (2) -> MED (1), then count desc
  const sortedClusters = [...clusters].sort((a, b) => {
    const sevRank = { CRIT: 3, HIGH: 2, MED: 1 };
    const rA = sevRank[a.severity] || (a.count >= 10 ? 3 : a.count >= 5 ? 2 : 1);
    const rB = sevRank[b.severity] || (b.count >= 10 ? 3 : b.count >= 5 ? 2 : 1);
    if (rB !== rA) return rB - rA;
    return (b.count || 0) - (a.count || 0);
  });

  listContainer.innerHTML = sortedClusters
    .map((c, index) => {
      const sevInfo = getSeverityInfo(c.count, c.severity, lang);
      const scamInfo = getScamInfo(c.top_scam_type, lang);
      const reportsText = isHi ? "स्वतंत्र रिपोर्टें" : "independent reports";
      const topLabel = isHi ? "शीर्ष स्कैम" : "Top Sighting";

      return `
        <div class="cluster-item cluster-item-${sevInfo.severity}" 
             data-pincode="${escapeHtml(c.pincode)}" 
             data-lat="${c.lat != null ? c.lat : ""}" 
             data-lng="${c.lng != null ? c.lng : ""}"
             tabindex="0"
             role="button"
             aria-label="${escapeHtml(c.locality)}, ${escapeHtml(c.city)}: ${c.count} ${reportsText}, ${sevInfo.severity} (${sevInfo.badge})">
          <div class="cluster-info">
            <div class="cluster-name">
              <span class="cluster-order-num">#${index + 1}</span>
              ${escapeHtml(c.locality || "Area")}, ${escapeHtml(c.city || "")} 
              <span class="cluster-pincode">(${escapeHtml(c.pincode)})</span>
            </div>
            <div class="cluster-meta">
              <span>${topLabel}: <strong>${escapeHtml(scamInfo.name)}</strong></span>
              <span class="meta-separator">•</span>
              <span><strong>${c.count}</strong> ${reportsText}</span>
            </div>
          </div>
          <div class="cluster-badges-group">
            <span class="cluster-badge cluster-${sevInfo.severity}">${sevInfo.severity}</span>
            <span class="cluster-text-badge text-badge-${sevInfo.severity}">${sevInfo.badge}</span>
          </div>
        </div>
      `;
    })
    .join("");

  // Attach click listener to pan map & open popup when a cluster item is clicked
  if (map) {
    listContainer.querySelectorAll(".cluster-item").forEach((item) => {
      item.addEventListener("click", () => {
        const lat = parseFloat(item.getAttribute("data-lat"));
        const lng = parseFloat(item.getAttribute("data-lng"));
        if (!isNaN(lat) && !isNaN(lng)) {
          map.setView([lat, lng], 13);
          // Find matching marker or fire popup
          if (activeMarkersLayer) {
            activeMarkersLayer.eachLayer((marker) => {
              const pos = marker.getLatLng();
              if (Math.abs(pos.lat - lat) < 0.0001 && Math.abs(pos.lng - lng) < 0.0001) {
                marker.openPopup();
              }
            });
          }
        }
      });
    });
  }
}
