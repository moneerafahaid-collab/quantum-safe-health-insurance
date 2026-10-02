from __future__ import annotations

from dataclasses import dataclass

from qshield.schemas import ClaimRecord, EntitlementFinding, EntitlementResult


@dataclass(frozen=True)
class ProcedureRule:
    name: str
    category: str  # vital | er_covered | elective | luxury
    points_required: int
    entitled_tiers: tuple[str, ...]


PROCEDURE_CATALOG: dict[str, ProcedureRule] = {
    "ER-CPR-01": ProcedureRule("إنعاش قلبي رئوي", "vital", 40, ("BASIC", "ESSENTIAL", "PREMIUM")),
    "ER-INTUBATION-01": ProcedureRule("تنبيب رغامي", "vital", 50, ("BASIC", "ESSENTIAL", "PREMIUM")),
    "ER-DEFIB-01": ProcedureRule("صدمات كهربائية", "vital", 45, ("BASIC", "ESSENTIAL", "PREMIUM")),
    "ER-HEMORRHAGE-01": ProcedureRule("سيطرة على نزيف حيوي", "vital", 35, ("BASIC", "ESSENTIAL", "PREMIUM")),
    "ER-THROMBOLYSIS-01": ProcedureRule("مذيب جلطة", "vital", 55, ("BASIC", "ESSENTIAL", "PREMIUM")),
    "ER-STABILIZE-01": ProcedureRule("تثبيت أولي في الطوارئ", "er_covered", 10, ("BASIC", "ESSENTIAL", "PREMIUM")),
    "ER-ECG-01": ProcedureRule("تخطيط قلب طوارئ", "er_covered", 10, ("BASIC", "ESSENTIAL", "PREMIUM")),
    "LAB-CBC-01": ProcedureRule("تحليل دم كامل", "er_covered", 8, ("BASIC", "ESSENTIAL", "PREMIUM")),
    "CT-TRAUMA-01": ProcedureRule("أشعة مقطعية للحوادث", "er_covered", 30, ("BASIC", "ESSENTIAL", "PREMIUM")),
    "CT-CHEST-02": ProcedureRule("أشعة مقطعية للصدر", "er_covered", 25, ("ESSENTIAL", "PREMIUM")),
    "MRI-LUMBAR-01": ProcedureRule("رنين أسفل الظهر", "elective", 70, ("PREMIUM",)),
    "SURGERY-KNEE-ELECTIVE-01": ProcedureRule("عملية ركبة اختيارية", "elective", 80, ("PREMIUM",)),
    "PRIVATE-SUITE-01": ProcedureRule("جناح خاص", "luxury", 0, ("PREMIUM",)),
    "COSMETIC-FILLER-01": ProcedureRule("إجراء تجميلي", "luxury", 0, ()),
    "DENTAL-WHITENING-01": ProcedureRule("تبييض أسنان", "luxury", 0, ()),
}

FRAUD_THRESHOLD = 50


class HospitalERFraudEngine:
    """رصد تلاعب التأمين في قسم الطوارئ: طلبات بلا أحقية مقابل عمليات حيوية بالنقاط."""

    def evaluate(self, claim: ClaimRecord | dict) -> EntitlementResult:
        current = claim if isinstance(claim, ClaimRecord) else ClaimRecord.model_validate(claim)
        if current.department.upper() != "ER":
            return EntitlementResult(
                applies=False,
                status="APPROVED",
                fraud_score=0,
                triage_points=current.triage_points,
                findings=[],
                vital_approved=False,
            )

        codes = [current.procedure_code, *current.requested_items]
        seen: set[str] = set()
        findings: list[EntitlementFinding] = []
        fraud_score = 0
        vital_ok = False
        not_entitled = 0
        luxury_count = 0

        for code in codes:
            if not code or code in seen:
                continue
            seen.add(code)
            finding = self._inspect(code, current.policy_tier, current.triage_points)
            findings.append(finding)
            if finding.category == "vital" and finding.entitled:
                vital_ok = True
            if finding.category in {"elective", "luxury"} and not finding.entitled:
                not_entitled += 1
                fraud_score += 40 if finding.category == "luxury" else 25
                if finding.category == "luxury":
                    luxury_count += 1
            elif finding.category == "er_covered" and not finding.entitled:
                not_entitled += 1
                fraud_score += 20

        extra_items = max(0, len(seen) - 1)
        if current.triage_points < 25 and extra_items >= 2:
            fraud_score += 20

        if fraud_score >= FRAUD_THRESHOLD or luxury_count > 0:
            status = "HOSPITAL_FRAUD"
        elif not_entitled > 0:
            status = "REJECTED_NOT_ENTITLED"
        elif vital_ok and all(item.category == "vital" or item.entitled for item in findings):
            status = "APPROVED_VITAL_POINTS"
        elif any(item.category == "vital" and not item.entitled for item in findings):
            status = "MANUAL_REVIEW"
        else:
            status = "APPROVED"

        return EntitlementResult(
            applies=True,
            status=status,
            fraud_score=min(fraud_score, 100),
            triage_points=current.triage_points,
            findings=findings,
            vital_approved=vital_ok,
        )

    @staticmethod
    def _inspect(code: str, policy_tier: str, triage_points: int) -> EntitlementFinding:
        rule = PROCEDURE_CATALOG.get(code)
        if rule is None:
            return EntitlementFinding(
                procedure_code=code,
                name=code,
                category="elective",
                points_required=0,
                entitled=False,
                reason="إجراء غير مدرج في أحقية الطوارئ لهذه الوثيقة.",
            )

        if rule.category == "vital":
            if triage_points >= rule.points_required:
                return EntitlementFinding(
                    procedure_code=code,
                    name=rule.name,
                    category="vital",
                    points_required=rule.points_required,
                    entitled=True,
                    reason=f"عملية حيوية: النقاط {triage_points} تحقق الحد {rule.points_required}.",
                )
            return EntitlementFinding(
                procedure_code=code,
                name=rule.name,
                category="vital",
                points_required=rule.points_required,
                entitled=False,
                reason=f"عملية حيوية تحتاج {rule.points_required} نقطة، والمتوفر {triage_points}.",
            )

        entitled = policy_tier.upper() in rule.entitled_tiers
        if entitled:
            reason = "مشمول في أحقية وثيقة المريض لقسم الطوارئ."
        elif rule.category == "luxury":
            reason = "طلب ترفيهي/غير طبي لا أحقية للمريض به في الطوارئ."
        else:
            reason = "إجراء غير مستحق على هذه الوثيقة من قسم الطوارئ."

        return EntitlementFinding(
            procedure_code=code,
            name=rule.name,
            category=rule.category,
            points_required=rule.points_required,
            entitled=entitled,
            reason=reason,
        )
