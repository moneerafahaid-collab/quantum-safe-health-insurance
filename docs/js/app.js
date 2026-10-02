const STORAGE_KEY = "qshi-committee-store";

const decisionLabels = {
  APPROVED: "مقبولة",
  APPROVED_VITAL_POINTS: "مقبولة — عملية حيوية بالنقاط",
  REJECTED_DUPLICATE: "مرفوضة — تكرار",
  REJECTED_NOT_ENTITLED: "مرفوضة — بلا أحقية",
  HOSPITAL_FRAUD: "تلاعب مستشفى — طوارئ",
  MANUAL_REVIEW: "مراجعة يدوية",
};

const scenarioLabels = {
  duplicate: "تكرار تبرير الأشعة",
  unique: "تحليل مخبري جديد",
  review: "تشابه جزئي للرنين",
  er_vital: "طوارئ: إنعاش بالنقاط",
  er_fraud: "طوارئ: تلاعب بلا أحقية",
  er_unentitled: "طوارئ: رنين غير مستحق",
};

const PROCEDURE_CATALOG = {
  "ER-CPR-01": { name: "إنعاش قلبي رئوي", category: "vital", points: 40, tiers: ["BASIC", "ESSENTIAL", "PREMIUM"] },
  "ER-INTUBATION-01": { name: "تنبيب رغامي", category: "vital", points: 50, tiers: ["BASIC", "ESSENTIAL", "PREMIUM"] },
  "ER-DEFIB-01": { name: "صدمات كهربائية", category: "vital", points: 45, tiers: ["BASIC", "ESSENTIAL", "PREMIUM"] },
  "ER-HEMORRHAGE-01": { name: "سيطرة على نزيف حيوي", category: "vital", points: 35, tiers: ["BASIC", "ESSENTIAL", "PREMIUM"] },
  "ER-THROMBOLYSIS-01": { name: "مذيب جلطة", category: "vital", points: 55, tiers: ["BASIC", "ESSENTIAL", "PREMIUM"] },
  "ER-STABILIZE-01": { name: "تثبيت أولي في الطوارئ", category: "er_covered", points: 10, tiers: ["BASIC", "ESSENTIAL", "PREMIUM"] },
  "ER-ECG-01": { name: "تخطيط قلب طوارئ", category: "er_covered", points: 10, tiers: ["BASIC", "ESSENTIAL", "PREMIUM"] },
  "LAB-CBC-01": { name: "تحليل دم كامل", category: "er_covered", points: 8, tiers: ["BASIC", "ESSENTIAL", "PREMIUM"] },
  "CT-TRAUMA-01": { name: "أشعة مقطعية للحوادث", category: "er_covered", points: 30, tiers: ["BASIC", "ESSENTIAL", "PREMIUM"] },
  "CT-CHEST-02": { name: "أشعة مقطعية للصدر", category: "er_covered", points: 25, tiers: ["ESSENTIAL", "PREMIUM"] },
  "MRI-LUMBAR-01": { name: "رنين أسفل الظهر", category: "elective", points: 70, tiers: ["PREMIUM"] },
  "SURGERY-KNEE-ELECTIVE-01": { name: "عملية ركبة اختيارية", category: "elective", points: 80, tiers: ["PREMIUM"] },
  "PRIVATE-SUITE-01": { name: "جناح خاص", category: "luxury", points: 0, tiers: ["PREMIUM"] },
  "COSMETIC-FILLER-01": { name: "إجراء تجميلي", category: "luxury", points: 0, tiers: [] },
  "DENTAL-WHITENING-01": { name: "تبييض أسنان", category: "luxury", points: 0, tiers: [] },
};

const HISTORY_JUSTIFICATION =
  "المريض يعاني من ألام حادة في الظهر وتم إعطاء علاج مسكن ولم يتحسن ويرغب في عمل أشعة";

