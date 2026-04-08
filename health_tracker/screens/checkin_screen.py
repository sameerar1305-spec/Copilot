"""
Daily Mental Health Check-in Screen
Users log mood, anxiety, stress, sleep, energy, and social interaction
using intuitive sliders. Data is saved to SQLite and triggers analysis.
"""

from datetime import date
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.slider import MDSlider
from kivymd.uix.textfield import MDTextField
from kivy.metrics import dp
from kivy.clock import Clock

from health_tracker import database as db
from health_tracker.utils.analyzer import get_mood_emoji, MOOD_LABELS


CHECKIN_FIELDS = [
    {
        "key": "mood_score",
        "label": "Mood",
        "desc": "How are you feeling overall today?",
        "low_label": "Very Low",
        "high_label": "Outstanding",
        "icon": "emoticon-happy-outline",
        "color": "#4CAF50",
    },
    {
        "key": "anxiety_level",
        "label": "Anxiety Level",
        "desc": "How anxious or worried do you feel?",
        "low_label": "Calm",
        "high_label": "Extremely Anxious",
        "icon": "pulse",
        "color": "#FF9800",
    },
    {
        "key": "stress_level",
        "label": "Stress Level",
        "desc": "How stressed do you feel right now?",
        "low_label": "No Stress",
        "high_label": "Overwhelmed",
        "icon": "brain",
        "color": "#F44336",
    },
    {
        "key": "sleep_quality",
        "label": "Sleep Quality",
        "desc": "Rate the quality of your last night's sleep.",
        "low_label": "Very Poor",
        "high_label": "Excellent",
        "icon": "sleep",
        "color": "#673AB7",
    },
    {
        "key": "energy_level",
        "label": "Energy Level",
        "desc": "How energetic do you feel today?",
        "low_label": "Exhausted",
        "high_label": "Very Energetic",
        "icon": "lightning-bolt",
        "color": "#FFC107",
    },
    {
        "key": "social_interaction",
        "label": "Social Interaction",
        "desc": "How connected do you feel with others?",
        "low_label": "Very Isolated",
        "high_label": "Very Connected",
        "icon": "account-group",
        "color": "#2196F3",
    },
]


class SliderRow(MDBoxLayout):
    """Label + Slider + value display for a single metric."""

    def __init__(self, field_def: dict, initial_value: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.field_def = field_def
        self.orientation = "vertical"
        self.spacing = dp(4)
        self.size_hint_y = None
        self.height = dp(100)

        # Header: label + live value
        header = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None, height=dp(28),
        )
        color = field_def["color"]
        self.value_label = MDLabel(
            text=f"{initial_value}/10",
            font_style="Subtitle2", bold=True,
            size_hint_x=None, width=dp(52),
            halign="right",
        )
        header.add_widget(MDLabel(
            text=field_def["label"],
            font_style="Subtitle2", bold=True,
        ))
        header.add_widget(self.value_label)
        self.add_widget(header)

        # Description
        self.add_widget(MDLabel(
            text=field_def["desc"],
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None, height=dp(20),
        ))

        # Slider row
        slider_row = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None, height=dp(40),
        )
        slider_row.add_widget(MDLabel(
            text=field_def["low_label"],
            font_style="Caption",
            size_hint_x=None, width=dp(72),
            halign="center",
        ))
        self.slider = MDSlider(
            min=1, max=10, value=initial_value, step=1,
            hint=True, hint_bg_color=(0.11, 0.46, 0.70, 1),
        )
        self.slider.bind(value=self._on_value_change)
        slider_row.add_widget(self.slider)
        slider_row.add_widget(MDLabel(
            text=field_def["high_label"],
            font_style="Caption",
            size_hint_x=None, width=dp(72),
            halign="center",
        ))
        self.add_widget(slider_row)

    def _on_value_change(self, instance, value):
        v = int(value)
        emoji = get_mood_emoji(v) if self.field_def["key"] == "mood_score" else ""
        self.value_label.text = f"{emoji} {v}/10"

    @property
    def value(self) -> int:
        return int(self.slider.value)


class CheckinScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "checkin"
        self.slider_rows = {}
        self._sleep_field = None
        self._notes_field = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", spacing=0)

        # App bar
        from kivymd.uix.toolbar import MDTopAppBar
        toolbar = MDTopAppBar(
            title="Daily Check-in",
            md_bg_color=(0.11, 0.46, 0.70, 1),
            specific_text_color=(1, 1, 1, 1),
            left_action_items=[["arrow-left", lambda x: self._go_back()]],
            elevation=4,
        )
        root.add_widget(toolbar)

        # Scrollable form
        scroll = MDScrollView()
        self.form = MDBoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(16), dp(16), dp(16), dp(80)],
            size_hint_y=None,
        )
        self.form.bind(minimum_height=self.form.setter("height"))
        scroll.add_widget(self.form)
        root.add_widget(scroll)
        self.add_widget(root)

    def on_enter(self):
        self.form.clear_widgets()
        self.slider_rows = {}
        self._build_form()

    def _build_form(self):
        existing = db.get_checkin_today()

        # Date header
        self.form.add_widget(MDLabel(
            text=f"Check-in for {date.today().strftime('%A, %B %d')}",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(36),
        ))

        if existing:
            self.form.add_widget(MDLabel(
                text="You already checked in today. You can update your entries below.",
                font_style="Body2",
                theme_text_color="Secondary",
                size_hint_y=None, height=dp(28),
            ))

        # Slider fields
        for field in CHECKIN_FIELDS:
            initial = existing.get(field["key"], 5) if existing else 5
            row = SliderRow(field_def=field, initial_value=initial)
            self.slider_rows[field["key"]] = row

            card = MDCard(
                orientation="vertical",
                padding=[dp(12), dp(8)],
                size_hint_y=None, height=dp(116),
                elevation=1, radius=[dp(10)],
            )
            card.add_widget(row)
            self.form.add_widget(card)

        # Sleep hours input
        sleep_card = MDCard(
            orientation="vertical",
            padding=dp(12), spacing=dp(8),
            size_hint_y=None, height=dp(96),
            elevation=1, radius=[dp(10)],
        )
        sleep_card.add_widget(MDLabel(
            text="Hours Slept Last Night",
            font_style="Subtitle2", bold=True,
            size_hint_y=None, height=dp(24),
        ))
        self._sleep_field = MDTextField(
            hint_text="e.g. 7.5",
            helper_text="Enter hours slept (e.g. 7 or 6.5)",
            helper_text_mode="on_focus",
            input_filter="float",
            size_hint_y=None, height=dp(48),
        )
        if existing and existing.get("sleep_hours"):
            self._sleep_field.text = str(existing["sleep_hours"])
        sleep_card.add_widget(self._sleep_field)
        self.form.add_widget(sleep_card)

        # Notes
        notes_card = MDCard(
            orientation="vertical",
            padding=dp(12), spacing=dp(8),
            size_hint_y=None, height=dp(120),
            elevation=1, radius=[dp(10)],
        )
        notes_card.add_widget(MDLabel(
            text="Notes (optional)",
            font_style="Subtitle2", bold=True,
            size_hint_y=None, height=dp(24),
        ))
        self._notes_field = MDTextField(
            hint_text="How was your day? Any notable events?",
            multiline=True,
            size_hint_y=None, height=dp(72),
        )
        if existing and existing.get("notes"):
            self._notes_field.text = existing["notes"]
        notes_card.add_widget(self._notes_field)
        self.form.add_widget(notes_card)

        # Submit button
        btn_row = MDBoxLayout(
            orientation="horizontal", spacing=dp(8),
            size_hint_y=None, height=dp(48),
        )
        btn_row.add_widget(MDFlatButton(
            text="Cancel",
            on_release=lambda x: self._go_back(),
        ))
        btn_row.add_widget(MDRaisedButton(
            text="Save Check-in",
            md_bg_color=(0.11, 0.46, 0.70, 1),
            on_release=lambda x: self._save_checkin(),
        ))
        self.form.add_widget(btn_row)

    def _save_checkin(self):
        sleep_text = self._sleep_field.text.strip()
        sleep_hours = float(sleep_text) if sleep_text else None

        data = {
            "checkin_date": str(date.today()),
            "mood_score": self.slider_rows["mood_score"].value,
            "anxiety_level": self.slider_rows["anxiety_level"].value,
            "stress_level": self.slider_rows["stress_level"].value,
            "sleep_hours": sleep_hours,
            "sleep_quality": self.slider_rows["sleep_quality"].value,
            "energy_level": self.slider_rows["energy_level"].value,
            "social_interaction": self.slider_rows["social_interaction"].value,
            "notes": self._notes_field.text.strip(),
        }

        db.save_checkin(data)
        self._show_success()

    def _show_success(self):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton as Btn

        mood = self.slider_rows["mood_score"].value
        emoji = get_mood_emoji(mood)
        label = MOOD_LABELS.get(mood, "")

        dialog = MDDialog(
            title="Check-in Saved!",
            text=f"Your mood: {emoji} {label} ({mood}/10)\n\nKeep tracking daily for best insights.",
            buttons=[
                Btn(text="View Dashboard", on_release=lambda x: self._close_and_go(dialog, "home")),
                Btn(text="Done", on_release=lambda x: dialog.dismiss()),
            ],
        )
        dialog.open()

    def _close_and_go(self, dialog, screen):
        dialog.dismiss()
        self.manager.current = screen

    def _go_back(self):
        self.manager.current = "home"
