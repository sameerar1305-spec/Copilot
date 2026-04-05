# Quick Reference — Meeting Sentiment Analysis

---

## Getting Started in 60 Seconds

```
1. Open meeting-sentiment-analysis.html in your browser
2. Paste your meeting transcript
3. Click "Analyze Sentiment"
4. Read your results
```

---

## Understanding Your Results

### Overall Sentiment

| Badge | Meaning | What to do |
|-------|---------|-----------|
| **Positive** | Team is engaged, optimistic, and aligned | Maintain momentum; document wins |
| **Neutral** | Professional but emotionally flat | Introduce more collaborative elements |
| **Mixed** | Both enthusiasm and concerns present | Address concerns before they escalate |
| **Negative** | Tension, frustration, or disengagement present | Immediate follow-up required |

### Sentiment Score Bars

```
Positive ████████████░░░░░░  65%   ← Good! High positive ratio
Neutral  ████░░░░░░░░░░░░░░  20%
Negative ████░░░░░░░░░░░░░░  15%   ← Low negative = healthy
```

- **Positive > 55%** → Team is in a good place
- **Negative > 35%** → Schedule a follow-up to address issues
- **Neutral > 60%** → Meeting may have lacked energy or engagement

---

### Metrics Explained

| Metric | High | Medium | Low |
|--------|------|--------|-----|
| **Engagement** | Lots of questions, ideas, suggestions | Some participation | Mostly passive listening |
| **Decision Satisfaction** | Clear agreement and buy-in | Partial agreement | Unresolved decisions |
| **Conflict Level** | Active disagreement | Some tension | Harmonious discussion |

**Conflict Level** is color-coded in reverse: Low conflict = green (good), High conflict = red (needs attention).

---

## Transcript Tips

### Best format for detailed results

```
Name: Their comment here.
Name: Another comment.
```

Example:
```
Alice: I'm excited about the roadmap!
Bob: I'm a bit worried about the timeline.
Carol: Let's create a risk register to address concerns.
```

### Works with any format too

Plain text without speaker labels is fine — you won't get per-participant stats but overall sentiment still works.

---

## Using Claude AI vs Keyword Analysis

| | Keyword | Claude AI |
|-|---------|-----------|
| Speed | Instant | ~2–5 seconds |
| Accuracy | Good for clear language | Excellent, handles nuance |
| Sarcasm | Often missed | Usually detected |
| Requires API key | No | Yes |
| Cost | Free | Claude API credits |
| Works offline | Yes | No |

**Recommendation**: Use keyword for quick checks; use Claude AI for important meetings.

---

## Common Examples

### After a sprint retrospective

1. Paste the retrospective notes/transcript.
2. Check **Conflict Level** — if Medium/High, add a team health discussion to the next retro.
3. Check **Engagement** — Low engagement suggests a format change is needed.

### After a difficult stakeholder meeting

1. Analyze the transcript immediately after.
2. If **Negative** overall, review the recommendations.
3. Send a follow-up email to stakeholders addressing top concerns.

### Weekly team pulse

1. Ask everyone to record their standup.
2. Combine the transcripts into one file.
3. Run weekly analysis and compare trends in history.

---

## Keyboard & UI Shortcuts

| Action | How |
|--------|-----|
| Load sample data | Click **Load Sample** button |
| Clear the form | Click **Clear** button |
| Export results | Click **Export JSON** (appears after analysis) |
| Reload past analysis | Click any item in the History panel |
| Clear all history | Click **Clear History** → confirm |

---

## Troubleshooting Flowchart

```
Problem: No results after clicking Analyze
    │
    ├─→ Is the transcript box empty?
    │       Yes → Paste your transcript first
    │
    └─→ Is there a red error message?
            Yes → Check API key (if using Claude)
                  or refresh the page

Problem: Participant breakdown is empty
    │
    └─→ Does your transcript have "Name: text" format?
            No → Add speaker labels for participant stats

Problem: History not saving
    │
    └─→ Is localStorage blocked in your browser?
            Try: Settings → Privacy → Allow site data

Problem: API error / fallback used
    │
    ├─→ Check API key starts with sk-ant-
    ├─→ Check your Anthropic account has credits
    └─→ Keyword fallback will still run automatically
```

---

## Recommended Actions by Sentiment

### Positive meeting
- Share the sentiment report with the team to reinforce culture.
- Document decisions and celebrate progress.
- Capture energy by assigning action items immediately.

### Neutral meeting
- Consider shortening future meetings or changing format.
- Add a brief "check-in" at the start to raise energy.
- Ensure clear outcomes are defined before ending.

### Mixed meeting
- Identify the specific concerns mentioned and assign owners.
- Schedule a brief 15-min follow-up to resolve open items.
- Acknowledge the positives publicly before addressing negatives.

### Negative meeting
- Do not ignore — send a follow-up within 24 hours.
- 1:1 check-ins with participants who seemed most frustrated.
- Consider a team retrospective focused on process improvement.
- Remove blockers mentioned during the meeting.

---

## Privacy & Security

- Transcripts are processed **in your browser** (keyword mode).
- When Claude API mode is used, transcript is sent to **Anthropic's API** — review their privacy policy.
- History is stored in **your browser only** (`localStorage`) — not synced or uploaded anywhere.
- **Never** paste confidential or personally identifiable information into a shared/public browser.
- API keys are held only in memory and lost when you close the tab.

---

## Getting Help

- **Full documentation**: [MEETING_SENTIMENT_README.md](MEETING_SENTIMENT_README.md)
- **Setup guide**: [COPILOT_STUDIO_SETUP.md](COPILOT_STUDIO_SETUP.md)
- **Implementation steps**: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- **GitHub issues**: `sameerar1305-spec/Copilot`

---

*Meeting Sentiment Analysis — Copilot Tools Suite*
