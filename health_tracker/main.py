"""
MindGuard - Mental Health & Medical Ailment Tracker
A Python mobile application built with Kivy + KivyMD that tracks:
  - Phone usage patterns (screen time, app categories)
  - Mental health daily check-ins (mood, stress, anxiety, sleep)
  - Physical/medical ailments linked to device use
  - Digital wellness scores and trends
  - Smart alerts and health recommendations

Run: python health_tracker/main.py
"""

import os

# Must be set before importing Kivy
os.environ["KIVY_NO_ENV_CONFIG"] = "1"

from kivy.config import Config
Config.set("graphics", "width", "390")
Config.set("graphics", "height", "844")
Config.set("graphics", "resizable", "0")

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.navigationdrawer import (
    MDNavigationDrawer, MDNavigationDrawerItem,
    MDNavigationDrawerMenu, MDNavigationDrawerHeader,
)
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.label import MDLabel

from health_tracker import database as db
from health_tracker.screens.home_screen import HomeScreen
from health_tracker.screens.checkin_screen import CheckinScreen
from health_tracker.screens.usage_screen import UsageScreen
from health_tracker.screens.history_screen import HistoryScreen
from health_tracker.screens.profile_screen import ProfileScreen


class MindGuardApp(MDApp):
    """
    Main Kivy application class for MindGuard.
    Configures the theme, screen manager, and bottom navigation.
    """

    def build(self):
        self.title = "MindGuard"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_hue = "700"

        # Initialize DB
        db.init_db()
        db.get_or_create_user()

        return self._build_layout()

    def _build_layout(self):
        """
        Layout structure:
          MDBoxLayout (vertical)
          ├── MDScreenManager  (main content area, flex)
          └── MDBottomNavigation (tab bar, fixed height)
        """
        root = MDBoxLayout(orientation="vertical")

        # ── Screen Manager ─────────────────────────────────────────────────
        self.sm = MDScreenManager()
        self.sm.add_widget(HomeScreen())
        self.sm.add_widget(CheckinScreen())
        self.sm.add_widget(UsageScreen())
        self.sm.add_widget(HistoryScreen())
        self.sm.add_widget(ProfileScreen())
        root.add_widget(self.sm)

        # ── Bottom Navigation ──────────────────────────────────────────────
        bottom_nav = self._build_bottom_nav()
        root.add_widget(bottom_nav)

        return root

    def _build_bottom_nav(self):
        """Build the bottom tab navigation bar."""
        nav_box = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60),
            md_bg_color=(0.11, 0.46, 0.70, 1),
        )

        nav_items = [
            ("home", "Home", "home"),
            ("checkin", "Check-in", "emoticon-happy-outline"),
            ("usage", "Usage", "cellphone"),
            ("history", "History", "chart-line"),
            ("profile", "Profile", "account"),
        ]

        for screen_name, label, icon in nav_items:
            btn = self._make_nav_button(screen_name, label, icon)
            nav_box.add_widget(btn)

        return nav_box

    def _make_nav_button(self, screen_name: str, label: str, icon: str):
        from kivymd.uix.button import MDIconButton
        from kivy.uix.boxlayout import BoxLayout

        box = BoxLayout(orientation="vertical")

        icon_btn = MDIconButton(
            icon=icon,
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 0.85),
            on_release=lambda x, sn=screen_name: self._switch_screen(sn),
        )
        lbl = MDLabel(
            text=label,
            font_style="Caption",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 0.85),
            halign="center",
            size_hint_y=None,
            height=dp(16),
        )
        box.add_widget(icon_btn)
        box.add_widget(lbl)
        return box

    def _switch_screen(self, screen_name: str):
        self.sm.current = screen_name

    def on_start(self):
        """Run startup tasks after app is fully initialized."""
        Clock.schedule_interval(self._check_daily_reminder, 3600)  # every hour

    def _check_daily_reminder(self, *args):
        """Check if user needs a reminder to log their daily check-in."""
        from datetime import datetime
        hour = datetime.now().hour
        if hour == 21:  # 9 PM reminder
            checkin = db.get_checkin_today()
            if not checkin:
                db.save_alert(
                    alert_type="recommendation",
                    category="mental_health",
                    message="Reminder: You haven't completed today's mental health check-in yet!"
                )


def main():
    MindGuardApp().run()


if __name__ == "__main__":
    main()
