"""
Phone Usage & Medical Ailment Tracker Screen
Users log phone usage sessions by category and track physical/medical
symptoms that may be linked to excessive screen time.
"""

from datetime import date
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField
from kivymd.uix.slider import MDSlider
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.chip import MDChip
from kivy.metrics import dp
from kivy.clock import Clock

from health_tracker import database as db
from health_tracker.utils.analyzer import (
    format_duration, APP_CATEGORY_LABELS, AILMENT_LABELS
)


APP_CATEGORIES = [
    ("social_media", "Social Media", "#E91E63"),
    ("gaming", "Gaming", "#9C27B0"),
    ("work", "Work / Productivity", "#2196F3"),
    ("entertainment", "Entertainment", "#FF9800"),
    ("other", "Other", "#607D8B"),
]

AILMENT_TYPES = [
    ("headache", "Headache"),
    ("eye_strain", "Eye Strain"),
    ("neck_pain", "Neck / Shoulder Pain"),
    ("back_pain", "Back Pain"),
    ("insomnia", "Sleep Difficulty"),
    ("fatigue", "Fatigue"),
    ("anxiety_attack", "Anxiety Episode"),
    ("depression_episode", "Low Mood Episode"),
    ("wrist_pain", "Wrist / Thumb Pain"),
    ("dizziness", "Dizziness"),
    ("other", "Other"),
]

PHONE_USE_TRIGGERS = [
    "After heavy social media use",
    "After prolonged gaming",
    "Late night phone use",
    "Excessive notifications",
    "After video streaming",
    "Work-related phone stress",
    "Unknown",
]


