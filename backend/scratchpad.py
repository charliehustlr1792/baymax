import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

SCRATCHPAD_PROMPT = """You are an internal reasoning engine for an emotional support AI.
Your job is to think carefully about what is REALLY happening in the user's message before any response is generated.
You are never shown to the user. Be honest, specific, and clinical in your reasoning.

Analyze the latest user message and answer these questions in order:

1. SURFACE: What is the literal content of the message?
2. UNDERNEATH: What is actually happening emotionally? Name the specific mechanism if possible (e.g. "emotional numbing as avoidance", "deflection masking distress", "self-blame as control", "withdrawal signaling hopelessness"). Do not settle for a category — name the mechanism.
3. LINGUISTIC SIGNALS: Note any deflection markers ("it's whatever", "I don't know", "doesn't matter"), hedge chains, significance-tone gaps (casual framing of serious events), or sarcasm patterns.
4. CONFIDENCE: How confident are you in your reading? high / medium / low
5. RESPONSE MODE: Based on confidence — "interpret" (high: name the mechanism, then deepen) or "explore" (medium/low: reflect and ask without asserting)
6. ANCHOR WORDS: Which exact words or phrases from the user's message MUST appear or be directly referenced in the response?
7. SAFETY: Is there any risk signal? If yes, tier: 1 (stress/burnout) / 2 (hopelessness/withdrawal) / 3 (crisis/self-harm). If no, write "none".

Conversation history for context:
{history}

Latest user message: {user_message}

Write your reasoning now:"""

async def run_scratchpad(user_message: str, history: list) -> str:
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in history[:-1][-6:]
    )

    prompt = SCRATCHPAD_PROMPT.format(
        history=history_text if history_text else "This is the first message.",
        user_message=user_message
    )

    response = await model.generate_content_async(
        prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=300,
            temperature=0.3,
        )
    )

    return response.text