"""
Profile & Settings Screen
Allows users to manage their profile, set screen time goals,
configure daily reminders, and view usage guidelines.
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch
from kivy.metrics import dp
from kivy.clock import Clock

from health_tracker import database as db
from health_tracker.utils.analyzer import get_health_score, format_duration


GENDER_OPTIONS = ["Male", "Female", "Non-binary", "Prefer not to say"]

HEALTH_TIPS = [
    ("Eye Care (20-20-20 Rule)",
     "Every 20 minutes, look at something 20 feet away for 20 seconds to reduce eye strain."),
    ("Screen Time Limits",
     "WHO recommends max 2h of recreational screen time daily. Keep total phone use under 4h."),
    ("Blue Light Exposure",
     "Blue light from screens suppresses melatonin. Enable night mode after 8 PM."),
    ("Mental Health & Social Media",
     "Studies link 3+ hrs of daily social media to depression, anxiety, and loneliness."),
    ("Nomophobia Awareness",
     "Phone addiction or nomophobia causes anxiety when separated from your phone. "
     "Practice phone-free periods daily."),
    ("Posture & Musculoskeletal Health",
     "Looking down at your phone causes 'text neck'. Hold your phone at eye level."),
    ("Sleep Hygiene",
     "Avoid phone use 1 hour before sleep. Notifications at night fragment sleep cycles."),
    ("Mindful Phone Use",
     "Turn off non-essential notifications. Check phone intentionally, not habitually."),
]

WHO_GUIDELINES = {
    "Daily recreational screen time": "< 2 hours",
    "Total daily screen time (adults)": "< 4 hours recommended",
    "Phone-free meals": "All meals — promotes mindful eating",
    "Pre-sleep phone-free window": "At least 60 minutes before bed",
    "Outdoor time": "Minimum 30 minutes/day",
    "Physical activity": "150 min moderate activity/week",
    "Social connections (offline)": "At least 1 meaningful interaction/day",
}


class ProfileScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "profile"
        self._name_field = None
        self._age_field = None
        self._gender_field = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", spacing=0)

        from kivymd.uix.toolbar import MDTopAppBar
        toolbar = MDTopAppBar(
            title="Profile & Settings",
            md_bg_color=(0.11, 0.46, 0.70, 1),
            specific_text_color=(1, 1, 1, 1),
            left_action_items=[["arrow-left", lambda x: self._go_back()]],
            elevation=4,
        )
        root.add_widget(toolbar)

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

    def on_enter(self):
        self.content.clear_widgets()
        self._build_profile_section()
        self._build_health_score_section()
        self._build_settings_section()
        self._build_guidelines_section()
        self._build_tips_section()

    def _build_profile_section(self):
        user = db.get_or_create_user()

        self.content.add_widget(MDLabel(
            text="Your Profile",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(32),
        ))

        card = MDCard(
            orientation="vertical",
            padding=dp(16), spacing=dp(8),
            size_hint_y=None, height=dp(230),
            elevation=3, radius=[dp(12)],
        )

        self._name_field = MDTextField(
            hint_text="Your Name",
            text=user.get("name", ""),
            helper_text="How should we address you?",
            helper_text_mode="on_focus",
            size_hint_y=None, height=dp(52),
        )

        self._age_field = MDTextField(
            hint_text="Age",
            text=str(user.get("age", "")) if user.get("age") else "",
            input_filter="int",
            helper_text="Used to personalize health recommendations",
            helper_text_mode="on_focus",
            size_hint_y=None, height=dp(52),
        )

        self._gender_field = MDTextField(
            hint_text="Gender",
            text=user.get("gender", "Prefer not to say"),
            helper_text="Male / Female / Non-binary / Prefer not to say",
            helper_text_mode="on_focus",
            size_hint_y=None, height=dp(52),
        )

        card.add_widget(self._name_field)
        card.add_widget(self._age_field)
        card.add_widget(self._gender_field)
        card.add_widget(MDRaisedButton(
            text="Save Profile",
            md_bg_color=(0.11, 0.46, 0.70, 1),
            size_hint_y=None, height=dp(40),
            on_release=lambda x: self._save_profile(),
        ))
        self.content.add_widget(card)

    def _build_health_score_section(self):
        score = get_health_score()
        checkins = db.get_checkins_last_n_days(7)
        usage = db.get_usage_last_n_days(7)

        self.content.add_widget(MDLabel(
            text="Your Wellness Overview",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(32),
        ))

        card = MDCard(
            orientation="vertical",
            padding=dp(16), spacing=dp(8),
            size_hint_y=None, height=dp(200),
            elevation=2, radius=[dp(12)],
        )

        color_map = {
            range(0, 40): (0.96, 0.26, 0.21, 1),
            range(40, 70): (1, 0.6, 0, 1),
            range(70, 101): (0.18, 0.65, 0.18, 1),
        }
        score_color = (0.18, 0.47, 0.71, 1)
        for r, c in color_map.items():
            if score in r:
                score_color = c

        card.add_widget(MDLabel(
            text=f"Wellness Score: {score}/100",
            font_style="H5", bold=True,
            theme_text_color="Custom",
            text_color=score_color,
            size_hint_y=None, height=dp(40),
        ))

        from kivymd.uix.progressbar import MDProgressBar
        card.add_widget(MDProgressBar(
            value=score, max=100,
            color=score_color,
            size_hint_y=None, height=dp(8),
        ))

        level = "Excellent" if score >= 80 else "Good" if score >= 60 else "Fair" if score >= 40 else "Needs Attention"
        card.add_widget(MDLabel(
            text=f"Status: {level}",
            font_style="Body1",
            size_hint_y=None, height=dp(28),
        ))

        stats_row = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(28),
        )
        stats_row.add_widget(MDLabel(
            text=f"Check-in streak: {len(checkins)} days",
            font_style="Caption",
        ))
        if usage:
            avg_screen = sum(u["total_screen_time_minutes"] for u in usage) // len(usage)
            stats_row.add_widget(MDLabel(
                text=f"Avg screen: {format_duration(avg_screen)}/day",
                font_style="Caption",
                halign="right",
            ))
        card.add_widget(stats_row)

        self.content.add_widget(card)

    def _build_settings_section(self):
        self.content.add_widget(MDLabel(
            text="App Settings",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(32),
        ))

        settings_items = [
            ("Daily check-in reminder", "Get notified at 9 PM to log your mood", True),
            ("Screen time warnings", "Alert when daily usage exceeds 4 hours", True),
            ("Sleep reminder", "Notify 1h before your target bedtime", True),
            ("Weekly health report", "Sunday summary of your wellness trends", False),
        ]

        card = MDCard(
            orientation="vertical",
            padding=dp(16), spacing=dp(8),
            size_hint_y=None,
            elevation=2, radius=[dp(12)],
        )
        for label, desc, default in settings_items:
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(52),
            )
            label_box = MDBoxLayout(orientation="vertical")
            label_box.add_widget(MDLabel(
                text=label,
                font_style="Subtitle2", bold=True,
                size_hint_y=None, height=dp(24),
            ))
            label_box.add_widget(MDLabel(
                text=desc,
                font_style="Caption",
                theme_text_color="Secondary",
                size_hint_y=None, height=dp(20),
            ))
            row.add_widget(label_box)
            switch = MDSwitch(active=default, size_hint_x=None, width=dp(56))
            row.add_widget(switch)
            card.add_widget(row)

        card.height = dp(52 * len(settings_items) + 32)
        self.content.add_widget(card)

    def _build_guidelines_section(self):
        self.content.add_widget(MDLabel(
            text="Healthy Digital Use Guidelines",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(32),
        ))

        card = MDCard(
            orientation="vertical",
            padding=dp(16), spacing=dp(6),
            size_hint_y=None,
            elevation=2, radius=[dp(12)],
        )
        for guideline, value in WHO_GUIDELINES.items():
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(32),
            )
            row.add_widget(MDLabel(
                text=guideline,
                font_style="Body2",
                theme_text_color="Secondary",
            ))
            row.add_widget(MDLabel(
                text=value,
                font_style="Body2", bold=True,
                halign="right",
                theme_text_color="Custom",
                text_color=(0.18, 0.47, 0.71, 1),
            ))
            card.add_widget(row)
        card.height = dp(38 * len(WHO_GUIDELINES) + 32)
        self.content.add_widget(card)

    def _build_tips_section(self):
        self.content.add_widget(MDLabel(
            text="Health Tips",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(32),
        ))

        for title, tip in HEALTH_TIPS:
            card = MDCard(
                orientation="vertical",
                padding=dp(16), spacing=dp(6),
                size_hint_y=None,
                elevation=1, radius=[dp(10)],
                md_bg_color=(0.97, 0.97, 1.0, 1),
            )
            card.add_widget(MDLabel(
                text=f"  {title}",
                font_style="Subtitle2", bold=True,
                size_hint_y=None, height=dp(24),
                theme_text_color="Custom",
                text_color=(0.11, 0.46, 0.70, 1),
            ))
            tip_label = MDLabel(
                text=tip,
                font_style="Body2",
                size_hint_y=None,
            )
            tip_label.bind(
                texture_size=lambda inst, val: setattr(inst, "height", val[1] + dp(8))
            )
            card.add_widget(tip_label)
            card.bind(minimum_height=card.setter("height"))
            self.content.add_widget(card)

    def _save_profile(self):
        name = self._name_field.text.strip() or "User"
        age_text = self._age_field.text.strip()
        age = int(age_text) if age_text.isdigit() else 25
        gender = self._gender_field.text.strip() or "Prefer not to say"

        db.update_user(name=name, age=age, gender=gender)

        from kivymd.uix.snackbar import MDSnackbar
        snack = MDSnackbar(text="Profile saved!", snackbar_x=dp(8), snackbar_y=dp(8))
        snack.size_hint_x = 0.9
        snack.open()

    def _go_back(self):
        self.manager.current = "home"
