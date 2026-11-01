// web/timepicker.js – India Standard Time (IST) Timepicker & Date Selector for SatyaCheck
// Implements Task F4 per specs:
// - Default stays "Just now" (zero extra taps, reports take < 60s)
// - Collapsed "Change date and time" drawer
// - Date and time inputs in India time (Asia/Kolkata), max = now, min = 90 days ago
// - Quick chips: Just now, 1 hour ago, This morning, Last night, Yesterday, 2-3 days ago, Last week
// - Summary line in EN & HI: e.g. "Happened: Sun 1 Nov, 3:40 pm (India time)"
// - Outputs occurred_at and reported_at as ISO strings with +05:30
// - Future time validation: blocks submit with friendly bilingual error
// - Pure function exports: nowIst() and istIso(dateStr, timeStr)
// - Exposed to window for testing in browser console

import { t, getLanguage } from "./i18n.js";

/**
 * Return an ISO string with +05:30 timezone offset from dateStr (YYYY-MM-DD) and timeStr (HH:MM or HH:MM:SS)
 */
export function istIso(dateStr, timeStr) {
  if (!dateStr || !timeStr) return "";
  const d = dateStr.trim();
  const t = timeStr.trim();
  const timeWithSec = t.length === 5 ? `${t}:00` : t;
  return `${d}T${timeWithSec}+05:30`;
}

/**
 * Extract exact date and time parts in Asia/Kolkata timezone regardless of client's local system timezone
 */
export function getIstParts(d = new Date()) {
  const dtf = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Kolkata",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  const parts = Object.fromEntries(dtf.formatToParts(d).map((p) => [p.type, p.value]));
  return {
    year: parts.year,
    month: parts.month,
    day: parts.day,
    hour: parts.hour,
    minute: parts.minute,
    second: parts.second || "00",
    dateStr: `${parts.year}-${parts.month}-${parts.day}`,
    timeStr: `${parts.hour}:${parts.minute}`,
  };
}

/**
 * Return current IST time as a pure function.
 * Evaluates to string representation "YYYY-MM-DDTHH:MM:SS+05:30",
 * and also exposes .iso, .dateStr, .timeStr, and component properties.
 */
export function nowIst(d = new Date()) {
  const p = getIstParts(d);
  const iso = istIso(p.dateStr, `${p.hour}:${p.minute}:${p.second}`);
  const str = new String(iso);
  str.iso = iso;
  str.dateStr = p.dateStr;
  str.timeStr = p.timeStr;
  str.year = p.year;
  str.month = p.month;
  str.day = p.day;
  str.hour = p.hour;
  str.minute = p.minute;
  str.second = p.second;
  return str;
}

// Attach to window so developers/evaluators can test directly in browser console
if (typeof window !== "undefined") {
  window.nowIst = nowIst;
  window.istIso = istIso;
}

/**
 * Return min date allowed (90 days ago in IST)
 */
export function getMinDateIst(now = new Date()) {
  const d = new Date(now.getTime() - 90 * 86400000);
  return getIstParts(d).dateStr;
}

/**
 * Return max date allowed (today in IST)
 */
export function getMaxDateIst(now = new Date()) {
  return getIstParts(now).dateStr;
}

/**
 * Format summary line in EN or HI
 * e.g. "Happened: Sun, 1 Nov, 3:40 pm (India time)" or "घटना का समय: रवि, 1 नव, 3:40 pm (भारतीय समय)"
 */
export function formatSummary(dateStr, timeStr, lang = getLanguage()) {
  if (!dateStr || !timeStr) return "";
  const iso = istIso(dateStr, timeStr);
  const d = new Date(iso);
  const isHi = lang === "hi";

  const locale = isHi ? "hi-IN" : "en-IN";
  const dtf = new Intl.DateTimeFormat(locale, {
    timeZone: "Asia/Kolkata",
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });

  const formatted = dtf.format(d);
  if (isHi) {
    return `घटना का समय: ${formatted} (भारतीय समय)`;
  }
  return `Happened: ${formatted} (India time)`;
}

/**
 * Validate chosen date and time against future time and 90-day window
 */