const payloads = {
  duplicate: {
    transaction_id: "NPHIES-TXN-2026-08923",
    patient: { id: "PAT-8812", national_id: "1098765432" },
    claim: {
      claim_id: "CLM-2099",
      procedure_code: "MRI-LUMBAR-01",
      doctor_id: "DOC-404",
      department: "OUTPATIENT",
      hospital_id: "",
      triage_points: 0,
      policy_tier: "BASIC",
      requested_items: [],
      justification: HISTORY_JUSTIFICATION,
    },
  },
  unique: {
    transaction_id: "NPHIES-TXN-2026-09001",
    patient: { id: "PAT-8812", national_id: "1098765432" },
    claim: {
      claim_id: "CLM-3100",
      procedure_code: "LAB-CBC-01",
      doctor_id: "DOC-12",
      department: "OUTPATIENT",
      hospital_id: "",
      triage_points: 0,
      policy_tier: "BASIC",
      requested_items: [],
      justification: "تحليل دم روتيني لمتابعة فقر الدم بعد بدء الحديد الفموي لمدة ثمانية أسابيع.",
    },
  },
  review: {
    transaction_id: "NPHIES-TXN-2026-09077",
    patient: { id: "PAT-8812", national_id: "1098765432" },
    claim: {
      claim_id: "CLM-3188",
      procedure_code: "MRI-LUMBAR-01",
      doctor_id: "DOC-77",
      department: "OUTPATIENT",
      hospital_id: "",
      triage_points: 0,
      policy_tier: "BASIC",
      requested_items: [],
      justification: "المريض يعاني من آلام في الظهر بعد علاج مسكن ويحتاج إعادة تقييم بالأشعة.",
    },
  },
  er_vital: {
    transaction_id: "NPHIES-TXN-2026-ER-1001",
    patient: { id: "PAT-8812", national_id: "1098765432" },
    claim: {
      claim_id: "CLM-ER-4401",
      procedure_code: "ER-CPR-01",
      doctor_id: "DOC-ER-7",
      department: "ER",
      hospital_id: "HOSP-HAIL-01",
      triage_points: 82,
      policy_tier: "BASIC",
      requested_items: [],
      justification: "توقف قلب في قسم الطوارئ واستدعي الإنعاش فوراً.",
    },
  },
  er_fraud: {
    transaction_id: "NPHIES-TXN-2026-ER-2088",
    patient: { id: "PAT-8812", national_id: "1098765432" },
    claim: {
      claim_id: "CLM-ER-4499",
      procedure_code: "ER-STABILIZE-01",
      doctor_id: "DOC-ER-19",
      department: "ER",
      hospital_id: "HOSP-HAIL-01",
      triage_points: 18,
      policy_tier: "BASIC",
      requested_items: ["MRI-LUMBAR-01", "PRIVATE-SUITE-01", "COSMETIC-FILLER-01"],
      justification: "مراجع طوارئ بشكوى خفيفة وتم طلب رنين وجناح خاص وتجميل دون أحقية.",
    },
  },
  er_unentitled: {
    transaction_id: "NPHIES-TXN-2026-ER-3012",
    patient: { id: "PAT-8812", national_id: "1098765432" },
    claim: {
      claim_id: "CLM-ER-4510",
      procedure_code: "MRI-LUMBAR-01",
      doctor_id: "DOC-ER-19",
      department: "ER",
      hospital_id: "HOSP-HAIL-01",
      triage_points: 22,
      policy_tier: "BASIC",
      requested_items: [],
      justification: "طلب رنين أسفل الظهر من الطوارئ دون أن يكون مشمولاً في الوثيقة.",
    },
  },
};

const $ = (id) => document.getElementById(id);

function toast(message) {
  const node = $("toast");
  node.hidden = false;
  node.textContent = message;
  setTimeout(() => {
    node.hidden = true;
  }, 2600);
}

function badge(decision) {
  return `<span class="badge ${decision}">${decisionLabels[decision] || decision}</span>`;
}

function shortHash(value) {
  return value ? `${value.slice(0, 10)}…${value.slice(-6)}` : "—";
}

