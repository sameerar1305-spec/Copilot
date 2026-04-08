"""
Home / Dashboard Screen
Displays daily health score, today's usage summary, quick stats,
recent alerts, and navigation to all other screens.
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
from kivy.properties import StringProperty, NumericProperty

from health_tracker import database as db
from health_tracker.utils.analyzer import (
    analyze_today, get_health_score, get_weekly_trend,
    format_duration, get_mood_emoji, MOOD_LABELS
)


class StatCard(MDCard):
    """Small summary card for a single metric."""

    def __init__(self, title="", value="", icon="", color="#1976D2", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(12)
        self.spacing = dp(4)
        self.size_hint_y = None
        self.height = dp(90)
        self.md_bg_color = (1, 1, 1, 1)
        self.elevation = 2
        self.radius = [dp(12)]

        icon_label = MDLabel(
            text=f"{icon}  {title}",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None,
            height=dp(20),
        )
        value_label = MDLabel(
            text=value,
            font_style="H6",
            theme_text_color="Custom",
            text_color=self._hex_to_rgba(color),
            bold=True,
        )
        self.add_widget(icon_label)
        self.add_widget(value_label)

    def _hex_to_rgba(self, hex_color: str):
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return (r / 255, g / 255, b / 255, 1)


class AlertItem(MDBoxLayout):
    """Single alert row."""

    def __init__(self, alert_type="warning", message="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(48)
        self.padding = [dp(4), 0]

        color_map = {"critical": "#F44336", "warning": "#FF9800", "recommendation": "#4CAF50"}
        icon_map = {"critical": "alert-circle", "warning": "alert", "recommendation": "lightbulb"}

        from kivymd.uix.label import MDIcon
        icon = MDLabel(
            text={"critical": "(!)", "warning": "(!)", "recommendation": "(i)"}.get(alert_type, ""),
            size_hint_x=None, width=dp(32),
            theme_text_color="Custom",
            text_color=self._hex(color_map.get(alert_type, "#9E9E9E")),
            bold=True,
        )
        msg = MDLabel(
            text=message[:100] + ("..." if len(message) > 100 else ""),
            font_style="Body2",
            theme_text_color="Primary",
        )
        self.add_widget(icon)
        self.add_widget(msg)

    def _hex(self, hex_color):
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return (r / 255, g / 255, b / 255, 1)


class HomeScreen(MDScreen):
    health_score = NumericProperty(50)
    risk_level = StringProperty("low")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "home"
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", spacing=0)

        # ── Top App Bar ───────────────────────────────────────────────────────
        from kivymd.uix.toolbar import MDTopAppBar
        toolbar = MDTopAppBar(
            title="MindGuard",
            md_bg_color=(0.11, 0.46, 0.70, 1),
            specific_text_color=(1, 1, 1, 1),
            right_action_items=[["bell-outline", lambda x: self.go_to("alerts")]],
            elevation=4,
        )
        root.add_widget(toolbar)

        # ── Scrollable content ────────────────────────────────────────────────
        scroll = MDScrollView()
        self.content = MDBoxLayout(
            orientation="vertical",
            spacing=dp(16),
            padding=[dp(16), dp(16), dp(16), dp(80)],
            size_hint_y=None,
        )
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll.add_widget(self.content)
        root.add_widget(scroll)

        self.add_widget(root)
        Clock.schedule_once(self._load_data, 0.1)

    def on_enter(self):
        Clock.schedule_once(self._load_data, 0)

    def _load_data(self, *args):
        self.content.clear_widgets()

        user = db.get_or_create_user()
        analysis = analyze_today()
        score = get_health_score()
        usage = db.get_usage_summary_today()
        checkin = db.get_checkin_today()
        trend = get_weekly_trend()

        self._add_greeting(user, score, analysis["overall_risk"])
        self._add_score_card(score, analysis["overall_risk"])
        self._add_quick_stats(usage, checkin)
        self._add_action_buttons(checkin)
        self._add_alerts_section(analysis["risks"])
        self._add_recommendations(analysis["recommendations"])

    def _add_greeting(self, user, score, risk):
        from datetime import datetime
        hour = datetime.now().hour
        greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        risk_color = {"low": "#4CAF50", "moderate": "#FF9800", "critical": "#F44336"}.get(risk, "#9E9E9E")

        box = MDBoxLayout(orientation="vertical", size_hint_y=None, height=dp(64), spacing=dp(4))
        box.add_widget(MDLabel(
            text=f"{greeting}, {user.get('name', 'User')}!",
            font_style="H5", bold=True,
            size_hint_y=None, height=dp(36),
        ))
        box.add_widget(MDLabel(
            text=f"Today's health risk: [{risk_color}]{risk.upper()}[/color]",
            font_style="Body1",
            markup=True,
            size_hint_y=None, height=dp(24),
        ))
        self.content.add_widget(box)

    def _add_score_card(self, score, risk):
        card = MDCard(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(8),
            size_hint_y=None, height=dp(150),
            elevation=4, radius=[dp(16)],
        )

        color_map = {"low": (0.18, 0.65, 0.18, 1), "moderate": (1, 0.6, 0, 1), "critical": (0.96, 0.26, 0.21, 1)}
        card.md_bg_color = color_map.get(risk, (0.18, 0.47, 0.71, 1))

        card.add_widget(MDLabel(
            text="Digital Wellness Score",
            font_style="Subtitle1",
            theme_text_color="Custom", text_color=(1, 1, 1, 0.85),
            size_hint_y=None, height=dp(28),
        ))
        card.add_widget(MDLabel(
            text=f"{score}/100",
            font_style="H3", bold=True,
            theme_text_color="Custom", text_color=(1, 1, 1, 1),
            size_hint_y=None, height=dp(52),
        ))
        bar = MDProgressBar(
            value=score, max=100,
            color=(1, 1, 1, 0.9),
            size_hint_y=None, height=dp(6),
        )
        card.add_widget(bar)
        self.content.add_widget(card)

    def _add_quick_stats(self, usage, checkin):
        self.content.add_widget(MDLabel(
            text="Today at a Glance",
            font_style="Subtitle1", bold=True,
            size_hint_y=None, height=dp(28),
        ))

        grid = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None, height=dp(96),
        )

        screen_time = format_duration(usage.get("total_screen_time_minutes", 0))
        mood = checkin["mood_score"] if checkin else "--"
        mood_emoji = get_mood_emoji(checkin["mood_score"]) if checkin else "?"
        pickups = usage.get("pickups_count", 0)

        grid.add_widget(StatCard(
            title="Screen Time", value=screen_time,
            icon="", color="#1976D2",
        ))
        grid.add_widget(StatCard(
            title="Mood", value=f"{mood_emoji} {mood}/10" if checkin else "Not logged",
            icon="", color="#4CAF50" if checkin and checkin["mood_score"] >= 6 else "#F44336",
        ))
        grid.add_widget(StatCard(
            title="Pickups", value=str(pickups),
            icon="", color="#FF9800",
        ))
        self.content.add_widget(grid)

        # Sleep stats if available
        if checkin and checkin.get("sleep_hours"):
            sleep_box = MDBoxLayout(
                orientation="horizontal", spacing=dp(8),
                size_hint_y=None, height=dp(96),
            )
            stress = checkin.get("stress_level", "--")
            anxiety = checkin.get("anxiety_level", "--")
            sleep_hrs = checkin.get("sleep_hours", "--")

            sleep_box.add_widget(StatCard(
                title="Sleep", value=f"{sleep_hrs}h",
                icon="", color="#673AB7",
            ))
            sleep_box.add_widget(StatCard(
                title="Stress", value=f"{stress}/10",
                icon="", color="#F44336" if isinstance(stress, int) and stress >= 7 else "#FF9800",
            ))
            sleep_box.add_widget(StatCard(
                title="Anxiety", value=f"{anxiety}/10",
                icon="", color="#F44336" if isinstance(anxiety, int) and anxiety >= 7 else "#FF9800",
            ))
            self.content.add_widget(sleep_box)

    def _add_action_buttons(self, checkin):
        self.content.add_widget(MDLabel(
            text="Quick Actions",
            font_style="Subtitle1", bold=True,
            size_hint_y=None, height=dp(28),
        ))

        btn_row = MDBoxLayout(
            orientation="horizontal", spacing=dp(8),
            size_hint_y=None, height=dp(44),
        )

        checkin_label = "Update Check-in" if checkin else "Daily Check-in"
        checkin_btn = MDRaisedButton(
            text=checkin_label,
            md_bg_color=(0.11, 0.46, 0.70, 1),
            on_release=lambda x: self.go_to("checkin"),
        )
        usage_btn = MDRaisedButton(
            text="Log Usage",
            md_bg_color=(0.18, 0.65, 0.18, 1),
            on_release=lambda x: self.go_to("usage"),
        )
        ailment_btn = MDFlatButton(
            text="Log Symptom",
            on_release=lambda x: self.go_to("usage"),
        )

        btn_row.add_widget(checkin_btn)
        btn_row.add_widget(usage_btn)
        btn_row.add_widget(ailment_btn)
        self.content.add_widget(btn_row)

    def _add_alerts_section(self, risks):
        if not risks:
            return
        self.content.add_widget(MDLabel(
            text=f"Health Alerts ({len(risks)})",
            font_style="Subtitle1", bold=True,
            size_hint_y=None, height=dp(28),
        ))
        alerts_card = MDCard(
            orientation="vertical",
            padding=dp(12), spacing=dp(4),
            size_hint_y=None,
            elevation=2, radius=[dp(12)],
        )
        for alert_type, category, message in risks[:4]:
            alerts_card.add_widget(AlertItem(alert_type=alert_type, message=message))
        alerts_card.height = dp(56 * min(len(risks), 4) + 24)
        self.content.add_widget(alerts_card)

    def _add_recommendations(self, recommendations):
        if not recommendations:
            return
        self.content.add_widget(MDLabel(
            text="Recommendations",
            font_style="Subtitle1", bold=True,
            size_hint_y=None, height=dp(28),
        ))
        rec_card = MDCard(
            orientation="vertical",
            padding=dp(12), spacing=dp(6),
            size_hint_y=None,
            elevation=2, radius=[dp(12)],
        )
        for rec in recommendations[:3]:
            rec_card.add_widget(MDLabel(
                text=f"  •  {rec}",
                font_style="Body2",
                size_hint_y=None, height=dp(32),
            ))
        rec_card.height = dp(42 * min(len(recommendations), 3) + 24)
        self.content.add_widget(rec_card)

    def go_to(self, screen_name: str):
        self.manager.current = screen_name