export function validateChosenTime(dateStr, timeStr, lang = getLanguage()) {
  if (!dateStr || !timeStr) {
    return {
      valid: false,
      error: lang === "hi" ? "कृपया तारीख और समय चुनें।" : "Please select date and time.",
    };
  }

  const iso = istIso(dateStr, timeStr);
  const chosenTime = new Date(iso).getTime();
  const nowTime = Date.now();

  // Block future times (allow 60s clock skew)
  if (chosenTime > nowTime + 60000) {
    return {
      valid: false,
      error:
        lang === "hi"
          ? "घटना का समय भविष्य का नहीं हो सकता। कृपया बीता हुआ समय चुनें।"
          : "Event time cannot be in the future. Please select a past date and time.",
    };
  }

  // 90 days limit check
  const minTime = nowTime - 91 * 86400000;
  if (chosenTime < minTime) {
    return {
      valid: false,
      error:
        lang === "hi"
          ? "रिपोर्ट 90 दिन से अधिक पुरानी नहीं हो सकती।"
          : "Report cannot be older than 90 days.",
    };
  }

  return { valid: true, error: "" };
}

// Module State
let selectedChip = "now";
let isCustomExpanded = false;

/**
 * Compute plausible IST date & time for each quick chip
 */
export function getChipTimeValues(chipType, now = new Date()) {
  const pNow = getIstParts(now);
  const curHour = parseInt(pNow.hour, 10);

  switch (chipType) {
    case "now":
      return { dateStr: pNow.dateStr, timeStr: pNow.timeStr };

    case "1h": {
      const d = new Date(now.getTime() - 3600000);
      return getIstParts(d);
    }

    case "this_morning": {
      // If currently after 10 AM, use 09:30 AM today; if earlier in morning, use 2 hours ago or 06:00
      let tStr = "09:30";
      if (curHour < 10) {
        const morningHour = Math.max(0, curHour - 2);
        tStr = `${String(morningHour).padStart(2, "0")}:00`;
      }
      return { dateStr: pNow.dateStr, timeStr: tStr };
    }

    case "last_night": {
      // Yesterday at 21:30 (9:30 PM IST)
      const d = new Date(now.getTime() - 86400000);
      return { dateStr: getIstParts(d).dateStr, timeStr: "21:30" };
    }

    case "yesterday": {
      // Yesterday at 15:00 (3:00 PM IST)
      const d = new Date(now.getTime() - 86400000);
      return { dateStr: getIstParts(d).dateStr, timeStr: "15:00" };
    }

    case "2_3_days": {
      // 3 days ago at 14:00 (2:00 PM IST)
      const d = new Date(now.getTime() - 3 * 86400000);
      return { dateStr: getIstParts(d).dateStr, timeStr: "14:00" };
    }

    case "last_week": {
      // 7 days ago at 11:00 (11:00 AM IST)
      const d = new Date(now.getTime() - 7 * 86400000);
      return { dateStr: getIstParts(d).dateStr, timeStr: "11:00" };
    }

    default:
      return { dateStr: pNow.dateStr, timeStr: pNow.timeStr };
  }
}

/**
 * Initialize timepicker interactive controls in report form
 */
