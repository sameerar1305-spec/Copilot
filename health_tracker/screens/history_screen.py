"""
Health History & Trends Screen
Shows weekly/monthly trends for mental health scores, screen time,
and medical ailments. Uses ASCII-style text charts since matplotlib
rendering requires extra setup in Kivy.
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.progressbar import MDProgressBar
from kivy.metrics import dp
from kivy.clock import Clock

from health_tracker import database as db
from health_tracker.utils.analyzer import (
    get_weekly_trend, format_duration, get_mood_emoji,
    AILMENT_LABELS, APP_CATEGORY_LABELS
)


def ascii_bar(value: float, max_value: float, width: int = 10) -> str:
    """Generate a text-based progress bar."""
    if max_value == 0:
        return "─" * width
    filled = int((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)


class TrendRow(MDBoxLayout):
    """One row in a trend table: date + bar + value."""

    def __init__(self, date_label="", value=0, max_value=10,
                 value_text="", color=(0.11, 0.46, 0.70, 1), **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(28)

        self.add_widget(MDLabel(
            text=date_label,
            font_style="Caption",
            size_hint_x=None, width=dp(52),
            halign="left",
        ))
        bar = MDProgressBar(
            value=value, max=max_value,
            color=color,
            size_hint_y=None, height=dp(10),
        )
        self.add_widget(bar)
        self.add_widget(MDLabel(
            text=value_text or str(value),
            font_style="Caption",
            size_hint_x=None, width=dp(56),
            halign="right",
        ))


class HistoryScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "history"
        self._period = 7  # days to show
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", spacing=0)

        from kivymd.uix.toolbar import MDTopAppBar
        toolbar = MDTopAppBar(
            title="Health History",
            md_bg_color=(0.11, 0.46, 0.70, 1),
            specific_text_color=(1, 1, 1, 1),
            left_action_items=[["arrow-left", lambda x: self._go_back()]],
            elevation=4,
        )
        root.add_widget(toolbar)

        # Period selector
        period_row = MDBoxLayout(
            orientation="horizontal", spacing=dp(4),
            padding=[dp(12), dp(6)],
            size_hint_y=None, height=dp(44),
        )
        for days, label in [(7, "7 Days"), (14, "14 Days"), (30, "30 Days")]:
            btn = MDFlatButton(
                text=label,
                on_release=lambda x, d=days: self._set_period(d),
            )
            period_row.add_widget(btn)
        root.add_widget(period_row)

        scroll = MDScrollView()
        self.content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=[dp(16), dp(8), dp(16), dp(80)],
            size_hint_y=None,
        )
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll.add_widget(self.content)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_enter(self):
        Clock.schedule_once(lambda dt: self._load_data(), 0.1)

    def _set_period(self, days: int):
        self._period = days
        self._load_data()

    def _load_data(self, *args):
        self.content.clear_widgets()
        trend = get_weekly_trend()
        checkins = db.get_checkins_last_n_days(self._period)
        usage_days = db.get_usage_last_n_days(self._period)
        ailments = db.get_ailments_last_n_days(self._period)

        self._add_mood_trend(checkins)
        self._add_stress_anxiety_trend(checkins)
        self._add_sleep_trend(checkins)
        self._add_screen_time_trend(usage_days)
        self._add_usage_breakdown(usage_days)
        self._add_ailment_summary(ailments)
        self._add_weekly_stats(checkins, usage_days)

    # ──────────────────────────────────────────────────────────────────────────

    def _add_mood_trend(self, checkins):
        self.content.add_widget(MDLabel(
            text="Mood Trend",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(32),
        ))
        if not checkins:
            self._add_empty_card("No check-in data yet.")
            return

        card = self._make_card(len(checkins) * dp(32) + dp(40))
        for c in reversed(checkins):
            mood = c["mood_score"]
            emoji = get_mood_emoji(mood)
            color = (0.18, 0.65, 0.18, 1) if mood >= 6 else (1, 0.6, 0, 1) if mood >= 4 else (0.96, 0.26, 0.21, 1)
            card.add_widget(TrendRow(
                date_label=c["checkin_date"][-5:],
                value=mood, max_value=10,
                value_text=f"{emoji} {mood}/10",
                color=color,
            ))
        self.content.add_widget(card)

    def _add_stress_anxiety_trend(self, checkins):
        self.content.add_widget(MDLabel(
            text="Stress & Anxiety Trend",
            font_style="Subtitle1", bold=True,
            size_hint_y=None, height=dp(28),
        ))
        if not checkins:
            self._add_empty_card("No check-in data yet.")
            return

        card = self._make_card(len(checkins) * dp(44) + dp(40))
        card.add_widget(MDLabel(
            text="Date         Stress             Anxiety",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None, height=dp(20),
        ))
        for c in reversed(checkins):
            row = MDBoxLayout(
                orientation="vertical", spacing=dp(2),
                size_hint_y=None, height=dp(44),
            )
            row.add_widget(TrendRow(
                date_label=c["checkin_date"][-5:],
                value=c["stress_level"], max_value=10,
                value_text=f"Stress: {c['stress_level']}/10",
                color=(0.96, 0.26, 0.21, 0.8),
            ))
            row.add_widget(TrendRow(
                date_label="",
                value=c["anxiety_level"], max_value=10,
                value_text=f"Anxiety: {c['anxiety_level']}/10",
                color=(1, 0.6, 0, 0.8),
            ))
            card.add_widget(row)
        self.content.add_widget(card)

    def _add_sleep_trend(self, checkins):
        sleep_data = [(c["checkin_date"][-5:], c.get("sleep_hours") or 0, c.get("sleep_quality") or 0)
                      for c in reversed(checkins) if c.get("sleep_hours")]
        if not sleep_data:
            return

        self.content.add_widget(MDLabel(
            text="Sleep Trend",
            font_style="Subtitle1", bold=True,
            size_hint_y=None, height=dp(28),
        ))
        card = self._make_card(len(sleep_data) * dp(32) + dp(40))
        for date_label, hours, quality in sleep_data:
            color = (0.42, 0.24, 0.73, 1) if hours >= 7 else (1, 0.6, 0, 1) if hours >= 6 else (0.96, 0.26, 0.21, 1)
            card.add_widget(TrendRow(
                date_label=date_label,
                value=hours, max_value=10,
                value_text=f"{hours}h  Q:{quality}/10",
                color=color,
            ))
        self.content.add_widget(card)

    def _add_screen_time_trend(self, usage_days):
        self.content.add_widget(MDLabel(
            text="Daily Screen Time",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(32),
        ))
        if not usage_days:
            self._add_empty_card("No usage data yet.")
            return

        max_time = max(u["total_screen_time_minutes"] for u in usage_days) or 360
        card = self._make_card(len(usage_days) * dp(32) + dp(40))

        # Warning threshold line label
        card.add_widget(MDLabel(
            text=f"Warning threshold: 4h  |  Critical: 6h",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None, height=dp(20),
        ))

        for u in reversed(usage_days):
            total = u["total_screen_time_minutes"]
            color = (0.96, 0.26, 0.21, 1) if total >= 360 else (1, 0.6, 0, 1) if total >= 240 else (0.18, 0.65, 0.18, 1)
            card.add_widget(TrendRow(
                date_label=u["summary_date"][-5:],
                value=total, max_value=max(max_time, 360),
                value_text=format_duration(total),
                color=color,
            ))
        self.content.add_widget(card)

    def _add_usage_breakdown(self, usage_days):
        if not usage_days:
            return

        self.content.add_widget(MDLabel(
            text=f"Avg Usage by Category ({self._period}-day)",
            font_style="Subtitle1", bold=True,
            size_hint_y=None, height=dp(28),
        ))

        totals = {}
        for u in usage_days:
            for cat in ["social_media", "gaming", "work", "entertainment", "other"]:
                totals[cat] = totals.get(cat, 0) + u.get(f"{cat}_minutes", 0)

        n = len(usage_days)
        averages = {k: v // n for k, v in totals.items()}
        max_avg = max(averages.values()) or 60

        card = self._make_card(len(averages) * dp(32) + dp(24))
        colors = {
            "social_media": (0.91, 0.12, 0.39, 1),
            "gaming": (0.61, 0.15, 0.69, 1),
            "work": (0.13, 0.59, 0.95, 1),
            "entertainment": (1, 0.6, 0, 1),
            "other": (0.38, 0.49, 0.55, 1),
        }
        for cat, avg_mins in sorted(averages.items(), key=lambda x: -x[1]):
            if avg_mins == 0:
                continue
            card.add_widget(TrendRow(
                date_label=APP_CATEGORY_LABELS.get(cat, cat)[:10],
                value=avg_mins, max_value=max_avg,
                value_text=f"~{format_duration(avg_mins)}/d",
                color=colors.get(cat, (0.5, 0.5, 0.5, 1)),
            ))
        self.content.add_widget(card)

    def _add_ailment_summary(self, ailments):
        if not ailments:
            return

        self.content.add_widget(MDLabel(
            text="Symptom Log",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(32),
        ))

        # Frequency by type
        freq = {}
        for a in ailments:
            freq[a["ailment_type"]] = freq.get(a["ailment_type"], 0) + 1

        card = self._make_card(len(freq) * dp(32) + dp(24))
        max_freq = max(freq.values()) if freq else 1
        for atype, count in sorted(freq.items(), key=lambda x: -x[1]):
            label = AILMENT_LABELS.get(atype, atype)
            card.add_widget(TrendRow(
                date_label=label[:12],
                value=count, max_value=max_freq,
                value_text=f"{count}x",
                color=(0.96, 0.26, 0.21, 0.8),
            ))
        self.content.add_widget(card)

        # Recent entries
        recent_card = MDCard(
            orientation="vertical",
            padding=dp(12), spacing=dp(6),
            size_hint_y=None,
            elevation=1, radius=[dp(10)],
        )
        recent_card.add_widget(MDLabel(
            text="Recent Entries",
            font_style="Subtitle2", bold=True,
            size_hint_y=None, height=dp(24),
        ))
        for a in ailments[:6]:
            atype = AILMENT_LABELS.get(a["ailment_type"], a["ailment_type"])
            sev = a["severity"]
            sev_color = (0.96, 0.26, 0.21, 1) if sev >= 7 else (1, 0.6, 0, 1) if sev >= 4 else (0.18, 0.65, 0.18, 1)
            row = MDBoxLayout(
                orientation="horizontal", spacing=dp(8),
                size_hint_y=None, height=dp(28),
            )
            row.add_widget(MDLabel(
                text=f"{a['log_date'][-5:]}  {atype}",
                font_style="Body2",
            ))
            row.add_widget(MDLabel(
                text=f"{sev}/10",
                font_style="Caption",
                theme_text_color="Custom",
                text_color=sev_color,
                size_hint_x=None, width=dp(40),
                halign="right",
            ))
            recent_card.add_widget(row)
        recent_card.height = dp(30 * min(len(ailments), 6) + 48)
        self.content.add_widget(recent_card)

    def _add_weekly_stats(self, checkins, usage_days):
        if not checkins and not usage_days:
            return

        self.content.add_widget(MDLabel(
            text=f"{self._period}-Day Summary",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(32),
        ))

        stats = {}
        if checkins:
            stats["Avg Mood"] = f"{sum(c['mood_score'] for c in checkins)/len(checkins):.1f}/10"
            stats["Avg Stress"] = f"{sum(c['stress_level'] for c in checkins)/len(checkins):.1f}/10"
            stats["Avg Anxiety"] = f"{sum(c['anxiety_level'] for c in checkins)/len(checkins):.1f}/10"
            sleep_data = [c["sleep_hours"] for c in checkins if c.get("sleep_hours")]
            if sleep_data:
                stats["Avg Sleep"] = f"{sum(sleep_data)/len(sleep_data):.1f}h/night"
            stats["Check-in Days"] = f"{len(checkins)}/{self._period}"

        if usage_days:
            total_screen = sum(u["total_screen_time_minutes"] for u in usage_days)
            stats["Total Screen Time"] = format_duration(total_screen)
            stats["Avg Daily Screen"] = format_duration(total_screen // len(usage_days))
            stats["Busiest Day"] = max(
                usage_days, key=lambda u: u["total_screen_time_minutes"]
            )["summary_date"][-5:]

        card = MDCard(
            orientation="vertical",
            padding=dp(16), spacing=dp(8),
            size_hint_y=None, height=dp(len(stats) * dp(32) + dp(24)),
            elevation=2, radius=[dp(12)],
        )
        for label, value in stats.items():
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(28),
            )
            row.add_widget(MDLabel(
                text=label,
                font_style="Body2",
                theme_text_color="Secondary",
            ))
            row.add_widget(MDLabel(
                text=value,
                font_style="Body2", bold=True,
                halign="right",
            ))
            card.add_widget(row)
        self.content.add_widget(card)

    def _make_card(self, height=None) -> MDCard:
        card = MDCard(
            orientation="vertical",
            padding=dp(12), spacing=dp(4),
            size_hint_y=None,
            elevation=2, radius=[dp(12)],
        )
        if height:
            card.height = height
        card.bind(minimum_height=card.setter("height"))
        return card

    def _add_empty_card(self, message: str):
        card = MDCard(
            orientation="vertical",
            padding=dp(16),
            size_hint_y=None, height=dp(64),
            elevation=1, radius=[dp(10)],
        )
        card.add_widget(MDLabel(
            text=message,
            font_style="Body2",
            theme_text_color="Secondary",
            halign="center",
        ))
        self.content.add_widget(card)

    def _go_back(self):
        self.manager.current = "home"