async function sha256(text) {
  const data = new TextEncoder().encode(text);
  const buf = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function tokenize(text) {
  return new Set((text || "").toLowerCase().split(/\s+/).filter(Boolean));
}

function jaccard(a, b) {
  const left = tokenize(a);
  const right = tokenize(b);
  const union = new Set([...left, ...right]);
  if (!union.size) return 0;
  let inter = 0;
  left.forEach((token) => {
    if (right.has(token)) inter += 1;
  });
  return inter / union.size;
}

function seedStore() {
  const now = new Date().toISOString();
  return {
    claims: [
      {
        claim_id: "CLM-1001",
        transaction_id: "NPHIES-TXN-2025-SEED",
        patient_id: "PAT-8812",
        national_id: "1098765432",
        procedure_code: "MRI-LUMBAR-01",
        doctor_id: "DOC-99",
        department: "OUTPATIENT",
        justification: HISTORY_JUSTIFICATION,
        decision: "APPROVED",
        execution_time_ms: 12,
        created_at: now,
      },
    ],
    audit: [
      {
        event_type: "SEED",
        detail: { claim_id: "CLM-1001", decision: "APPROVED" },
        created_at: now,
      },
    ],
  };
}

function loadStore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return seedStore();
    const parsed = JSON.parse(raw);
    if (!parsed.claims || !parsed.audit) return seedStore();
    return parsed;
  } catch {
    return seedStore();
  }
}

function saveStore(store) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

function statsFrom(store) {
  return {
    total_claims: store.claims.length,
    approved: store.claims.filter((item) => String(item.decision).startsWith("APPROVED")).length,
    hospital_fraud: store.claims.filter((item) => item.decision === "HOSPITAL_FRAUD").length,
    rejected: store.claims.filter((item) => String(item.decision).startsWith("REJECTED") || item.decision === "HOSPITAL_FRAUD").length,
  };
}

function inspectProcedure(code, policyTier, triagePoints) {
  const rule = PROCEDURE_CATALOG[code];
  if (!rule) {
    return {
      procedure_code: code,
      name: code,
      category: "elective",
      entitled: false,
      reason: "إجراء غير مدرج في أحقية الطوارئ لهذه الوثيقة.",
    };
  }

  if (rule.category === "vital") {
    const entitled = triagePoints >= rule.points;
    return {
      procedure_code: code,
      name: rule.name,
      category: "vital",
      entitled,
      reason: entitled
        ? `عملية حيوية: النقاط ${triagePoints} تحقق الحد ${rule.points}.`
        : `عملية حيوية تحتاج ${rule.points} نقطة، والمتوفر ${triagePoints}.`,
    };
  }

  const entitled = rule.tiers.includes(policyTier);
  let reason = "إجراء غير مستحق على هذه الوثيقة من قسم الطوارئ.";
  if (entitled) reason = "مشمول في أحقية وثيقة المريض لقسم الطوارئ.";
  else if (rule.category === "luxury") reason = "طلب ترفيهي/غير طبي لا أحقية للمريض به في الطوارئ.";
  return { procedure_code: code, name: rule.name, category: rule.category, entitled, reason };
}

function evaluateEntitlement(claim) {
  if ((claim.department || "OUTPATIENT").toUpperCase() !== "ER") {
    return { applies: false, status: null, findings: [], fraud: 0 };
  }

  const codes = [claim.procedure_code, ...(claim.requested_items || [])].filter(Boolean);
  const seen = new Set();
  const findings = [];
  let fraud = 0;
  let vitalOk = false;
  let notEntitled = 0;
  let luxuryCount = 0;

  for (const code of codes) {
    if (seen.has(code)) continue;
    seen.add(code);
    const finding = inspectProcedure(code, claim.policy_tier, Number(claim.triage_points || 0));
    findings.push(finding);
    if (finding.category === "vital" && finding.entitled) vitalOk = true;
    if ((finding.category === "elective" || finding.category === "luxury") && !finding.entitled) {
      notEntitled += 1;
      fraud += finding.category === "luxury" ? 40 : 25;
      if (finding.category === "luxury") luxuryCount += 1;
    } else if (finding.category === "er_covered" && !finding.entitled) {
      notEntitled += 1;
      fraud += 20;
    }
  }

  if (Number(claim.triage_points || 0) < 25 && Math.max(0, seen.size - 1) >= 2) {
    fraud += 20;
  }

  let status = "APPROVED";
  if (fraud >= 50 || luxuryCount > 0) status = "HOSPITAL_FRAUD";
  else if (notEntitled > 0) status = "REJECTED_NOT_ENTITLED";
  else if (vitalOk && findings.every((item) => item.category === "vital" || item.entitled)) status = "APPROVED_VITAL_POINTS";
  else if (findings.some((item) => item.category === "vital" && !item.entitled)) status = "MANUAL_REVIEW";

  return { applies: true, status, findings, fraud: Math.min(fraud, 100) };
}

