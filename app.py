"""
AI Assistant Development — Major Project
=========================================
A small Flask web app that demonstrates prompt engineering by offering
4 distinct AI functions, each with 3 differently-designed prompts
(varying length, tone, and structure), plus a feedback loop that logs
whether each response was helpful.

Run:
    pip install -r requirements.txt
    export GEMINI_API_KEY=...      (optional — get a free key at https://aistudio.google.com/apikey
                                     — app runs in DEMO MODE without it)
    python app.py
Then open http://127.0.0.1:5000
"""

import json
import os
import datetime
from pathlib import Path

from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
FEEDBACK_LOG = BASE_DIR / "logs" / "feedback_log.json"
FEEDBACK_LOG.parent.mkdir(exist_ok=True)
if not FEEDBACK_LOG.exists():
    FEEDBACK_LOG.write_text("[]")

# ---------------------------------------------------------------------------
# 1. Try to set up a real AI client. Uses Google's Gemini API, which has a
#    genuine free tier (no credit card, no trial-credit expiry) — get a key
#    at https://aistudio.google.com/apikey and set it as GEMINI_API_KEY.
#    If no key is present, the app keeps running in DEMO MODE so the
#    assistant is fully testable out of the box.
# ---------------------------------------------------------------------------
client = None
DEMO_MODE = True
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
try:
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key)
        DEMO_MODE = False
except Exception:
    client = None
    DEMO_MODE = True


