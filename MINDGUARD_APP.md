# MindGuard — Mental Health & Medical Ailment Tracker

A Python mobile application that correlates **smartphone usage patterns** with
**mental health** and **physical well-being**, helping users build healthier
digital habits.

---

## Features

### Dashboard (Home Screen)
- **Digital Wellness Score** (0–100) — composite score from mood, stress, sleep & screen time
- At-a-glance stats: screen time, mood, pickups, sleep, stress, anxiety
- Smart health alerts (warning / critical)
- Personalized recommendations

### Daily Mental Health Check-in
- **Mood** (1–10) with emoji feedback
- **Anxiety level** (1–10)
- **Stress level** (1–10)
- **Sleep hours** + **sleep quality**
- **Energy level** & **social interaction**
- Free-text notes

### Phone Usage Tracker
- Log sessions by category:
  - Social Media, Gaming, Work/Productivity, Entertainment, Other
- Today's breakdown with per-category progress bars
- Running totals and session count

### Medical Ailment Log
- Log symptoms linked to phone use:
  - Headache, Eye Strain, Neck/Shoulder Pain, Back Pain
  - Sleep Difficulty, Fatigue, Anxiety Episode, Low Mood Episode
  - Wrist/Thumb Pain, Dizziness
- Severity scale (1–10)
- Trigger attribution
- Recent symptom history

### Health History & Trends
- 7/14/30-day trend views
- Mood, stress, anxiety, sleep trends (progress-bar charts)
- Screen time daily breakdown
- App category averages
- Symptom frequency analysis
- Period summary statistics

### Profile & Settings
- User profile (name, age, gender)
- Wellness score + streak
- Toggle: reminders, screen time warnings, sleep alerts, weekly report
- **WHO / evidence-based health guidelines**
- Digital wellness tips (20-20-20 rule, nomophobia, sleep hygiene, etc.)

---

## Health Intelligence Engine (`utils/analyzer.py`)

The analyzer correlates data across three domains:

| Trigger | Risk Generated |
|---|---|
| Screen time > 4h | Usage warning |
| Screen time > 6h | Critical alert |
| Social media > 2h | Mental health warning |
| Mood score ≤ 4 | Mental health warning |
| Anxiety ≥ 7 | Mental health warning |
| Stress ≥ 7 | Critical alert |
| Sleep < 6h | Physical warning |
| Severe ailment (sev ≥ 7) | Critical alert |

**Wellness Score Formula:**
```
score = mood(25%) + low_anxiety(20%) + low_stress(20%) + sleep(20%) + low_usage(15%)
```

---

## Project Structure

```
health_tracker/
├── main.py                  # App entry point (Kivy MDApp)
├── database.py              # SQLite database manager
├── screens/
│   ├── home_screen.py       # Dashboard
│   ├── checkin_screen.py    # Daily mental health check-in
│   ├── usage_screen.py      # Phone usage + ailment logging
│   ├── history_screen.py    # Trends & history
│   └── profile_screen.py   # Profile, settings, tips
└── utils/
    └── analyzer.py          # Health analysis & alert engine
run_app.py                   # Root launcher
requirements.txt             # Python dependencies
```

---

## Installation & Running

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App (Desktop simulation)
```bash
python run_app.py
```

The app window simulates a 390×844 px phone screen (iPhone 14 Pro size).

### 3. Build for Android (Buildozer)
```bash
pip install buildozer
buildozer android debug
```

---

## Tech Stack

| Component | Technology |
|---|---|
| UI Framework | [Kivy](https://kivy.org) 2.3 + [KivyMD](https://kivymd.readthedocs.io) 1.2 |
| Database | SQLite 3 (via Python `sqlite3` stdlib) |
| Notifications | [Plyer](https://plyer.readthedocs.io) |
| Analysis | Pure Python |
| Target Platforms | Android, iOS, Linux, macOS, Windows |

---

## Data Privacy

- All data is stored **locally on device** (SQLite in `~/.health_tracker/`)
- No data is sent to any server
- No user accounts required
- Data can be deleted by removing the DB file

---

## Medical Disclaimer

This application is for **informational and self-monitoring purposes only**.
It is **not a substitute for professional medical advice, diagnosis, or treatment**.
Always consult a qualified healthcare provider for medical concerns.
