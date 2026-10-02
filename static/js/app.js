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

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "تعذر تنفيذ الطلب");
  }
  return response.json();
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
  $("recent-claims").innerHTML = items
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
  $("audit-feed").innerHTML = items
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
  $("ledger-body").innerHTML = items
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

function renderResult(result) {
  const preview = result.decrypted_preview_for_demo;
  $("result-empty").classList.add("hidden");
  $("result-body").classList.remove("hidden");
  $("result-decision").textContent = decisionLabels[preview.decision] || preview.decision;
  $("result-decision").className = preview.decision;
  $("m-consistency").textContent = preview.metrics.consistency_score;
  $("m-similarity").textContent = preview.metrics.similarity_score;
  $("m-points").textContent = preview.metrics.triage_points ?? 0;
  $("m-fraud").textContent = preview.metrics.fraud_score ?? 0;
  $("result-hash").textContent = shortHash(preview.anonymized_patient_hash);
  const findings = preview.entitlement_findings || [];
  $("result-entitlement").innerHTML = findings.length
    ? findings
        .map(
          (item) =>
            `<li>${item.entitled ? "مستحق" : "غير مستحق"} — ${item.name} (${item.procedure_code}): ${item.reason}</li>`
        )
        .join("")
    : "<li>لا ينطبق رصد أحقية الطوارئ على هذه المطالبة.</li>";
  $("result-warnings").innerHTML = preview.warnings.length
    ? preview.warnings
        .map(
          (item) =>
            `<li>مطالبة سابقة ${item.past_claim_id} / طبيب ${item.doctor_id} / تشابه ${item.similarity_score}</li>`
        )
        .join("")
    : "<li>لا توجد تحذيرات.</li>";
  $("result-encrypted").textContent = result.encrypted_payload;
  $("result-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function refresh() {
  const [stats, claims, audit] = await Promise.all([
    api("/api/stats"),
    api("/api/claims"),
    api("/api/audit"),
  ]);
  renderKpis(stats);
  renderRecent(claims.items);
  renderAudit(audit.items);
  renderLedger(claims.items);
}

async function boot() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((node) => node.classList.remove("is-active"));
      document.querySelectorAll(".view").forEach((node) => node.classList.remove("is-active"));
      tab.classList.add("is-active");
      $(`view-${tab.dataset.view}`).classList.add("is-active");
    });
  });

  const payloads = await api("/api/demo-payloads");
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
    try {
      const result = await api("/api/nphies/claims", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      renderResult(result);
      await refresh();
      toast("اكتملت معالجة المطالبة");
    } catch (error) {
      toast(error.message);
    }
  });

  const startDemo = $("start-committee-demo");
  if (startDemo) {
    startDemo.addEventListener("click", () => {
      const intake = document.querySelector('[data-view="intake"]');
      if (intake) intake.click();
    });
  }

  $("reset-demo").addEventListener("click", async () => {
    await api("/api/demo/reset", { method: "POST" });
    $("result-body").classList.add("hidden");
    $("result-empty").classList.remove("hidden");
    await refresh();
    toast("أُعيد زرع السجل التجريبي");
  });

  await refresh();
}

boot().catch((error) => toast(error.message));
