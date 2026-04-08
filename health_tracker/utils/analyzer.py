"""
Health Analyzer - Correlates phone usage patterns with mental health data
and generates intelligent alerts and recommendations.
"""

from datetime import date
from health_tracker import database as db


# ─── Thresholds ───────────────────────────────────────────────────────────────

SCREEN_TIME_WARNING_MINUTES = 240    # 4 hours/day
SCREEN_TIME_CRITICAL_MINUTES = 360   # 6 hours/day
SOCIAL_MEDIA_WARNING_MINUTES = 120   # 2 hours/day
GAMING_WARNING_MINUTES = 180         # 3 hours/day
LOW_MOOD_THRESHOLD = 4               # mood_score <= 4
HIGH_ANXIETY_THRESHOLD = 7           # anxiety_level >= 7
HIGH_STRESS_THRESHOLD = 7            # stress_level >= 7
LOW_SLEEP_HOURS = 6.0
POOR_SLEEP_QUALITY = 4


APP_CATEGORY_LABELS = {
    "social_media": "Social Media",
    "gaming": "Gaming",
    "work": "Work / Productivity",
    "entertainment": "Entertainment",
    "other": "Other",
}

AILMENT_LABELS = {
    "headache": "Headache",
    "eye_strain": "Eye Strain",
    "neck_pain": "Neck / Shoulder Pain",
    "back_pain": "Back Pain",
    "insomnia": "Sleep Difficulty",
    "fatigue": "Fatigue",
    "anxiety_attack": "Anxiety Episode",
    "depression_episode": "Low Mood Episode",
    "wrist_pain": "Wrist / Thumb Pain",
    "dizziness": "Dizziness",
    "other": "Other",
}

MOOD_LABELS = {
    1: "Very Low",
    2: "Low",
    3: "Below Average",
    4: "Slightly Low",
    5: "Neutral",
    6: "Slightly Good",
    7: "Good",
    8: "Very Good",
    9: "Excellent",
    10: "Outstanding",
}

STRESS_COLOR_MAP = {
    range(1, 4): "#4CAF50",   # Green - Low
    range(4, 7): "#FF9800",   # Orange - Moderate
    range(7, 11): "#F44336",  # Red - High
}


def get_stress_color(score: int) -> str:
    for r, color in STRESS_COLOR_MAP.items():
        if score in r:
            return color
    return "#9E9E9E"


def get_mood_emoji(score: int) -> str:
    emojis = {1: "😞", 2: "😔", 3: "😕", 4: "😟", 5: "😐",
               6: "🙂", 7: "😊", 8: "😄", 9: "😁", 10: "🤩"}
    return emojis.get(score, "😐")


