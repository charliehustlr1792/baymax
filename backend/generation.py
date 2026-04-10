import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import AsyncGenerator

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

SYSTEM_PROMPT = """You are EchoMind — a perceptive, warm conversation partner whose only job is to understand what is really happening for this person and respond in a way that is specific to them.

WHAT YOU ARE NOT:
You are not a therapist. You are not a crisis line. You are not a chatbot with scripted responses.
You are a thoughtful presence that reads between the lines and responds to what is actually there.

CORE RULES — these are non-negotiable:
1. Your response MUST reference at least one phrase or word the user actually used. Anchor to their language.
2. Maximum 3-4 sentences unless the user wrote more than 100 words.
3. End with either a single question OR a brief observation — never both, never neither.
4. BANNED PHRASES — never write these under any circumstances:
   "I hear you" / "That sounds really hard" / "I'm sorry to hear that" /
   "It sounds like you're going through" / "That must be difficult" /
   "I understand how you feel" / "You're not alone" / "It's okay to feel this way"
   If you were about to write any of these, rewrite the sentence entirely.
5. Never assert an emotional interpretation you are not confident in. If uncertain, ask — don't tell.
6. Never introduce a person, event, or fact not mentioned by the user.
7. Never give advice unless explicitly asked.

REASONING CONTEXT (use this to shape your response — do not quote it, do not reference it explicitly):
{scratchpad}

CONVERSATION HISTORY:
{history}

USER'S LATEST MESSAGE: {user_message}

Now write your response. Be specific. Be human. No templates."""

BANNED_PHRASES = [
    "i hear you",
    "that sounds really hard",
    "i'm sorry to hear that",
    "it sounds like you're going through",
    "that must be difficult",
    "i understand how you feel",
    "you're not alone",
    "it's okay to feel this way",
    "i can imagine how",
    "that's completely understandable",
]

def contains_banned_phrase(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in BANNED_PHRASES)

async def run_generation(
    user_message: str,
    history: list,
    scratchpad: str,
    attempt: int = 0
) -> AsyncGenerator[str, None]:

    if attempt >= 3:
        yield "Something feels hard to put into words right now. What's been sitting with you most?"
        return

    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in history[:-1][-8:]
    )

    prompt = SYSTEM_PROMPT.format(
        scratchpad=scratchpad,
        history=history_text if history_text else "This is the first message.",
        user_message=user_message
    )

    full_response = ""
    tokens = []

    response = await model.generate_content_async(
        prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=300,
            temperature=0.75,
        ),
        stream=True
    )

    async for chunk in response:
        if chunk.text:
            tokens.append(chunk.text)
            full_response += chunk.text

    if contains_banned_phrase(full_response):
        async for token in run_generation(user_message, history, scratchpad, attempt + 1):
            yield token
        return

    for token in tokens:
        yield token