async function decide(payload, store) {
  const started = performance.now();
  const claim = payload.claim;
  const patientHash = await sha256(`${payload.patient.id}|${payload.patient.national_id}|qshi-salt`);
  const history = store.claims.filter(
    (item) => item.patient_id === payload.patient.id && item.national_id === payload.patient.national_id
  );

  let best = 0;
  const warnings = [];
  for (const past of history) {
    const score = Number(jaccard(claim.justification, past.justification).toFixed(2));
    if (score > best) best = score;
    if (score >= 0.6) {
      warnings.push({
        past_claim_id: past.claim_id,
        doctor_id: past.doctor_id,
        similarity_score: score,
      });
    }
  }

  const entitlement = evaluateEntitlement(claim);
  let qgnn = "APPROVED";
  if (best >= 0.85) qgnn = "REJECTED_DUPLICATE";
  else if (best >= 0.6) qgnn = "MANUAL_REVIEW";

  let decision = qgnn;
  if (entitlement.applies && (entitlement.status === "HOSPITAL_FRAUD" || entitlement.status === "REJECTED_NOT_ENTITLED")) {
    decision = entitlement.status;
  } else if (entitlement.applies && entitlement.status === "APPROVED_VITAL_POINTS") {
    decision = "APPROVED_VITAL_POINTS";
  } else if (entitlement.applies && entitlement.status === "MANUAL_REVIEW" && qgnn !== "REJECTED_DUPLICATE") {
    decision = "MANUAL_REVIEW";
  }

  const createdAt = new Date().toISOString();
  const record = {
    claim_id: claim.claim_id,
    transaction_id: payload.transaction_id,
    patient_id: payload.patient.id,
    national_id: payload.patient.national_id,
    anonymized_patient_hash: patientHash,
    procedure_code: claim.procedure_code,
    doctor_id: claim.doctor_id,
    department: claim.department || "OUTPATIENT",
    justification: claim.justification,
    decision,
    execution_time_ms: Math.max(8, Math.round(performance.now() - started)),
    created_at: createdAt,
    metrics: {
      consistency_score: Number((1 - best).toFixed(2)),
      similarity_score: best,
      triage_points: Number(claim.triage_points || 0),
      fraud_score: entitlement.fraud,
    },
    entitlement_findings: entitlement.findings,
    warnings,
  };

  store.claims.unshift(record);
  store.audit.unshift({
    event_type: "CLAIM_DECIDED",
    detail: { claim_id: record.claim_id, decision },
    created_at: createdAt,
  });
  saveStore(store);
  return record;
}

function fillForm(payload) {
  const form = $("claim-form");
  form.transaction_id.value = payload.transaction_id;
  form.claim_id.value = payload.claim.claim_id;
  form.patient_id.value = payload.patient.id;
  form.national_id.value = payload.patient.national_id;
  form.procedure_code.value = payload.claim.procedure_code;
  form.doctor_id.value = payload.claim.doctor_id;
  form.department.value = payload.claim.department || "OUTPATIENT";
  form.hospital_id.value = payload.claim.hospital_id || "";
  form.triage_points.value = payload.claim.triage_points ?? 0;
  form.policy_tier.value = payload.claim.policy_tier || "BASIC";
  form.requested_items.value = (payload.claim.requested_items || []).join(", ");
  form.justification.value = payload.claim.justification;
}

function renderKpis(stats) {
  const cards = [
    ["إجمالي المطالبات", stats.total_claims],
    ["مقبولة", stats.approved],
    ["تلاعب مستشفى", stats.hospital_fraud],
    ["مرفوضة", stats.rejected],
  ];
  $("kpis").innerHTML = cards
    .map(([label, value]) => `<article class="kpi"><span>${label}</span><b>${value}</b></article>`)
    .join("");
}

function renderRecent(items) {
  $("recent-claims").innerHTML =
    items
      .slice(0, 8)
      .map(
        (item) => `
      <tr>
        <td>${item.claim_id}</td>
        <td>${item.procedure_code}</td>
        <td>${badge(item.decision)}</td>
        <td>${item.department || "—"}</td>
        <td>${item.execution_time_ms}ms</td>
      </tr>`
      )
      .join("") || `<tr><td colspan="5">لا توجد مطالبات بعد.</td></tr>`;
}

