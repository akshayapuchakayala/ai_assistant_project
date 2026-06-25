# AI Assistant — Prompt Engineering Project

A Flask web app demonstrating 4 AI-assistant functions, each with **3 differently
designed prompts** (varying length, tone, and structure), plus a feedback loop.

## Functions
1. **Answer Questions** — factual Q&A
2. **Summarize Text** — condense a block of text
3. **Generate Creative Content** — stories, poems, brainstorms
4. **Get Advice** — tips and plans on any topic

Each function offers 3 selectable "prompt styles" (e.g. *Quick Fact* vs.
*Detailed Explainer* vs. *Fun Facts List*) — see `app.py` → `PROMPT_LIBRARY`
for the exact templates.

## Setup

```bash
cd ai_assistant_project
pip install -r requirements.txt
```

### Run in Demo Mode (no API key needed)
```bash
python app.py
```
The app detects there's no `GEMINI_API_KEY` and serves clearly-labeled
demo answers, so every feature (tabs, prompt styles, prompt inspector,
feedback, dashboard) is fully testable out of the box.

### Run with a real AI (free Gemini API key)
1. Go to **https://aistudio.google.com/apikey** and sign in with a Google account.
2. Click **Create API key** — no credit card required.
3. Set it as an environment variable and run:
```bash
export GEMINI_API_KEY=your-key-here      # macOS/Linux
python app.py
```
```powershell
$env:GEMINI_API_KEY="your-key-here"      # Windows PowerShell
python app.py
```
The app uses `gemini-2.5-flash` by default, which is on Google's free tier
(no billing needed). If Google changes free-tier model names later, override
it with `export GEMINI_MODEL=gemini-2.0-flash` (or whatever the current free
Flash model is — check https://ai.google.dev/pricing).

Then open **http://127.0.0.1:5000** in your browser.

## How it works
- Pick a function tab → pick one of its 3 prompt styles → type your input → **Generate**.
- The right-hand panel shows the **exact prompt sent to the model** (the "Prompt Inspector")
  next to the AI's response — useful for understanding how prompt wording shapes output.
- After each response, click 👍/👎 to log feedback. Feedback is stored in
  `logs/feedback_log.json` and summarized live in the dashboard at the bottom
  of the page (helpful % per function) — this is the data you'd use to decide
  which prompt styles need refining.

## Project structure
```
ai_assistant_project/
├── app.py                 # Flask routes, prompt library, AI calling logic, demo fallback
├── requirements.txt
├── templates/index.html   # Page structure
├── static/style.css       # Styling
├── static/script.js       # Tab/style switching, API calls, feedback, dashboard
└── logs/feedback_log.json # Feedback records (auto-created)
```

See the accompanying slide deck for a full user guide and the prompt-design rationale.
