from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


ACTION_CALL = "CALL"
ACTION_EMAIL = "EMAIL"
ACTION_DEMO = "DEMO"
ACTION_NURTURE = "NURTURE"
ACTION_REVIEW = "REVIEW"

VALID_ACTIONS = {ACTION_CALL, ACTION_EMAIL, ACTION_DEMO, ACTION_NURTURE, ACTION_REVIEW}


def _safe_int(val: Any, default: int = 0) -> int:
    """
    Safely converts a value (including NaN, None, floats) to an integer.
    """
    if val is None or pd.isna(val):
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_float(val: Any, default: Optional[float] = None) -> Optional[float]:
    """
    Safely converts a value (including NaN, None) to a float.
    """
    if val is None or pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


class RecommendationEngine:
    """
    Deterministic Next-Best-Action Recommendation Engine.

    Evaluates transparent, score-band rules and CRM behavioral signals to recommend
    the optimal sales follow-up action (CALL, EMAIL, DEMO, NURTURE, REVIEW).
    
    Computes an explicit recommendation confidence and rule-trace rationale that
    remain strictly separate from the ML conversion probability and lead score.
    """

    def recommend(
        self,
        lead_data: Dict[str, Any] | pd.DataFrame | pd.Series,
        lead_id: Optional[str] = None,
        lead_score: Optional[int] = None,
        conversion_probability: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Computes the Next-Best-Action recommendation for a given lead record.
        """
        # Extract dictionary of values
        if isinstance(lead_data, pd.DataFrame):
            record = lead_data.iloc[0].to_dict()
        elif isinstance(lead_data, pd.Series):
            record = lead_data.to_dict()
        else:
            record = dict(lead_data)

        extracted_id = record.get("lead_id", lead_id)
        raw_score = record.get("lead_score", lead_score)
        raw_prob = record.get("conversion_probability", conversion_probability)

        score = _safe_int(raw_score, default=None)
        prob = _safe_float(raw_prob, default=None)

        if score is None:
            if prob is not None:
                score = int(round(prob * 100))
            else:
                score = 50  # Default fallback if unscored

        # Extract relevant CRM signal inputs safely
        demo_requested = _safe_int(record.get("demo_requested"), default=0)
        pricing_visits = _safe_int(record.get("pricing_page_visit"), default=0)
        email_opened = _safe_int(record.get("email_opened"), default=0)
        email_clicked = _safe_int(record.get("email_clicked"), default=0)
        calls_made = _safe_int(record.get("call_made"), default=0)
        web_visits = _safe_int(record.get("web_visit"), default=0)
        days_since_contact = _safe_int(record.get("days_since_last_contact"), default=60)
        total_interactions = _safe_int(record.get("total_interactions"), default=0)

        confidence_reasons: List[str] = []
        action = ACTION_NURTURE
        score_band = ""
        trigger = ""
        rationale = ""
        base_confidence = 0.70

        # Rule evaluation by score band
        if score >= 80:
            score_band = "80-100 (High Priority)"
            base_confidence = 0.85
            confidence_reasons.append("Lead score is in the high-priority band (>= 80)")

            if demo_requested > 0:
                action = ACTION_DEMO
                trigger = "demo_requested"
                confidence_reasons.append(f"Direct demo request signal detected ({demo_requested} request(s))")
                if pricing_visits > 0:
                    base_confidence += 0.05
                    confidence_reasons.append("High pricing page intent aligns with demo readiness")
                rationale = (
                    f"Lead has a high priority score of {score} and explicitly requested a product demo. "
                    "Immediate scheduling of a product demonstration (DEMO) is recommended."
                )
            else:
                action = ACTION_CALL
                trigger = "high_score_no_demo"
                confidence_reasons.append("High conversion probability indicates readiness for direct phone call")
                if days_since_contact <= 14:
                    base_confidence += 0.05
                    confidence_reasons.append("Recent contact recency (<= 14 days) reinforces call timeliness")
                rationale = (
                    f"Lead has a high priority score of {score} without an active demo request. "
                    "Direct phone outreach (CALL) is recommended to qualify intent and advance the deal."
                )

        elif 60 <= score <= 79:
            score_band = "60-79 (Warm Opportunity)"
            base_confidence = 0.75
            confidence_reasons.append("Lead score is in the warm opportunity band (60-79)")

            # Check email engagement vs strong recent interaction
            has_high_email = (email_clicked >= 1) or (email_opened >= 3)
            has_recent_interaction = (days_since_contact <= 14) or (calls_made >= 1) or (total_interactions >= 5)

            if has_high_email and not (has_recent_interaction and days_since_contact <= 7):
                action = ACTION_EMAIL
                trigger = "high_email_engagement"
                confidence_reasons.append(
                    f"Strong email engagement detected ({email_opened} opens, {email_clicked} clicks)"
                )
                if email_clicked >= 1:
                    base_confidence += 0.05
                    confidence_reasons.append("Active link click-throughs confirm email as effective follow-up channel")
                rationale = (
                    f"Lead has a warm score of {score} with proven email responsiveness. "
                    "A personalized email follow-up (EMAIL) with targeted collateral is recommended."
                )
            elif has_recent_interaction:
                action = ACTION_CALL
                trigger = "strong_recent_interaction"
                confidence_reasons.append(
                    f"Active recent engagement detected (last contact {days_since_contact} days ago)"
                )
                if total_interactions >= 4:
                    base_confidence += 0.04
                    confidence_reasons.append("High cumulative touchpoints support proactive phone call")
                rationale = (
                    f"Lead has a warm score of {score} with strong recent interaction history. "
                    "A phone follow-up (CALL) is recommended to maintain sales momentum."
                )
            else:
                action = ACTION_EMAIL
                trigger = "moderate_score_standard_nurture_email"
                confidence_reasons.append("Standard email outreach appropriate for warm lead without recent calls")
                rationale = (
                    f"Lead has a warm score of {score}. An informative email touchpoint (EMAIL) is recommended "
                    "to re-engage interest."
                )

        elif 40 <= score <= 59:
            score_band = "40-59 (Developing / Mid-Funnel)"
            base_confidence = 0.72
            action = ACTION_NURTURE
            trigger = "moderate_score_nurture"
            confidence_reasons.append("Lead score is in the mid-funnel band (40-59)")
            confidence_reasons.append("Sales rep time is preserved by routing to automated nurture campaigns")
            rationale = (
                f"Lead has a moderate score of {score}. Marketing nurture sequence (NURTURE) is recommended "
                "to build product awareness and cultivate higher intent."
            )

        else:  # score < 40
            score_band = "0-39 (Cold / Early Stage)"
            base_confidence = 0.82
            action = ACTION_NURTURE
            trigger = "low_score_long_term_nurture"
            confidence_reasons.append("Lead score is in the low-priority band (< 40)")
            confidence_reasons.append("Automated drip campaign prevents premature sales rep overhead")
            rationale = (
                f"Lead has a low score of {score}. Long-term drip nurture (NURTURE) is recommended "
                "until behavioral signals indicate readiness."
            )

        # General confidence boundary penalties
        if score >= 60 and days_since_contact > 90:
            base_confidence -= 0.05
            confidence_reasons.append("Stale contact recency (> 90 days) slightly moderates action urgency")

        # Clamp confidence to valid deterministic range [0.50, 0.95]
        recommendation_confidence = round(float(np.clip(base_confidence, 0.50, 0.95)), 2)

        return {
            "lead_id": extracted_id,
            "lead_score": score,
            "conversion_probability": prob,
            "recommended_action": action,
            "recommendation_confidence": recommendation_confidence,
            "confidence_reasons": confidence_reasons,
            "rationale": rationale,
            "rule_trace": {
                "score_band": score_band,
                "trigger": trigger,
                "action": action,
            },
        }

    def recommend_batch(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Generates recommendations for a collection of lead records.
        """
        results = []
        for _, row in df.iterrows():
            results.append(self.recommend(row))
        return results
