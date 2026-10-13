"use strict";
// Public educational demo: no network requests, patient inputs, signatures, or data persistence.
const EXAMPLES = {
  "KRAS G12C": {sites:["lung","colorectal"],descriptions:{lung:"Sotorasib / adagrasib — example agents; line of therapy and current labels require review.",colorectal:"KRAS G12C-directed combinations are context-dependent; confirm regimen and labeling."}},
  "EGFR L858R": {sites:["lung"],descriptions:{lung:"Osimertinib — example agent; confirm histology, staging, co-alterations, and current indication."}},
  "BRAF V600E": {sites:["colorectal","melanoma"],descriptions:{colorectal:"Encorafenib plus cetuximab — colorectal example; requires current clinical review.",melanoma:"BRAF/MEK combinations are melanoma examples; current labels require review."}},
  "PIK3CA H1047R": {sites:["breast"],descriptions:{breast:"Pathway-targeted options depend on receptor status and prior therapy; not determined here."}}
};

function evaluateMtb(site, variant) {
  const record = EXAMPLES[variant];
  if (!record || !record.sites.includes(site)) {
    return {status:"No context-matched example",details:"An unlisted or tumor-mismatched alteration cannot be assigned an evidence tier or treatment by this demonstration."};
  }
  return {status:"Illustrative association found",details:record.descriptions[site]};
}

function evaluateQc(primary, secondary, descriptor, critical) {
  if (!Number.isFinite(primary) || !Number.isFinite(secondary)) {
    throw new Error("Both measurements must be finite numbers.");
  }
  const alerts = [];
  if (primary > 25) alerts.push("Primary metric exceeds the demonstration threshold (25).");
  if (critical || secondary > 12) alerts.push("Safety flag or secondary demonstration threshold (>12) triggered.");
  if (["DISCORDANT","ANOMALY","MUTANT","VIOLATION","FAIL","REJECT"].some(word=>String(descriptor).toUpperCase().includes(word))) {
    alerts.push("Descriptor contains a demonstration conformance-warning term.");
  }
  return {
    urgency: critical ? "CRITICAL_STAT_PANIC" : alerts.length ? "ELEVATED_RISK" : "ROUTINE",
    integrity: critical ? "RECALIBRATION_REQUIRED" : alerts.length ? "DISCORDANT_ANOMALY" : "VALIDATED_OPTIMAL",
    alerts
  };
}

function putResult(root, heading, lines) {
  root.replaceChildren();
  const title = document.createElement("h4");
  title.textContent = "Local demonstration output";
  const status = document.createElement("p");
  status.className = "status";
  status.textContent = heading;
  const list = document.createElement("ul");
  lines.forEach(line => {
    const item = document.createElement("li");
    item.textContent = line;
    list.appendChild(item);
  });
  root.append(title,status,list);
}

function initPage() {
  const mtbForm = document.getElementById("mtb-form");
  const qcForm = document.getElementById("qc-form");
  if (!mtbForm || !qcForm) return;
  mtbForm.addEventListener("submit", event => {
    event.preventDefault();
    const result = evaluateMtb(document.getElementById("tumor").value, document.getElementById("variant").value);
    putResult(document.getElementById("mtb-result"), result.status, [
      result.details,
      "No actual clinical trial search, guideline verification, or treatment recommendation was performed."
    ]);
  });
  qcForm.addEventListener("submit", event => {
    event.preventDefault();
    const primary = Number(document.getElementById("primary").value);
    const secondary = Number(document.getElementById("secondary").value);
    try {
      if (document.getElementById("primary").value.trim() === "" || document.getElementById("secondary").value.trim() === "") throw new Error("Both measurements are required.");
      const result = evaluateQc(primary,secondary,document.getElementById("descriptor").value,document.getElementById("critical").checked);
      putResult(document.getElementById("qc-result"),result.urgency,[result.integrity].concat(result.alerts.length ? result.alerts : ["No demonstration rules triggered."]).concat(["No HMAC audit signature is generated in this browser."]));
    } catch (error) {
      putResult(document.getElementById("qc-result"),"Input error",[error.message]);
    }
  });
}
if (typeof document !== "undefined") document.addEventListener("DOMContentLoaded", initPage);
if (typeof module !== "undefined" && module.exports) module.exports = {evaluateMtb,evaluateQc};
