# Implementation Guide

Step-by-step guide to deploy the Meeting Sentiment Analysis system from scratch to production.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Phase 1 — Local Setup](#phase-1--local-setup)
3. [Phase 2 — Claude API Integration](#phase-2--claude-api-integration)
4. [Phase 3 — Google Apps Script Backend](#phase-3--google-apps-script-backend)
5. [Phase 4 — Teams & Copilot Studio](#phase-4--teams--copilot-studio)
6. [Phase 5 — Power Automate Automation](#phase-5--power-automate-automation)
7. [Deployment Checklist](#deployment-checklist)
8. [Integration Scenarios](#integration-scenarios)
9. [Monitoring & Maintenance](#monitoring--maintenance)

---

## System Overview

```
AUTOMATED PIPELINE
──────────────────
Teams Meeting ──→ Auto-Transcript ──→ Power Automate ──→ Apps Script ──→ Analysis
                                                                        ──→ Teams Notification

MANUAL PIPELINE
───────────────
User ──→ meeting-sentiment-analysis.html ──→ Claude API or Keyword ──→ Results + History
```

### Components

| Component | Technology | Role |
|-----------|-----------|------|
| Web UI | HTML5 + Vanilla JS | Manual analysis interface |
| Sentiment Engine | Claude API / Keyword | Core analysis logic |
| History Store | localStorage | Browser-side persistence |
| Backend (optional) | Google Apps Script | Webhook + persistent storage |
| Automation | Power Automate | Auto-trigger on meeting end |
| Agent | Microsoft Copilot Studio | Chat-based interface in Teams |

---

## Phase 1 — Local Setup

**Goal**: Get the web UI running locally.

### Step 1.1 — Clone the repository

```bash
git clone https://github.com/sameerar1305-spec/Copilot.git
cd Copilot
```

### Step 1.2 — Open the web app

No build step required. Open directly:

```bash
# macOS
open meeting-sentiment-analysis.html

# Linux
xdg-open meeting-sentiment-analysis.html

# Windows
start meeting-sentiment-analysis.html
```

Or serve with a local web server (recommended for API calls):

```bash
python3 -m http.server 8080
# Open http://localhost:8080/meeting-sentiment-analysis.html
```

### Step 1.3 — Verify basic functionality

1. Click **Load Sample** to populate a test transcript.
2. Click **Analyze Sentiment**.
3. Confirm results appear: sentiment badge, score bars, metrics, recommendations.
4. Check that the history panel shows the new entry.

**Phase 1 complete** when basic analysis works without API key.

---

## Phase 2 — Claude API Integration

**Goal**: Enable AI-powered analysis with the Anthropic Claude API.

### Step 2.1 — Get an API key

1. Visit [console.anthropic.com](https://console.anthropic.com).
2. Create an account or sign in.
3. Navigate to **API Keys** → **Create Key**.
4. Copy the key (starts with `sk-ant-`).

### Step 2.2 — Configure the key in the UI

1. Open `meeting-sentiment-analysis.html`.
2. Click **Configure Claude API Key**.
3. Paste the key.
4. Click **Analyze Sentiment** — results should now say "✦ Claude AI" in history.

### Step 2.3 — (Optional) Server-side API calls

For production, avoid exposing API keys in the browser. Proxy requests through Apps Script:

```javascript
// In your Google Apps Script
function callClaude(transcript) {
  const apiKey = PropertiesService.getScriptProperties().getProperty('ANTHROPIC_API_KEY');
  const response = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01'
    },
    payload: JSON.stringify({
      model: 'claude-sonnet-4-6',
      max_tokens: 1024,
      messages: [{
        role: 'user',
        content: buildPrompt(transcript)
      }]
    })
  });

  return JSON.parse(response.getContentText());
}
```

**Phase 2 complete** when Claude API analysis returns deeper insights than keyword fallback.

---

## Phase 3 — Google Apps Script Backend

**Goal**: Create a persistent backend that stores all analyses and provides a webhook endpoint.

### Step 3.1 — Create a Google Sheets spreadsheet

1. Go to [sheets.google.com](https://sheets.google.com).
2. Create a new sheet named `MeetingSentimentHistory`.
3. Add headers in row 1:
   ```
   A: Timestamp | B: Meeting Name | C: Date | D: Overall | E: Positive% | F: Neutral% | G: Negative% | H: Engagement | I: Tone | J: Conflict | K: Method
   ```
4. Copy the Spreadsheet ID from the URL (the long string between `/d/` and `/edit`).

### Step 3.2 — Create the Apps Script project

1. Extensions → **Apps Script**.
2. Replace the default `Code.gs` with:

```javascript
const SHEET_ID = 'YOUR_SPREADSHEET_ID'; // replace this

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const result = analyzeTranscript(data);
    storeResult(data, result);
    sendTeamsNotification(data.meetingName, result);

    return ContentService
      .createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function analyzeTranscript(data) {
  const apiKey = PropertiesService.getScriptProperties().getProperty('ANTHROPIC_API_KEY');
  if (apiKey) {
    return callClaude(data.transcript, apiKey);
  }
  return keywordFallback(data.transcript);
}

function storeResult(data, result) {
  const sheet = SpreadsheetApp.openById(SHEET_ID).getActiveSheet();
  sheet.appendRow([
    new Date(),
    data.meetingName || 'Unnamed',
    data.date || '',
    result.overall,
    result.scores.positive,
    result.scores.neutral,
    result.scores.negative,
    result.metrics.engagement,
    result.metrics.tone,
    result.metrics.conflictLevel,
    result.method
  ]);
}

function sendTeamsNotification(meetingName, result) {
  const webhookUrl = PropertiesService.getScriptProperties().getProperty('TEAMS_WEBHOOK_URL');
  if (!webhookUrl) return;

  const emoji = result.overall === 'Positive' ? '✅' :
                result.overall === 'Negative' ? '⚠️' : 'ℹ️';

  UrlFetchApp.fetch(webhookUrl, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({
      text: `${emoji} **Meeting Sentiment Report: ${meetingName}**\n` +
            `Overall: **${result.overall}**\n` +
            `Positive: ${result.scores.positive}% | Neutral: ${result.scores.neutral}% | Negative: ${result.scores.negative}%\n` +
            `Engagement: ${result.metrics.engagement} | Conflict: ${result.metrics.conflictLevel}`
    })
  });
}
```

### Step 3.3 — Set Script Properties

Apps Script → **Project Settings** → **Script Properties**:

| Key | Value |
|-----|-------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `TEAMS_WEBHOOK_URL` | Your Teams incoming webhook URL |

### Step 3.4 — Deploy as web app

1. Deploy → **New deployment**.
2. Type: **Web app**.
3. Execute as: **Me**.
4. Who has access: **Anyone** (or restrict to your org).
5. Click **Deploy** and copy the URL.

**Phase 3 complete** when POSTing to the webhook URL returns a valid analysis JSON.

---

## Phase 4 — Teams & Copilot Studio

**Goal**: Allow team members to trigger sentiment analysis via a Teams chat command.

See [COPILOT_STUDIO_SETUP.md](COPILOT_STUDIO_SETUP.md) for full details.

### Quick steps

1. Create agent in [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com).
2. Add "Analyze Meeting" topic with transcript question.
3. Add HTTP action pointing to your Apps Script webhook.
4. Publish to Microsoft Teams.
5. Test in Teams by typing `analyze this meeting`.

**Phase 4 complete** when the bot responds with a sentiment report in Teams chat.

---

## Phase 5 — Power Automate Automation

**Goal**: Automatically analyze every Teams meeting that has a transcript.

See [COPILOT_STUDIO_SETUP.md](COPILOT_STUDIO_SETUP.md) for full flow configuration.

### Quick steps

1. Power Automate → **Create** → **Automated cloud flow**.
2. Trigger: Teams **"When a meeting recording is available"**.
3. Get transcript via Graph API.
4. POST to your Apps Script webhook.
5. Post result to a Teams channel.
6. Turn on the flow.

**Phase 5 complete** when ending a recorded Teams meeting automatically generates a sentiment report.

---

## Deployment Checklist

### Pre-deployment

- [ ] Web app opens without errors in Chrome, Firefox, Safari
- [ ] Sample data loads and analyzes correctly
- [ ] Keyword fallback works without API key
- [ ] History saves and loads correctly
- [ ] Export JSON produces valid JSON file

### Claude API

- [ ] API key configured and stored securely (not in source code)
- [ ] Claude analysis returns valid JSON matching `AnalysisResult` schema
- [ ] Fallback triggers correctly on API error

### Apps Script Backend (if used)

- [ ] Spreadsheet ID configured in `Code.gs`
- [ ] Script Properties set (`ANTHROPIC_API_KEY`, `TEAMS_WEBHOOK_URL`)
- [ ] Web app deployed with correct permissions
- [ ] Webhook URL tested with curl: `curl -X POST {url} -H "Content-Type: application/json" -d '{"transcript":"Alice: Great meeting!"}'`
- [ ] Google Sheet rows are created on each call

### Teams Integration (if used)

- [ ] Azure AD app registered with correct permissions
- [ ] Admin consent granted
- [ ] Copilot Studio agent published to Teams
- [ ] Bot responds to "analyze this meeting"

### Power Automate (if used)

- [ ] Flow triggers on meeting recording available
- [ ] Graph API authentication working
- [ ] Transcript retrieved successfully
- [ ] Teams notification posted after analysis

### Security

- [ ] API keys NOT committed to source control (check `.gitignore`)
- [ ] Apps Script restricted to org (if required)
- [ ] No sensitive transcripts in sample data

---

## Integration Scenarios

### Scenario A — Small team, manual only

Deploy the HTML file to GitHub Pages. Team members paste transcripts manually after meetings.

**Effort**: 30 minutes | **Cost**: Free

### Scenario B — Medium team, automated notifications

Small team setup + Apps Script backend + Power Automate trigger + Teams channel notification.

**Effort**: 2–4 hours | **Cost**: Power Automate Premium licence

### Scenario C — Enterprise, full automation

All of the above + Copilot Studio agent + Azure AD app + Meeting attendance bot + Google Sheets analytics dashboard.

**Effort**: 1–2 days | **Cost**: Microsoft 365 E3+, Power Platform Premium

### Scenario D — API-only integration

Use the `keywordAnalysis` or `claudeAnalysis` functions programmatically in your own application.

```javascript
// Load script
import { keywordAnalysis, claudeAnalysis } from './meeting-sentiment-analysis.js';
// (or copy the functions into your codebase)

const result = keywordAnalysis(transcript);
console.log(result); // AnalysisResult
```

---

## Monitoring & Maintenance

### Health checks

Run weekly:

1. **Test the web app**: Load sample → Analyze → Confirm results.
2. **Check Apps Script logs**: Apps Script → Executions → Review errors.
3. **Verify Power Automate flow**: Flow detail page → Run history.
4. **Review Google Sheet**: Confirm new rows are appearing.

### Log monitoring

Apps Script logs are available at: Apps Script → **Executions** tab.

Set up email alerts for failures:
```javascript
function onFailure(e) {
  MailApp.sendEmail(
    'admin@yourorg.com',
    'Meeting Sentiment Analysis Failed',
    'Error: ' + e.message
  );
}
```

### Updating the Claude model

To upgrade to a newer Claude model, change the model ID in two places:

1. **Browser (`meeting-sentiment-analysis.html`)** — line with `model: 'claude-sonnet-4-6'`
2. **Apps Script (`Code.gs`)** — equivalent line in `callClaude()`

Available models: `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`

### Word list maintenance

Add domain-specific terms to improve keyword analysis accuracy:

```javascript
// In meeting-sentiment-analysis.html
const POSITIVE_WORDS = [
  // existing words...
  'sprint velocity', 'on track', 'green status', 'stakeholder alignment'
];

const NEGATIVE_WORDS = [
  // existing words...
  'red status', 'escalation', 'scope creep', 'technical debt'
];
```

### Backup & recovery

- localStorage history: Export JSON regularly for backup.
- Apps Script data: Google Sheets auto-saves; download `.xlsx` monthly.
- Configuration: Keep API keys and deployment URLs in a password manager.

---

*See also: [COPILOT_STUDIO_SETUP.md](COPILOT_STUDIO_SETUP.md) | [MEETING_SENTIMENT_README.md](MEETING_SENTIMENT_README.md) | [QUICK_REFERENCE.md](QUICK_REFERENCE.md)*
