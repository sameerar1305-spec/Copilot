# Meeting Sentiment Analysis

A browser-based tool for analyzing the emotional tone, team dynamics, and engagement levels of Microsoft Teams meeting transcripts — with optional Claude AI integration and local history tracking.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [API Reference](#api-reference)
6. [Analysis Methodology](#analysis-methodology)
7. [Data Storage](#data-storage)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)

---

## Overview

Meeting Sentiment Analysis provides teams with actionable insights into meeting quality and team morale. It works entirely in the browser with no server required for the core experience. Optionally, you can connect it to the Anthropic Claude API for deeper AI-powered analysis.

### Architecture

```
┌─────────────────────┐      ┌──────────────────────┐
│  Teams Meeting      │──→───│  Copilot Studio Agent │
│  (transcript)       │      │  (capture & forward)  │
└─────────────────────┘      └──────────┬───────────┘
                                         │
                              ┌──────────▼───────────┐
                              │  meeting-sentiment-  │
                              │  analysis.html       │
                              │  (browser app)       │
                              └──────────┬───────────┘
                                         │
                     ┌───────────────────┼──────────────────┐
                     ▼                   ▼                  ▼
              ┌────────────┐    ┌──────────────┐   ┌───────────────┐
              │ Claude API │    │ Keyword      │   │  localStorage │
              │ (optional) │    │ Fallback     │   │  (history)    │
              └────────────┘    └──────────────┘   └───────────────┘
```

---

## Features

### Sentiment Analysis
- **Multi-level classification**: Positive / Neutral / Negative / Mixed
- **Score breakdown**: Percentage scores for each sentiment category
- **Confidence**: Claude API provides higher accuracy; keyword fallback always available offline

### Team Dynamics Metrics
| Metric | Description |
|--------|-------------|
| Engagement | How actively participants contributed (High / Medium / Low) |
| Emotional Tone | Descriptive tone label (e.g. Enthusiastic, Cautious, Tense) |
| Decision Satisfaction | Team's apparent satisfaction with meeting outcomes |
| Conflict Level | Detected tension or disagreement level |

### Participant Insights
- Per-speaker line count
- Individual sentiment classification per participant
- Contribution balance detection

### Recommendations
- 2–5 actionable recommendations generated per analysis
- Tailored to the specific sentiment pattern detected
- Cover follow-up actions, process improvements, and morale boosts

### History & Trends
- Up to 50 analyses stored in browser `localStorage`
- Click any history item to reload the full analysis
- Export individual results as JSON
- Clear history with one click

---

## Installation

### Browser-only (no backend)

No installation required. Simply open `meeting-sentiment-analysis.html` in any modern browser.

```bash
# Clone the repository
git clone https://github.com/sameerar1305-spec/Copilot.git
cd Copilot

# Open directly
open meeting-sentiment-analysis.html
# or
start meeting-sentiment-analysis.html  # Windows
```

### Self-hosted web server

```bash
# Python (recommended for local testing)
python3 -m http.server 8080
# Navigate to http://localhost:8080/meeting-sentiment-analysis.html

# Node.js
npx serve .
# Navigate to http://localhost:3000/meeting-sentiment-analysis.html
```

### Deploy to GitHub Pages

1. Push the repository to GitHub.
2. Settings → Pages → Source: `main` branch, `/ (root)`.
3. Access at `https://{username}.github.io/{repo}/meeting-sentiment-analysis.html`.

---

## Usage

### Manual Analysis (Web UI)

1. Open `meeting-sentiment-analysis.html` in your browser.
2. Enter the **meeting name** and **date** (optional but recommended for history).
3. Paste the meeting **transcript** into the text area.
4. Click **Analyze Sentiment**.
5. View results: sentiment scores, metrics, participant breakdown, and recommendations.

### With Claude API

1. Click **Configure Claude API Key**.
2. Enter your `sk-ant-...` API key.
3. The key is stored only in memory for the current browser session.
4. Click **Analyze Sentiment** — Claude will perform deep natural language analysis.

### Transcript Format

The tool works with any plain-text transcript. Speaker-labeled format yields participant insights:

```
Alice: I'm really excited about the new feature roadmap!
Bob: I agree, though I'm a bit concerned about the timeline.
Carol: We should discuss the risks more carefully before committing.
```

Unlabeled text is also accepted but won't produce per-participant metrics.

### Programmatic Usage (JavaScript)

You can import the analysis functions into your own scripts:

```javascript
// Keyword-based analysis (no API key required)
const result = keywordAnalysis(transcriptText);
console.log(result.overall);         // "Positive"
console.log(result.scores.positive); // 68
console.log(result.recommendations); // ["..."]

// Claude API analysis
const result = await claudeAnalysis(transcriptText, apiKey);
console.log(result.overall); // "Mixed"
```

---

## API Reference

### `keywordAnalysis(transcript: string): AnalysisResult`

Performs rule-based sentiment analysis using curated word lists.

**Parameters**
- `transcript` — Plain text meeting transcript

**Returns** `AnalysisResult`

---

### `claudeAnalysis(transcript: string, apiKey: string): Promise<AnalysisResult>`

Calls the Anthropic Claude API for AI-powered analysis.

**Parameters**
- `transcript` — Plain text meeting transcript
- `apiKey` — Anthropic API key (`sk-ant-...`)

**Returns** `Promise<AnalysisResult>`

**Throws** on API error (falls back to keyword analysis in UI)

---

### Type: `AnalysisResult`

```typescript
interface AnalysisResult {
  overall: "Positive" | "Neutral" | "Negative" | "Mixed";
  scores: {
    positive: number;  // 0–100
    neutral:  number;  // 0–100
    negative: number;  // 0–100
                       // must sum to 100
  };
  metrics: {
    engagement:           "High" | "Medium" | "Low";
    tone:                 string;   // e.g. "Enthusiastic"
    decisionSatisfaction: "High" | "Medium" | "Low";
    conflictLevel:        "High" | "Medium" | "Low";
  };
  participants: Array<{
    name:      string;
    lines:     number;
    sentiment: "Positive" | "Neutral" | "Negative";
  }>;
  recommendations: string[];  // 2–5 items
  method: "claude" | "keyword";
}
```

---

### History Entry (localStorage)

```typescript
interface HistoryEntry extends AnalysisResult {
  meetingName: string;
  date:        string;   // YYYY-MM-DD
  transcript:  string;
  savedAt:     string;   // ISO 8601
}
```

---

## Analysis Methodology

### Keyword Analysis

The fallback engine uses two curated word lists:

**Positive indicators** (50+ terms): great, excellent, excited, agree, success, resolve, thank, milestone, collaborative, …

**Negative indicators** (50+ terms): concern, frustrated, delayed, blocked, conflict, uncertain, blame, burnout, …

**Engagement indicators**: question, suggest, propose, idea, action item, follow up, we should, …

Scoring algorithm:
1. Count occurrences of each category across the full transcript.
2. Compute ratio: `positive / (positive + negative + 1)`.
3. Normalise to 0–100% with remainder assigned to neutral.
4. Derive `overall` from thresholds: positive >55% → Positive; negative >40% → Negative; etc.

### Claude AI Analysis

When an API key is provided, the transcript is sent to `claude-sonnet-4-6` with a structured prompt requesting:
- Overall sentiment classification
- Percentage score breakdown
- Engagement, tone, decision satisfaction, conflict level
- Per-participant classification
- 2–5 specific recommendations

Claude's natural language understanding captures nuance that keyword matching misses (sarcasm, implicit dissatisfaction, contextual positivity, etc.).

---

## Data Storage

All data is stored exclusively in **browser `localStorage`** under the key `msa_history_v1`.

- Maximum 50 history entries (oldest are dropped).
- Transcripts are stored verbatim — do not paste sensitive/confidential content in shared browsers.
- No data is ever sent to any server except when you explicitly provide a Claude API key.
- Clear history via the **Clear History** button or `localStorage.removeItem('msa_history_v1')`.

---

## Configuration

### Environment variables (Apps Script backend)

If deploying the Google Apps Script backend, set the following in Script Properties:

| Property | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key for server-side analysis |
| `SHEET_ID` | Google Sheets ID for persistent history |
| `TEAMS_WEBHOOK_URL` | Incoming webhook for Teams notifications |

### Customising word lists

Edit the arrays in `meeting-sentiment-analysis.html`:

```javascript
const POSITIVE_WORDS = [ /* add your domain-specific terms */ ];
const NEGATIVE_WORDS = [ /* add your domain-specific terms */ ];
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Analysis failed" error | Invalid API key | Check key starts with `sk-ant-` |
| No participant breakdown | Transcript not labeled | Ensure format is `Name: text` |
| All scores show 0% | Empty transcript | Paste content before clicking Analyze |
| History not saving | localStorage blocked | Allow storage in browser settings |
| CORS error with API | Direct browser call blocked | Use server-side proxy or confirm `anthropic-dangerous-direct-browser-calls` header is accepted |
| Scores don't sum to 100 | Claude returned invalid JSON | Retry; fallback will be used automatically |

### Browser compatibility

| Browser | Supported |
|---------|-----------|
| Chrome 90+ | ✓ |
| Firefox 88+ | ✓ |
| Safari 14+ | ✓ |
| Edge 90+ | ✓ |
| IE 11 | ✗ |

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-improvement`.
3. Make changes to `meeting-sentiment-analysis.html`.
4. Test in multiple browsers.
5. Submit a pull request with a clear description.

### Code style

- Vanilla JavaScript only (no build step required).
- CSS variables for theming.
- All UI strings in English; i18n-ready attribute patterns preferred.

---

*See also: [COPILOT_STUDIO_SETUP.md](COPILOT_STUDIO_SETUP.md) | [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) | [QUICK_REFERENCE.md](QUICK_REFERENCE.md)*
