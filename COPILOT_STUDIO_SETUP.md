# Copilot Studio Setup Guide

Complete guide for configuring a Microsoft Copilot agent to capture Teams meeting transcripts and trigger sentiment analysis.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Create the Copilot Agent](#create-the-copilot-agent)
3. [Teams Integration](#teams-integration)
4. [Power Automate Workflow](#power-automate-workflow)
5. [Meeting Attendance Automation](#meeting-attendance-automation)
6. [Webhook Configuration](#webhook-configuration)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- Microsoft 365 Business Standard or higher licence
- Microsoft Copilot Studio access (Power Platform)
- Power Automate Premium (for custom connectors)
- Teams admin rights (or IT support)
- Azure Active Directory access to register apps
- Google Apps Script project (for backend) **or** your own API endpoint

---

## Create the Copilot Agent

### Step 1 — Create a new agent in Copilot Studio

1. Navigate to [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com).
2. Click **Create** → **New agent**.
3. Name: `Meeting Sentiment Bot`.
4. Description: `Captures Teams meeting transcripts and performs sentiment analysis.`
5. Choose **English** as the primary language.

### Step 2 — Add trigger topics

Create a topic called **"Analyze Meeting"**:

```
Trigger phrases:
- analyze this meeting
- sentiment analysis
- how was the meeting
- meeting mood report
- check team sentiment
```

### Step 3 — Build the conversation flow

Add the following nodes to the topic flow:

```
[Message] → "I'll help analyze the meeting sentiment. Please paste the transcript below."

[Question] → "Please share the meeting transcript:"
  Save response to: {transcript}

[Question] → "What is the meeting name? (or type 'skip')"
  Save response to: {meetingName}

[Action] → Call HTTP action (see Webhook Configuration)
  - Method: POST
  - URL: {your_webhook_url}
  - Body: { "transcript": "{transcript}", "meetingName": "{meetingName}" }

[Message] → "Analysis complete! Here is your sentiment report: {actionOutput}"
```

### Step 4 — Publish the agent

1. Click **Publish** in the top-right corner.
2. Select **Microsoft Teams** as the channel.
3. Follow the Teams app configuration wizard.
4. Submit for admin approval if required.

---

## Teams Integration

### Enable meeting transcription

Teams meeting transcription must be enabled by your admin:

1. Teams Admin Center → **Meetings** → **Meeting policies**.
2. Enable **Allow transcription**.
3. Enable **Allow cloud recording** (required for transcript access).

### Add the bot to meetings

**Option A — Manual** (any user):
1. In a Teams meeting, click **+ Add app**.
2. Search for `Meeting Sentiment Bot`.
3. Add to the meeting.

**Option B — Automatic via meeting policy**:
1. Teams Admin Center → **Meetings** → **Meeting settings**.
2. Under **Bots**, enable **Allow bots to join meetings**.
3. Configure your bot's app ID in the policy.

### Configure Graph API permissions

Register an Azure AD app to read meeting transcripts:

1. Azure Portal → **Azure Active Directory** → **App registrations** → **New registration**.
2. Name: `MeetingSentimentApp`.
3. Supported account types: Single tenant.
4. Add the following **Application permissions** (not delegated):
   - `OnlineMeetings.Read.All`
   - `CallRecords.Read.All`
   - `Calls.AccessMedia.All`
   - `User.Read.All`
5. Grant admin consent.
6. Create a client secret and save the value.

---

## Power Automate Workflow

### Workflow: "Post-Meeting Sentiment Analysis"

This workflow triggers after a Teams meeting ends and automatically sends the transcript for analysis.

#### Trigger

```
Connector: Microsoft Teams
Trigger:   "When a meeting recording is available"
```

#### Step 1 — Get meeting details

```
Action: Microsoft Teams → "Get meeting details"
  Meeting ID: triggerBody()?['meetingId']
```

#### Step 2 — Get transcript

```
Action: HTTP
  Method: GET
  URI: https://graph.microsoft.com/v1.0/me/onlineMeetings/{meetingId}/transcripts
  Authentication: Active Directory OAuth
    Tenant: {your_tenant_id}
    Client ID: {azure_app_client_id}
    Client Secret: {azure_app_client_secret}
    Resource: https://graph.microsoft.com
```

#### Step 3 — Parse transcript content

```
Action: HTTP
  Method: GET
  URI: @{body('Get_Transcript')?['value'][0]['transcriptContentUrl']}
  Authentication: (same as above)
```

#### Step 4 — Send for analysis

```
Action: HTTP
  Method: POST
  URI: {your_webhook_url}
  Headers: Content-Type: application/json
  Body:
    {
      "transcript": "@{body('Get_Transcript_Content')}",
      "meetingName": "@{triggerBody()?['subject']}",
      "date": "@{utcNow()}",
      "participants": "@{join(triggerBody()?['participants'], ', ')}"
    }
```

#### Step 5 — Post result to Teams channel

```
Action: Microsoft Teams → "Post message in a chat or channel"
  Team:    {your_team}
  Channel: General
  Message: "Meeting Sentiment Report for @{triggerBody()?['subject']}:
            Overall: @{body('HTTP_Analyze')?['overall']}
            See full report: {your_webapp_url}"
```

### Import the workflow

1. Power Automate → **My flows** → **Import**.
2. Upload the provided `.zip` package (create manually using the steps above).
3. Configure all connection references.
4. Turn on the flow.

---

## Meeting Attendance Automation

### Automatically join meetings as bot

Use the Graph API to programmatically join meetings:

```http
POST https://graph.microsoft.com/v1.0/communications/calls
Content-Type: application/json

{
  "@odata.type": "#microsoft.graph.call",
  "callbackUri": "https://your-bot-endpoint/callback",
  "requestedModalities": ["audio"],
  "meetingInfo": {
    "@odata.type": "#microsoft.graph.organizerMeetingInfo",
    "organizer": {
      "@odata.type": "#microsoft.graph.identitySet",
      "user": {
        "@odata.type": "#microsoft.graph.identity",
        "id": "{organizer_user_id}"
      }
    },
    "allowConversationWithoutHost": true
  }
}
```

### Schedule automatic attendance

Use Power Automate recurrence trigger:

```
Trigger: Recurrence (every 15 minutes)
Action 1: Get calendar events (next 20 minutes)
Action 2: For each event with "Teams" in join URL:
  - Join meeting via Graph API
  - Enable transcription
Action 3: On meeting end:
  - Retrieve transcript
  - Run sentiment analysis
```

---

## Webhook Configuration

### Google Apps Script endpoint

Create a new Google Apps Script project and deploy as a web app:

```javascript
function doPost(e) {
  const data = JSON.parse(e.postData.contents);
  const result = analyzeSentiment(data.transcript);

  // Store result
  const sheet = SpreadsheetApp.openById('YOUR_SHEET_ID').getActiveSheet();
  sheet.appendRow([
    new Date(),
    data.meetingName,
    result.overall,
    result.scores.positive,
    result.scores.neutral,
    result.scores.negative
  ]);

  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}
```

Deploy settings:
- Execute as: **Me**
- Who has access: **Anyone** (or "Anyone within [org]")
- Copy the deployment URL — this is your `{your_webhook_url}`.

### CORS configuration

If calling from a browser directly, add these headers in the Apps Script response:

```javascript
function doPost(e) {
  // ... your logic ...
  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON)
    // Note: Apps Script doesn't support custom CORS headers in doPost.
    // Use a proxy or call from server-side only.
}
```

---

## Testing

### Test the Copilot agent

1. Copilot Studio → your agent → **Test** panel.
2. Type: `analyze this meeting`
3. Paste a sample transcript when prompted.
4. Verify the sentiment result is returned.

### Test the Power Automate flow

1. Power Automate → your flow → **Test** → **Manual**.
2. Provide a sample meeting ID.
3. Check the run history for success/failure.
4. Verify the Teams channel post appears.

### End-to-end test

1. Schedule a test Teams meeting.
2. Enable transcription at the start.
3. Have 2–3 participants speak for a few minutes.
4. End the meeting.
5. Wait 5–10 minutes for the transcript to generate.
6. Verify the Power Automate flow triggers.
7. Check the Teams channel for the sentiment report.

---

## Troubleshooting

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| Bot not responding in Teams | App not approved | Request admin approval in Teams Admin Center |
| Transcript not available | Recording disabled | Enable cloud recording + transcription in meeting policy |
| Graph API 403 error | Missing permissions | Add `OnlineMeetings.Read.All` and grant admin consent |
| Power Automate flow failing | Connection expired | Refresh OAuth connection in flow connections |
| Webhook returning 500 | Apps Script error | Check Apps Script execution log |
| Analysis returns empty | Transcript format issue | Ensure transcript has `Speaker: text` format |

### Useful diagnostic commands

Check if transcription is enabled for a meeting:
```http
GET https://graph.microsoft.com/v1.0/me/onlineMeetings/{meetingId}
```

List available transcripts:
```http
GET https://graph.microsoft.com/v1.0/me/onlineMeetings/{meetingId}/transcripts
```

Retrieve transcript content:
```http
GET https://graph.microsoft.com/v1.0/me/onlineMeetings/{meetingId}/transcripts/{transcriptId}/content?$format=text/vtt
```

---

*For additional support, see [MEETING_SENTIMENT_README.md](MEETING_SENTIMENT_README.md) and [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md).*
