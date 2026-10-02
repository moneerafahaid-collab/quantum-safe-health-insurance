from __future__ import annotations

import hashlib
import math
from typing import Iterable

from qshield.config import settings
from qshield.schemas import AnalysisResult, ClaimRecord, FlaggedClaim


class QGNNInferenceEngine:
    """محرك شبكات الرسم البياني العصبية الكوانتية لرصد اتساق التبرير الطبي."""

    def __init__(
        self,
        similarity_threshold: float | None = None,
        review_threshold: float | None = None,
    ) -> None:
        self.similarity_threshold = similarity_threshold or settings.similarity_threshold
        self.review_threshold = review_threshold or settings.review_threshold

    def quantum_state_embedding(self, medical_justification: str) -> list[float]:
        """تحويل النص الطبي إلى متجه ثابت يمثل حالة كوانتية محاكاة."""
        tokens = [token for token in medical_justification.split() if token]
        if not tokens:
            return [0.0]

        vector: list[float] = []
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            amplitude = int.from_bytes(digest[:2], "big") / 65535.0
            phase = int.from_bytes(digest[2:4], "big") / 65535.0
            vector.append(round((amplitude + phase) / 2.0, 4))
        return vector

    def evaluate_claim_consistency(
        self,
        current_claim: ClaimRecord | dict,
        patient_history: Iterable[ClaimRecord | dict],
    ) -> AnalysisResult:
        """تحليل الاتساق بين المطالبة الحالية وسجل المريض."""
        current = self._as_claim(current_claim)
        current_vector = self.quantum_state_embedding(current.justification)

        duplicates_found: list[FlaggedClaim] = []
        hard_duplicates: list[FlaggedClaim] = []
        max_jaccard = 0.0
        max_quantum = 0.0

        for past in patient_history:
            previous = self._as_claim(past)
            if previous.procedure_code != current.procedure_code:
                continue
            if previous.claim_id == current.claim_id:
                continue

            jaccard = self._jaccard(current.justification, previous.justification)
            quantum = self._cosine(current_vector, self.quantum_state_embedding(previous.justification))
            similarity = round(max(jaccard, quantum), 4)

            max_jaccard = max(max_jaccard, jaccard)
            max_quantum = max(max_quantum, quantum)

            if similarity >= self.review_threshold:
                flagged = FlaggedClaim(
                    past_claim_id=previous.claim_id,
                    doctor_id=previous.doctor_id,
                    similarity_score=round(similarity, 2),
                    quantum_similarity=round(quantum, 2),
                )
                duplicates_found.append(flagged)
                if jaccard >= self.similarity_threshold:
                    hard_duplicates.append(flagged)

        is_duplicate = len(hard_duplicates) > 0
        peak = max(max_jaccard, max_quantum)

        if is_duplicate:
            status = "REJECTED_DUPLICATE"
        elif peak >= self.review_threshold:
            status = "MANUAL_REVIEW"
        else:
            status = "APPROVED"

        return AnalysisResult(
            consistency_score=round(1.0 - peak, 2),
            similarity_score=round(peak, 2),
            quantum_similarity=round(max_quantum, 2),
            is_duplicate_detected=is_duplicate,
            status=status,
            flagged_claims=hard_duplicates if is_duplicate else duplicates_found,
        )

    @staticmethod
    def _as_claim(value: ClaimRecord | dict) -> ClaimRecord:
        return value if isinstance(value, ClaimRecord) else ClaimRecord.model_validate(value)

    @staticmethod
    def _jaccard(left: str, right: str) -> float:
        left_tokens = set(left.split())
        right_tokens = set(right.split())
        if not left_tokens and not right_tokens:
            return 1.0
        union = left_tokens | right_tokens
        if not union:
            return 0.0
        return round(len(left_tokens & right_tokens) / len(union), 4)

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        size = max(len(left), len(right), 1)
        a = left + [0.0] * (size - len(left))
        b = right + [0.0] * (size - len(right))
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return round(dot / (norm_a * norm_b), 4)