def format_duration(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m" if mins else f"{hours}h"


def analyze_today() -> dict:
    """
    Run full daily analysis — correlate usage, mental health, and ailments.
    Returns a risk summary dict and generates DB alerts if needed.
    """
    usage = db.get_usage_summary_today()
    checkin = db.get_checkin_today()
    ailments = db.get_ailments_last_n_days(1)
    today_ailments = [a for a in ailments if a["log_date"] == str(date.today())]

    risks = []
    recommendations = []

    # ── Screen time checks ────────────────────────────────────────────────────
    total = usage.get("total_screen_time_minutes", 0)
    if total >= SCREEN_TIME_CRITICAL_MINUTES:
        risks.append(("critical", "usage",
                       f"Critical: {format_duration(total)} of screen time today. "
                       "This significantly increases risk of digital eye strain, "
                       "anxiety, and sleep disruption."))
        recommendations.append("Take a 20-minute break every 2 hours (20-20-20 rule).")
    elif total >= SCREEN_TIME_WARNING_MINUTES:
        risks.append(("warning", "usage",
                       f"Warning: {format_duration(total)} of screen time today. "
                       "Consider reducing usage to under 4 hours."))
        recommendations.append("Set a screen time limit goal in your settings.")

    social = usage.get("social_media_minutes", 0)
    if social >= SOCIAL_MEDIA_WARNING_MINUTES:
        risks.append(("warning", "mental_health",
                       f"High social media usage ({format_duration(social)}) linked to "
                       "increased anxiety, FOMO, and low self-esteem."))
        recommendations.append("Try a 30-minute social media detox after 9 PM.")

    # ── Mental health checks ──────────────────────────────────────────────────
    if checkin:
        mood = checkin.get("mood_score", 5)
        anxiety = checkin.get("anxiety_level", 5)
        stress = checkin.get("stress_level", 5)
        sleep_hrs = checkin.get("sleep_hours") or 0
        sleep_q = checkin.get("sleep_quality") or 5

        if mood <= LOW_MOOD_THRESHOLD:
            risks.append(("warning", "mental_health",
                           f"Low mood score ({mood}/10) recorded today. "
                           "Extended phone use may be contributing."))
            recommendations.append("Try a 15-minute walk without your phone today.")

        if anxiety >= HIGH_ANXIETY_THRESHOLD:
            risks.append(("warning", "mental_health",
                           f"High anxiety level ({anxiety}/10) today. "
                           "Notifications and social media are common triggers."))
            recommendations.append("Enable 'Do Not Disturb' mode for focused hours.")

        if stress >= HIGH_STRESS_THRESHOLD:
            risks.append(("critical", "mental_health",
                           f"High stress level ({stress}/10). "
                           "Digital overload is a key stress amplifier."))
            recommendations.append("Practice 5 minutes of deep breathing or meditation.")

        if sleep_hrs < LOW_SLEEP_HOURS:
            risks.append(("warning", "physical",
                           f"Only {sleep_hrs}h of sleep reported. "
                           "Blue light from screens before bed disrupts melatonin."))
            recommendations.append("Avoid screens 1 hour before bedtime.")

        if sleep_q <= POOR_SLEEP_QUALITY:
            risks.append(("warning", "physical",
                           "Poor sleep quality reported. Consider a digital wind-down routine."))

    # ── Physical ailment correlation ──────────────────────────────────────────
    for ailment in today_ailments:
        atype = ailment["ailment_type"]
        severity = ailment["severity"]
        label = AILMENT_LABELS.get(atype, atype)
        if severity >= 7:
            risks.append(("critical", "physical",
                           f"Severe {label} (severity {severity}/10) logged today. "
                           "Consult a doctor if this persists."))
        elif severity >= 4:
            risks.append(("warning", "physical",
                           f"Moderate {label} reported — often linked to prolonged screen use."))

    # Save new alerts to DB
    for alert_type, category, message in risks:
        db.save_alert(alert_type, category, message)

    overall_risk = "low"
    if any(r[0] == "critical" for r in risks):
        overall_risk = "critical"
    elif any(r[0] == "warning" for r in risks):
        overall_risk = "moderate"

    return {
        "overall_risk": overall_risk,
        "risks": risks,
        "recommendations": list(dict.fromkeys(recommendations)),  # deduplicate
        "total_screen_time": total,
        "has_checkin": checkin is not None,
    }


def get_weekly_trend() -> dict:
    """Return 7-day aggregated trends for dashboard charts."""
    checkins = db.get_checkins_last_n_days(7)
    usage_days = db.get_usage_last_n_days(7)

    mood_trend = [c["mood_score"] for c in reversed(checkins)]
    stress_trend = [c["stress_level"] for c in reversed(checkins)]
    anxiety_trend = [c["anxiety_level"] for c in reversed(checkins)]
    usage_trend = [u["total_screen_time_minutes"] for u in reversed(usage_days)]
    dates = [u["summary_date"][-5:] for u in reversed(usage_days)]  # MM-DD

    avg_mood = sum(mood_trend) / len(mood_trend) if mood_trend else 5
    avg_stress = sum(stress_trend) / len(stress_trend) if stress_trend else 5
    avg_screen = sum(usage_trend) / len(usage_trend) if usage_trend else 0

    return {
        "dates": dates,
        "mood_trend": mood_trend,
        "stress_trend": stress_trend,
        "anxiety_trend": anxiety_trend,
        "usage_trend": usage_trend,
        "avg_mood": round(avg_mood, 1),
        "avg_stress": round(avg_stress, 1),
        "avg_screen_time_minutes": round(avg_screen),
    }


def get_health_score() -> int:
    """
    Calculate a composite mental health score (0-100) based on recent data.
    Higher = healthier digital habits and mental state.
    """
    checkins = db.get_checkins_last_n_days(3)
    usage_days = db.get_usage_last_n_days(3)

    if not checkins:
        return 50  # neutral default

    avg_mood = sum(c["mood_score"] for c in checkins) / len(checkins)
    avg_anxiety = sum(c["anxiety_level"] for c in checkins) / len(checkins)
    avg_stress = sum(c["stress_level"] for c in checkins) / len(checkins)
    avg_sleep = sum((c["sleep_hours"] or 7) for c in checkins) / len(checkins)

    avg_screen = (sum(u["total_screen_time_minutes"] for u in usage_days) / len(usage_days)) if usage_days else 180

    # Weighted scoring components
    mood_score = (avg_mood / 10) * 25
    anxiety_score = ((10 - avg_anxiety) / 10) * 20
    stress_score = ((10 - avg_stress) / 10) * 20
    sleep_score = min(avg_sleep / 8, 1.0) * 20
    usage_score = max(0, (1 - avg_screen / SCREEN_TIME_CRITICAL_MINUTES)) * 15

    total = mood_score + anxiety_score + stress_score + sleep_score + usage_score
    return max(0, min(100, round(total)))