class UsageScreen(MDScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "usage"
        self._selected_category = None
        self._duration_field = None
        self._selected_ailment = None
        self._severity_slider = None
        self._ailment_duration_field = None
        self._trigger_selected = None
        self._ailment_notes_field = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation="vertical", spacing=0)

        from kivymd.uix.toolbar import MDTopAppBar
        toolbar = MDTopAppBar(
            title="Usage & Symptoms",
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
        self._build_usage_section()
        self._build_today_summary()
        self._build_ailment_section()

    # ──────────────────────────────────────────────────────────────────────────
    # Phone Usage Logging Section
    # ──────────────────────────────────────────────────────────────────────────

    def _build_usage_section(self):
        self.content.add_widget(MDLabel(
            text="Log Phone Usage Session",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(32),
        ))

        card = MDCard(
            orientation="vertical",
            padding=dp(16), spacing=dp(12),
            size_hint_y=None, height=dp(280),
            elevation=3, radius=[dp(12)],
        )

        # Category selection
        card.add_widget(MDLabel(
            text="Select App Category",
            font_style="Subtitle2", bold=True,
            size_hint_y=None, height=dp(24),
        ))

        self._category_buttons = {}
        cat_grid = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            size_hint_y=None, height=dp(36),
        )
        for key, label, color in APP_CATEGORIES:
            btn = MDFlatButton(
                text=label,
                size_hint_x=None,
            )
            btn.bind(on_release=lambda x, k=key: self._select_category(k))
            self._category_buttons[key] = btn
            cat_grid.add_widget(btn)
        card.add_widget(cat_grid)

        # Category display (second row for overflow)
        cat_grid2 = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(6),
            size_hint_y=None, height=dp(36),
        )
        for key, label, color in APP_CATEGORIES[2:]:
            btn2 = MDFlatButton(
                text=label,
                size_hint_x=None,
            )
            btn2.bind(on_release=lambda x, k=key: self._select_category(k))
            self._category_buttons[key + "_2"] = btn2
            cat_grid2.add_widget(btn2)
        card.add_widget(cat_grid2)

        # Duration input
        card.add_widget(MDLabel(
            text="Duration (minutes)",
            font_style="Subtitle2", bold=True,
            size_hint_y=None, height=dp(24),
        ))
        self._duration_field = MDTextField(
            hint_text="e.g. 45",
            helper_text="How many minutes did you spend?",
            helper_text_mode="on_focus",
            input_filter="int",
            size_hint_y=None, height=dp(48),
        )
        card.add_widget(self._duration_field)

        # Selected category display
        self._cat_display = MDLabel(
            text="No category selected",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None, height=dp(20),
        )
        card.add_widget(self._cat_display)

        # Log button
        card.add_widget(MDRaisedButton(
            text="Log Usage Session",
            md_bg_color=(0.18, 0.65, 0.18, 1),
            size_hint_y=None, height=dp(40),
            on_release=lambda x: self._save_usage(),
        ))

        self.content.add_widget(card)

    def _select_category(self, key: str):
        self._selected_category = key
        label = APP_CATEGORY_LABELS.get(key, key)
        self._cat_display.text = f"Selected: {label}"

    def _save_usage(self):
        if not self._selected_category:
            self._show_snack("Please select a category first.")
            return
        duration_text = self._duration_field.text.strip()
        if not duration_text or not duration_text.isdigit():
            self._show_snack("Please enter a valid duration.")
            return

        db.log_usage_session({
            "usage_date": str(date.today()),
            "app_category": self._selected_category,
            "duration_minutes": int(duration_text),
            "session_start": None,
            "session_end": None,
        })

        self._selected_category = None
        self._duration_field.text = ""
        self._cat_display.text = "No category selected"
        self._show_snack("Usage session logged!")
        Clock.schedule_once(lambda dt: self._refresh_summary(), 0.3)

    def _build_today_summary(self):
        self.content.add_widget(MDLabel(
            text="Today's Usage Breakdown",
            font_style="Subtitle1", bold=True,
            size_hint_y=None, height=dp(28),
        ))

        usage = db.get_usage_summary_today()
        total = usage.get("total_screen_time_minutes", 0)
        pickups = usage.get("pickups_count", 0)

        summary_card = MDCard(
            orientation="vertical",
            padding=dp(12), spacing=dp(8),
            size_hint_y=None, height=dp(220),
            elevation=2, radius=[dp(12)],
        )

        # Total bar
        summary_card.add_widget(MDLabel(
            text=f"Total Screen Time: {format_duration(total)}  |  Sessions: {pickups}",
            font_style="Subtitle2", bold=True,
            size_hint_y=None, height=dp(28),
        ))

        from kivymd.uix.progressbar import MDProgressBar

        categories = [
            ("social_media", "Social Media", "#E91E63"),
            ("gaming", "Gaming", "#9C27B0"),
            ("work", "Work", "#2196F3"),
            ("entertainment", "Entertainment", "#FF9800"),
            ("other", "Other", "#607D8B"),
        ]

        for key, label, color in categories:
            mins = usage.get(f"{key}_minutes", 0)
            if mins == 0:
                continue
            row = MDBoxLayout(
                orientation="horizontal", spacing=dp(8),
                size_hint_y=None, height=dp(28),
            )
            row.add_widget(MDLabel(
                text=label,
                font_style="Caption",
                size_hint_x=None, width=dp(100),
            ))
            pct = min(mins / max(total, 1), 1.0) * 100
            bar = MDProgressBar(value=pct, max=100, size_hint_y=None, height=dp(8))
            row.add_widget(bar)
            row.add_widget(MDLabel(
                text=format_duration(mins),
                font_style="Caption",
                size_hint_x=None, width=dp(48),
                halign="right",
            ))
            summary_card.add_widget(row)

        self._summary_card = summary_card
        self.content.add_widget(summary_card)

    def _refresh_summary(self):
        # Rebuild summary after logging
        try:
            idx = self.content.children.index(self._summary_card)
            self.content.remove_widget(self._summary_card)
            usage = db.get_usage_summary_today()
            total = usage.get("total_screen_time_minutes", 0)
            pickups = usage.get("pickups_count", 0)
            new_card = MDCard(
                orientation="vertical",
                padding=dp(12), spacing=dp(8),
                size_hint_y=None, height=dp(180),
                elevation=2, radius=[dp(12)],
            )
            new_card.add_widget(MDLabel(
                text=f"Total: {format_duration(total)}  |  Sessions: {pickups}",
                font_style="Subtitle2", bold=True,
                size_hint_y=None, height=dp(28),
            ))
            self._summary_card = new_card
            self.content.add_widget(new_card, index=idx)
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    # Medical Ailment Logging Section
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ailment_section(self):
        self.content.add_widget(MDLabel(
            text="Log a Symptom / Medical Ailment",
            font_style="H6", bold=True,
            size_hint_y=None, height=dp(32),
        ))

        card = MDCard(
            orientation="vertical",
            padding=dp(16), spacing=dp(12),
            size_hint_y=None, height=dp(440),
            elevation=3, radius=[dp(12)],
        )

        # Ailment type selection
        card.add_widget(MDLabel(
            text="Select Ailment Type",
            font_style="Subtitle2", bold=True,
            size_hint_y=None, height=dp(24),
        ))

        self._ailment_display = MDLabel(
            text="No ailment selected",
            font_style="Caption",
            theme_text_color="Secondary",
            size_hint_y=None, height=dp(20),
        )

        # Two rows of ailment chips
        ailment_row1 = MDBoxLayout(
            orientation="horizontal", spacing=dp(4),
            size_hint_y=None, height=dp(36),
        )
        ailment_row2 = MDBoxLayout(
            orientation="horizontal", spacing=dp(4),
            size_hint_y=None, height=dp(36),
        )

        ailments_split = [AILMENT_TYPES[:5], AILMENT_TYPES[5:]]
        for row_widget, ailments_group in zip([ailment_row1, ailment_row2], ailments_split):
            for key, label in ailments_group:
                btn = MDFlatButton(
                    text=label[:14] + ("." if len(label) > 14 else ""),
                    size_hint_x=None,
                )
                btn.bind(on_release=lambda x, k=key, l=label: self._select_ailment(k, l))
                row_widget.add_widget(btn)

        card.add_widget(ailment_row1)
        card.add_widget(ailment_row2)
        card.add_widget(self._ailment_display)

        # Severity slider
        card.add_widget(MDLabel(
            text="Severity (1 = Mild, 10 = Severe)",
            font_style="Subtitle2", bold=True,
            size_hint_y=None, height=dp(24),
        ))
        severity_row = MDBoxLayout(
            orientation="horizontal", spacing=dp(8),
            size_hint_y=None, height=dp(40),
        )
        severity_row.add_widget(MDLabel(
            text="Mild", font_style="Caption",
            size_hint_x=None, width=dp(40),
        ))
        self._severity_slider = MDSlider(min=1, max=10, value=5, step=1, hint=True)
        self._severity_value_label = MDLabel(
            text="5/10",
            font_style="Caption",
            size_hint_x=None, width=dp(40),
            halign="right",
        )
        self._severity_slider.bind(
            value=lambda i, v: setattr(self._severity_value_label, "text", f"{int(v)}/10")
        )
        severity_row.add_widget(self._severity_slider)
        severity_row.add_widget(MDLabel(
            text="Severe", font_style="Caption",
            size_hint_x=None, width=dp(48),
        ))
        card.add_widget(severity_row)

        # Duration
        card.add_widget(MDLabel(
            text="Duration (minutes, optional)",
            font_style="Subtitle2", bold=True,
            size_hint_y=None, height=dp(24),
        ))
        self._ailment_duration_field = MDTextField(
            hint_text="How long did it last?",
            input_filter="int",
            size_hint_y=None, height=dp(48),
        )
        card.add_widget(self._ailment_duration_field)

        # Trigger
        card.add_widget(MDLabel(
            text="Possible Trigger",
            font_style="Subtitle2", bold=True,
            size_hint_y=None, height=dp(24),
        ))
        self._trigger_field = MDTextField(
            hint_text="e.g. After 3h social media use",
            size_hint_y=None, height=dp(48),
        )
        card.add_widget(self._trigger_field)

        # Notes
        self._ailment_notes_field = MDTextField(
            hint_text="Additional notes...",
            size_hint_y=None, height=dp(48),
        )
        card.add_widget(self._ailment_notes_field)

        # Save button
        card.add_widget(MDRaisedButton(
            text="Log Symptom",
            md_bg_color=(0.96, 0.26, 0.21, 1),
            size_hint_y=None, height=dp(40),
            on_release=lambda x: self._save_ailment(),
        ))

        self.content.add_widget(card)

        # Recent ailments
        self._build_recent_ailments()

    def _select_ailment(self, key: str, label: str):
        self._selected_ailment = key
        self._ailment_display.text = f"Selected: {label}"

    def _save_ailment(self):
        if not self._selected_ailment:
            self._show_snack("Please select an ailment type.")
            return

        duration_text = self._ailment_duration_field.text.strip()
        db.log_ailment({
            "log_date": str(date.today()),
            "ailment_type": self._selected_ailment,
            "severity": int(self._severity_slider.value),
            "duration_minutes": int(duration_text) if duration_text.isdigit() else None,
            "possible_trigger": self._trigger_field.text.strip(),
            "notes": self._ailment_notes_field.text.strip(),
        })

        self._selected_ailment = None
        self._ailment_display.text = "No ailment selected"
        self._severity_slider.value = 5
        self._ailment_duration_field.text = ""
        self._trigger_field.text = ""
        self._ailment_notes_field.text = ""
        self._show_snack("Symptom logged!")

    def _build_recent_ailments(self):
        ailments = db.get_ailments_last_n_days(3)
        if not ailments:
            return

        self.content.add_widget(MDLabel(
            text="Recent Symptoms",
            font_style="Subtitle1", bold=True,
            size_hint_y=None, height=dp(28),
        ))
        rec_card = MDCard(
            orientation="vertical",
            padding=dp(12), spacing=dp(6),
            size_hint_y=None,
            elevation=1, radius=[dp(10)],
        )
        for a in ailments[:5]:
            label = AILMENT_LABELS.get(a["ailment_type"], a["ailment_type"])
            row = MDBoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(32),
            )
            row.add_widget(MDLabel(
                text=f"{a['log_date']}  {label}",
                font_style="Body2",
            ))
            sev_color = "#F44336" if a["severity"] >= 7 else "#FF9800" if a["severity"] >= 4 else "#4CAF50"
            row.add_widget(MDLabel(
                text=f"Sev: {a['severity']}/10",
                font_style="Caption",
                size_hint_x=None, width=dp(72),
                theme_text_color="Custom",
                text_color=self._hex(sev_color),
            ))
            rec_card.add_widget(row)
        rec_card.height = dp(44 * min(len(ailments), 5) + 24)
        self.content.add_widget(rec_card)

    def _show_snack(self, message: str):
        from kivymd.uix.snackbar import MDSnackbar
        snack = MDSnackbar(text=message, snackbar_x=dp(8), snackbar_y=dp(8))
        snack.size_hint_x = 0.9
        snack.open()

    def _hex(self, hex_color):
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return (r / 255, g / 255, b / 255, 1)

    def _go_back(self):
        self.manager.current = "home"