function renderAudit(items) {
  $("audit-feed").innerHTML =
    items
      .slice(0, 8)
      .map(
        (item) => `
      <li>
        <strong>${item.event_type}</strong>
        <div>${item.detail.decision || item.detail.claim_id || "حدث نظام"}</div>
        <time>${item.created_at}</time>
      </li>`
      )
      .join("") || "<li>لا يوجد تدقيق بعد.</li>";
}

function renderLedger(items) {
  $("ledger-body").innerHTML =
    items
      .map(
        (item) => `
      <tr>
        <td>${item.created_at.replace("T", " ").slice(0, 19)}</td>
        <td>${item.transaction_id}</td>
        <td>${item.claim_id}</td>
        <td>${item.doctor_id}</td>
        <td>${item.procedure_code}</td>
        <td>${badge(item.decision)}</td>
        <td>${item.justification}</td>
      </tr>`
      )
      .join("") || `<tr><td colspan="7">السجل فارغ.</td></tr>`;
}

function renderResult(record) {
  $("result-empty").classList.add("hidden");
  $("result-body").classList.remove("hidden");
  $("result-decision").textContent = decisionLabels[record.decision] || record.decision;
  $("result-decision").className = record.decision;
  $("m-consistency").textContent = record.metrics.consistency_score;
  $("m-similarity").textContent = record.metrics.similarity_score;
  $("m-points").textContent = record.metrics.triage_points ?? 0;
  $("m-fraud").textContent = record.metrics.fraud_score ?? 0;
  $("result-hash").textContent = shortHash(record.anonymized_patient_hash);
  const findings = record.entitlement_findings || [];
  $("result-entitlement").innerHTML = findings.length
    ? findings
        .map(
          (item) =>
            `<li>${item.entitled ? "مستحق" : "غير مستحق"} — ${item.name} (${item.procedure_code}): ${item.reason}</li>`
        )
        .join("")
    : "<li>لا ينطبق رصد أحقية الطوارئ على هذه المطالبة.</li>";
  $("result-warnings").innerHTML = record.warnings.length
    ? record.warnings
        .map(
          (item) =>
            `<li>مطالبة سابقة ${item.past_claim_id} / طبيب ${item.doctor_id} / تشابه ${item.similarity_score}</li>`
        )
        .join("")
    : "<li>لا توجد تحذيرات.</li>";
  $("result-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

function refresh() {
  const store = loadStore();
  renderKpis(statsFrom(store));
  renderRecent(store.claims);
  renderAudit(store.audit);
  renderLedger(store.claims);
}

function showView(name) {
  document.querySelectorAll(".tab").forEach((node) => node.classList.toggle("is-active", node.dataset.view === name));
  document.querySelectorAll(".view").forEach((node) => node.classList.toggle("is-active", node.id === `view-${name}`));
}

function boot() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => showView(tab.dataset.view));
  });

  const scenarioBox = $("scenarios");
  Object.entries(payloads).forEach(([key, payload], index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `scenario${index === 0 ? " is-active" : ""}`;
    button.textContent = scenarioLabels[key] || key;
    button.addEventListener("click", () => {
      document.querySelectorAll(".scenario").forEach((node) => node.classList.remove("is-active"));
      button.classList.add("is-active");
      fillForm(payload);
    });
    scenarioBox.appendChild(button);
  });
  fillForm(payloads.duplicate);

  $("claim-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = {
      transaction_id: form.transaction_id.value,
      patient: {
        id: form.patient_id.value,
        national_id: form.national_id.value,
      },
      claim: {
        claim_id: form.claim_id.value,
        procedure_code: form.procedure_code.value,
        doctor_id: form.doctor_id.value,
        department: form.department.value,
        hospital_id: form.hospital_id.value,
        triage_points: Number(form.triage_points.value || 0),
        policy_tier: form.policy_tier.value,
        requested_items: form.requested_items.value
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        justification: form.justification.value,
      },
    };
    const record = await decide(payload, loadStore());
    renderResult(record);
    refresh();
    toast("اكتملت معالجة المطالبة");
  });

  $("start-committee-demo").addEventListener("click", () => showView("intake"));

  $("reset-demo").addEventListener("click", () => {
    saveStore(seedStore());
    $("result-body").classList.add("hidden");
    $("result-empty").classList.remove("hidden");
    refresh();
    toast("أُعيد زرع السجل التجريبي");
  });

  refresh();
}

boot();
