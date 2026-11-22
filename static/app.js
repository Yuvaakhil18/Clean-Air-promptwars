"use strict";

// Unique tile ID counter to avoid duplicate IDs if titles ever collide.
let _tileCounter = 0;

(() => {
  const form = document.getElementById("advice-form");
  const submitButton = document.getElementById("submit-button");
  const statusEl = document.getElementById("status");
  const resultsEl = document.getElementById("results");

  // All server data is inserted with textContent, never innerHTML, to prevent XSS.
  function el(tag, text, attrs = {}) {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    return node;
  }

  function tile(variant, title, body) {
    const id = `tile-${++_tileCounter}`;
    const wrapper = el("section", undefined, { class: `tile ${variant}`, "aria-labelledby": id });
    wrapper.append(el("h3", title, { id }), body);
    return wrapper;
  }

  function levelMeter(level) {
    // Visual meter is hidden from AT; accessible text is provided separately.
    const meter = el("div", undefined, { class: "meter", "aria-hidden": "true" });
    for (let i = 0; i <= 5; i += 1) {
      meter.append(el("span", undefined, { class: i <= level ? "on" : "" }));
    }
    return meter;
  }

  function overviewBody(plan) {
    const wrap = el("div");
    wrap.append(
      el("p", `${plan.risk_label}`, { class: "risk-label" }),
      // Screen-reader-visible risk level text (the visual meter is aria-hidden).
      el("p", `Risk level ${plan.risk_level} out of 5`, { class: "sr-only" }),
      el("p", plan.measured ? `Reading: ${plan.pm25} µg/m³ PM2.5` : "No reading entered: general estimate", { class: "summary-meta" }),
      levelMeter(plan.risk_level),
      el("p", plan.summary, { class: "summary-text" }),
      el(
        "p",
        plan.summary_source === "ai" ? "Written for your household by AI." : "Built from standard guidance.",
        { class: "summary-meta" },
      ),
    );
    return wrap;
  }

  function warningsBody(warnings) {
    if (!warnings.length) return el("p", "Nothing needs urgent attention.");
    const ul = el("ul", undefined, { class: "warning-list" });
    for (const warning of warnings) ul.append(el("li", warning));
    return ul;
  }

  function impactsBody(impacts) {
    const grid = el("div", undefined, { class: "impact-grid" });
    for (const impact of impacts) {
      const headingId = `impact-title-${++_tileCounter}`;
      const card = el("article", undefined, {
        class: "impact-card",
        "aria-labelledby": headingId,
      });
      card.append(
        el("h4", impact.title, { id: headingId }),
        el("p", impact.estimate, { class: "impact-estimate" }),
        el("p", impact.explanation),
        el("p", `Assumptions: ${impact.assumptions}`, { class: "impact-assumptions" }),
      );
      grid.append(card);
    }
    return grid;
  }

  function tipList(tips) {
    const ol = el("ol", undefined, { class: "tips" });
    for (const tip of tips) {
      const li = el("li");
      li.append(el("strong", tip.title), el("span", tip.detail));
      ol.append(li);
    }
    return ol;
  }

  function routinesBody(plan) {
    const wrap = el("div");
    wrap.append(tipList(plan.routines));
    if (plan.personal_tips.length) {
      wrap.append(el("h4", "Tailored for your household"));
      const ul = el("ul", undefined, { class: "warning-list" });
      for (const tip of plan.personal_tips) ul.append(el("li", tip));
      wrap.append(ul);
    }
    return wrap;
  }

  function alternativesBody(tips) {
    const grid = el("div", undefined, { class: "alt-grid" });
    for (const tip of tips) {
      const headingId = `alt-title-${++_tileCounter}`;
      const card = el("article", undefined, {
        class: "alt-card",
        "aria-labelledby": headingId,
      });
      card.append(el("h4", tip.title, { id: headingId }), el("p", tip.detail));
      grid.append(card);
    }
    return grid;
  }

  function render(plan) {
    _tileCounter = 0;
    const grid = el("div", undefined, { class: "bento" });
    // h2 anchors the heading hierarchy; tiles inside use h3
    grid.append(
      el("h2", "Your plan", { class: "sr-only" }),
      tile("tile-overview", "Your air today", overviewBody(plan)),
      tile("tile-warnings", "Things to check", warningsBody(plan.warnings)),
      tile("tile-impact", "What your choices change", impactsBody(plan.impacts)),
      tile("tile-routines", "Daily routine", routinesBody(plan)),
      tile("tile-indoor", "Indoor air hacks", tipList(plan.indoor_hacks)),
      tile("tile-alternatives", "Lower-emission alternatives", alternativesBody(plan.alternatives)),
      el("p", plan.disclaimer, { class: "disclaimer" }),
    );
    resultsEl.replaceChildren(grid);
    resultsEl.focus();
  }

  const optionalNumber = (value) => (value === "" || value === null ? null : Number(value));

  function readForm() {
    const data = new FormData(form);
    return {
      location: data.get("location"),
      pm25: optionalNumber(data.get("pm25")),
      aqi_scale: data.get("aqi_scale"),
      adults: Number(data.get("adults")),
      children: Number(data.get("children")),
      older_adults: Number(data.get("older_adults")),
      pregnant: form.elements.pregnant.checked,
      respiratory_condition: form.elements.respiratory_condition.checked,
      home: data.get("home"),
      cooking_fuel: data.get("cooking_fuel"),
      room_area_m2: Number(data.get("room_area_m2")),
      ceiling_height_m: Number(data.get("ceiling_height_m")),
      has_purifier: form.elements.has_purifier.checked,
      purifier_cadr_m3h: optionalNumber(data.get("purifier_cadr_m3h")),
      commute_mode: data.get("commute_mode"),
      commute_km: Number(data.get("commute_km")),
      commute_days_per_week: Number(data.get("commute_days_per_week")),
      outdoor_work: form.elements.outdoor_work.checked,
      notes: data.get("notes") || "",
    };
  }

  function errorMessage(status, data) {
    if (status === 422 && typeof data.detail === "string") return data.detail;
    if (status === 422) return "Please check the highlighted fields and try again.";
    if (status === 429) return "Too many requests. Please wait a moment and try again.";
    return "We could not build your plan right now. Please try again shortly.";
  }

  function setBusy(busy) {
    submitButton.disabled = busy;
    submitButton.textContent = busy ? "Preparing your plan…" : "Show my plan";
    submitButton.setAttribute("aria-label", busy ? "Preparing your plan, please wait" : "Show my plan");
    form.setAttribute("aria-busy", String(busy));
  }

  /** Mark fields as valid or invalid for screen readers. */
  function clearValidationState() {
    for (const el of form.querySelectorAll("[aria-invalid]")) {
      el.removeAttribute("aria-invalid");
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearValidationState();

    if (!form.reportValidity()) {
      // Mark each invalid field for screen readers.
      for (const field of form.elements) {
        if (!field.validity.valid) {
          field.setAttribute("aria-invalid", "true");
        }
      }
      return;
    }

    setBusy(true);
    statusEl.textContent = "Preparing your plan…";
    try {
      const response = await fetch("/api/advice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(readForm()),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(errorMessage(response.status, data));
      render(data);
      statusEl.textContent = "Your plan is ready.";
    } catch (error) {
      statusEl.textContent = error.message;
    } finally {
      setBusy(false);
    }
  });
})();