# ---------------------------------------------------------------------------
# 2. Prompt Library — the core "prompt engineering" deliverable.
#    Each function has 3 prompt variants that differ in length, specificity,
#    tone/style, and complexity, as required by the assignment.
# ---------------------------------------------------------------------------
PROMPT_LIBRARY = {
    "qa": {
        "label": "Answer Questions",
        "tagline": "Factual Q&A",
        "color": "blue",
        "placeholder": "e.g. What is the capital of France?",
        "styles": [
            {
                "id": "concise",
                "name": "Quick Fact",
                "description": "Short, direct answer (1–2 sentences).",
                "template": (
                    "Answer the following question in one or two clear, factual "
                    "sentences. Do not add unnecessary preamble.\n\nQuestion: {input}"
                ),
            },
            {
                "id": "detailed",
                "name": "Detailed Explainer",
                "description": "In-depth answer with background and significance.",
                "template": (
                    "You are a knowledgeable tutor. Provide a thorough, well-organized "
                    "answer to the question below. Include relevant background, context, "
                    "and why it matters. Use 2-4 short paragraphs.\n\nQuestion: {input}"
                ),
            },
            {
                "id": "facts",
                "name": "Fun Facts List",
                "description": "Three engaging facts, friendly tone.",
                "template": (
                    "Answer the question below in a fun, engaging tone by listing exactly "
                    "three interesting facts as a numbered list. Keep each fact to one "
                    "sentence.\n\nQuestion: {input}"
                ),
            },
        ],
    },
    "summarize": {
        "label": "Summarize Text",
        "tagline": "Summarization",
        "color": "teal",
        "placeholder": "Paste the article or block of text you want summarized...",
        "styles": [
            {
                "id": "brief",
                "name": "Brief Overview",
                "description": "2–3 sentence summary.",
                "template": (
                    "Summarize the following text in 2-3 concise sentences, capturing "
                    "only the most essential point.\n\nText:\n{input}"
                ),
            },
            {
                "id": "bullets",
                "name": "Key Points",
                "description": "5 scannable bullet points.",
                "template": (
                    "Read the following text and extract exactly 5 bullet points "
                    "covering its main ideas. Use short, scannable phrases.\n\nText:\n{input}"
                ),
            },
            {
                "id": "exec",
                "name": "Executive Summary",
                "description": "Formal one-paragraph business summary.",
                "template": (
                    "Write a formal, one-paragraph executive summary of the following "
                    "text suitable for a business audience. Use a professional tone and "
                    "avoid casual language.\n\nText:\n{input}"
                ),
            },
        ],
    },
    "creative": {
        "label": "Generate Creative Content",
        "tagline": "Creative Writing",
        "color": "magenta",
        "placeholder": "e.g. a dragon and a princess / autumn / a lonely lighthouse keeper",
        "styles": [
            {
                "id": "story",
                "name": "Short Story",
                "description": "A whimsical ~150-word story.",
                "template": (
                    "Write a short, whimsical story (about 150 words) about the "
                    "following theme. Give it a clear beginning, middle, and end.\n\n"
                    "Theme: {input}"
                ),
            },
            {
                "id": "poem",
                "name": "Poem",
                "description": "A 4-stanza poem with vivid imagery.",
                "template": (
                    "Write a 4-stanza poem about the following theme. Use vivid imagery "
                    "and a consistent rhyme scheme.\n\nTheme: {input}"
                ),
            },
            {
                "id": "brainstorm",
                "name": "Idea Brainstorm",
                "description": "3 distinct creative concept pitches.",
                "template": (
                    "Brainstorm 3 distinct creative concepts inspired by the following "
                    "theme. For each, give a punchy one-line pitch and a 1-sentence "
                    "description.\n\nTheme: {input}"
                ),
            },
        ],
    },
    "advice": {
        "label": "Get Advice",
        "tagline": "Advice & Tips",
        "color": "amber",
        "placeholder": "e.g. How can I study more effectively?",
        "styles": [
            {
                "id": "tips",
                "name": "Quick Tips",
                "description": "5 short, actionable bullet tips.",
                "template": (
                    "Give 5 short, actionable bullet-point tips in response to the "
                    "following request. Keep each tip to one sentence.\n\nRequest: {input}"
                ),
            },
            {
                "id": "plan",
                "name": "Step-by-Step Plan",
                "description": "A numbered, sequential action plan.",
                "template": (
                    "Provide a numbered, step-by-step plan (5-7 steps) to address the "
                    "following request. Briefly explain each step.\n\nRequest: {input}"
                ),
            },
            {
                "id": "coach",
                "name": "Coach's Perspective",
                "description": "Warm, conversational coaching tone.",
                "template": (
                    "Respond like a supportive personal coach speaking directly to "
                    "someone with this request. Use a warm, conversational tone in one "
                    "or two short paragraphs, and end with one encouraging sentence.\n\n"
                    "Request: {input}"
                ),
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# 3. AI call helper (real API call, or demo fallback)
# ---------------------------------------------------------------------------
def call_ai(prompt: str) -> str:
    if client is not None:
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return (response.text or "").strip()
    return demo_response(prompt)


def demo_response(prompt: str) -> str:
    """A small canned-response engine so the assistant is fully testable
    without an API key/billing set up. Clearly labeled as DEMO MODE."""
    lower = prompt.lower()
    if "numbered list" in lower or "interesting facts" in lower:
        body = (
            "1. This is a sample fact generated in demo mode.\n"
            "2. Add a GEMINI_API_KEY (free at aistudio.google.com/apikey) for a real, input-specific answer.\n"
            "3. The prompt structure above is what actually gets sent to the model."
        )
    elif "executive summary" in lower:
        body = (
            "[Demo executive summary] The supplied text would be condensed here into "
            "a single, formal paragraph highlighting its central argument and key "
            "takeaways, written for a business audience."
        )
    elif "bullet points" in lower:
        body = (
            "• Demo bullet one — main idea of the text\n"
            "• Demo bullet two — supporting detail\n"
            "• Demo bullet three — supporting detail\n"
            "• Demo bullet four — notable example or data point\n"
            "• Demo bullet five — concluding takeaway"
        )
    elif "poem" in lower:
        body = (
            "[Demo poem]\nFour stanzas would unfold right here,\n"
            "tracing your theme both far and near,\n"
            "with rhyme and rhythm, line by line —\n"
            "add an API key for the real design."
        )
    elif "story" in lower:
        body = (
            "[Demo story] Once, in a place much like the one you described, something "
            "small set off something large. By the end, everything had changed — just "
            "not in the way anyone expected. (Connect a real API key for a full, "
            "input-specific story.)"
        )
    elif "brainstorm" in lower:
        body = (
            "1. \"Demo Concept A\" — a one-line pitch would appear here.\n"
            "2. \"Demo Concept B\" — a second distinct angle.\n"
            "3. \"Demo Concept C\" — a third, more unexpected angle."
        )
    elif "step-by-step plan" in lower:
        body = (
            "1. Clarify the goal.\n2. Identify the first concrete action.\n"
            "3. Schedule time for it.\n4. Remove one likely obstacle in advance.\n"
            "5. Review progress and adjust."
        )
    elif "coach" in lower:
        body = (
            "[Demo coach response] I hear what you're working on, and it's a "
            "completely reasonable thing to want help with. Start with the smallest "
            "version of the task today — momentum matters more than perfection. You've "
            "got this."
        )
    else:
        body = (
            "[Demo answer] This is a placeholder response because no GEMINI_API_KEY "
            "was found. Get a free key at https://aistudio.google.com/apikey, set it "
            "as an environment variable, and restart the app to get real, "
            "input-specific answers from the model."
        )
    return body


# ---------------------------------------------------------------------------
# 4. Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template(
        "index.html", prompt_library=PROMPT_LIBRARY, demo_mode=DEMO_MODE
    )


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    func_key = data.get("function")
    style_id = data.get("style")
    user_input = (data.get("input") or "").strip()

    if func_key not in PROMPT_LIBRARY:
        return jsonify({"error": "Unknown function."}), 400
    if not user_input:
        return jsonify({"error": "Please enter some input text."}), 400

    function_def = PROMPT_LIBRARY[func_key]
    style = next((s for s in function_def["styles"] if s["id"] == style_id), None)
    if style is None:
        return jsonify({"error": "Unknown prompt style."}), 400

    final_prompt = style["template"].format(input=user_input)

    try:
        ai_text = call_ai(final_prompt)
    except Exception as exc:  # pragma: no cover - defensive
        return jsonify({"error": f"AI call failed: {exc}"}), 500

    return jsonify(
        {
            "prompt_used": final_prompt,
            "response": ai_text,
            "demo_mode": DEMO_MODE,
        }
    )


@app.route("/api/feedback", methods=["POST"])
def feedback():
    data = request.get_json(force=True)
    record = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "function": data.get("function"),
        "style": data.get("style"),
        "input": data.get("input"),
        "response": data.get("response"),
        "helpful": bool(data.get("helpful")),
        "comment": data.get("comment", ""),
    }
    log = json.loads(FEEDBACK_LOG.read_text())
    log.append(record)
    FEEDBACK_LOG.write_text(json.dumps(log, indent=2))
    return jsonify({"status": "ok", "stats": compute_stats(log)})


@app.route("/api/feedback/stats")
def feedback_stats():
    log = json.loads(FEEDBACK_LOG.read_text())
    return jsonify(compute_stats(log))


def compute_stats(log):
    stats = {}
    for key in PROMPT_LIBRARY:
        entries = [r for r in log if r.get("function") == key]
        helpful = sum(1 for r in entries if r.get("helpful"))
        total = len(entries)
        stats[key] = {
            "total": total,
            "helpful": helpful,
            "rate": round((helpful / total) * 100) if total else None,
        }
    return stats


if __name__ == "__main__":
    app.run(debug=True)