export function initTimepicker() {
  const dateInput = document.getElementById("timepicker-date");
  const timeInput = document.getElementById("timepicker-time");
  const toggleBtn = document.getElementById("timepicker-toggle-btn");
  const drawer = document.getElementById("timepicker-custom-drawer");
  const summaryEl = document.getElementById("timepicker-summary");
  const errorEl = document.getElementById("timepicker-error");
  const chipsContainer = document.getElementById("report-time-chips");

  if (!dateInput || !timeInput) return;

  // Set min & max dates in IST
  dateInput.max = getMaxDateIst();
  dateInput.min = getMinDateIst();

  // Initialize with current time IST
  const current = nowIst();
  dateInput.value = current.dateStr;
  timeInput.value = current.timeStr;
  selectedChip = "now";
  isCustomExpanded = false;

  updateSummaryLine();

  // Quick Chips Click Listener
  if (chipsContainer) {
    chipsContainer.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (!chip) return;
      const type = chip.getAttribute("data-time") || "now";

      chipsContainer.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      selectedChip = type;

      const vals = getChipTimeValues(type);
      dateInput.value = vals.dateStr;
      timeInput.value = vals.timeStr;

      // Clear any previous error
      if (errorEl) {
        errorEl.textContent = "";
        errorEl.style.display = "none";
      }

      updateSummaryLine();
    });
  }

  // Collapsible toggle button
  if (toggleBtn && drawer) {
    toggleBtn.addEventListener("click", () => {
      isCustomExpanded = !isCustomExpanded;
      drawer.style.display = isCustomExpanded ? "block" : "none";
      toggleBtn.classList.toggle("expanded", isCustomExpanded);
      toggleBtn.setAttribute("aria-expanded", String(isCustomExpanded));
    });
  }

  // Inputs change listener
  const handleInputChange = () => {
    // When inputs are manually tweaked, check if they match any chip; if not, deselect chips
    const curVal = `${dateInput.value} ${timeInput.value}`;
    let matched = false;
    if (chipsContainer) {
      chipsContainer.querySelectorAll(".chip").forEach((chip) => {
        const type = chip.getAttribute("data-time");
        const chipVals = getChipTimeValues(type);
        if (`${chipVals.dateStr} ${chipVals.timeStr}` === curVal) {
          chip.classList.add("active");
          selectedChip = type;
          matched = true;
        } else {
          chip.classList.remove("active");
        }
      });
      if (!matched) {
        selectedChip = "custom";
      }
    }

    // Validate
    const validation = validateChosenTime(dateInput.value, timeInput.value, getLanguage());
    if (errorEl) {
      if (!validation.valid) {
        errorEl.textContent = validation.error;
        errorEl.style.display = "block";
      } else {
        errorEl.textContent = "";
        errorEl.style.display = "none";
      }
    }

    updateSummaryLine();
  };

  dateInput.addEventListener("change", handleInputChange);
  timeInput.addEventListener("change", handleInputChange);
  dateInput.addEventListener("input", handleInputChange);
  timeInput.addEventListener("input", handleInputChange);
}

/**
 * Update summary line text
 */
export function updateSummaryLine() {
  const summaryEl = document.getElementById("timepicker-summary");
  const dateInput = document.getElementById("timepicker-date");
  const timeInput = document.getElementById("timepicker-time");
  if (!summaryEl || !dateInput || !timeInput) return;

  if (!dateInput.value || !timeInput.value) {
    summaryEl.textContent = "";
    return;
  }

  summaryEl.textContent = formatSummary(dateInput.value, timeInput.value, getLanguage());
}

/**
 * Get current timepicker value for payload submission
 */
export function getTimepickerValue() {
  const dateInput = document.getElementById("timepicker-date");
  const timeInput = document.getElementById("timepicker-time");
  const lang = getLanguage();

  const reportedAtIso = nowIst().iso;

  // Default path: "Just now" without manual customization
  if (selectedChip === "now" && !isCustomExpanded) {
    const curIst = nowIst();
    return {
      occurredAtIso: curIst.iso,
      reportedAtIso: reportedAtIso,
      isValid: true,
      error: "",
    };
  }

  const dVal = dateInput ? dateInput.value : "";
  const tVal = timeInput ? timeInput.value : "";
  const validation = validateChosenTime(dVal, tVal, lang);

  if (!validation.valid) {
    return {
      occurredAtIso: null,
      reportedAtIso: reportedAtIso,
      isValid: false,
      error: validation.error,
    };
  }

  const occurredAtIso = istIso(dVal, tVal);
  return {
    occurredAtIso: occurredAtIso,
    reportedAtIso: reportedAtIso,
    isValid: true,
    error: "",
  };
}

/**
 * Reset timepicker back to default "Just now" collapsed state
 */
export function resetTimepicker() {
  const dateInput = document.getElementById("timepicker-date");
  const timeInput = document.getElementById("timepicker-time");
  const drawer = document.getElementById("timepicker-custom-drawer");
  const toggleBtn = document.getElementById("timepicker-toggle-btn");
  const errorEl = document.getElementById("timepicker-error");
  const chipsContainer = document.getElementById("report-time-chips");

  selectedChip = "now";
  isCustomExpanded = false;

  if (drawer) drawer.style.display = "none";
  if (toggleBtn) {
    toggleBtn.classList.remove("expanded");
    toggleBtn.setAttribute("aria-expanded", "false");
  }
  if (errorEl) {
    errorEl.textContent = "";
    errorEl.style.display = "none";
  }

  const current = nowIst();
  if (dateInput) dateInput.value = current.dateStr;
  if (timeInput) timeInput.value = current.timeStr;

  if (chipsContainer) {
    chipsContainer.querySelectorAll(".chip").forEach((c, idx) => {
      c.classList.toggle("active", idx === 0);
    });
  }

  updateSummaryLine();
}
