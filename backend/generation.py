import os
from groq import AsyncGroq
from dotenv import load_dotenv
from typing import AsyncGenerator

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are EchoMind — a perceptive, warm conversation partner whose only job is to understand what is really happening for this person and respond in a way that is completely specific to them.

YOU ARE NOT: a therapist, a crisis line, or a chatbot with scripted responses.
YOU ARE: a thoughtful presence that reads between the lines and responds to what is actually there.

HARD RULES — violating any of these is a failure:
1. Your response MUST directly engage with at least one exact phrase or word the user actually used.
2. Maximum 3-4 sentences unless the user wrote more than 100 words themselves.
3. End with either one question OR one observation. Never both. Never neither.
4. BANNED PHRASES — never write these:
   "I hear you" / "That sounds really hard" / "I'm sorry to hear that" /
   "It sounds like you're going through" / "That must be difficult" /
   "I understand how you feel" / "You're not alone" / "It's okay to feel this way" /
   "I can imagine how" / "That's completely understandable" / "Thank you for sharing" /
   "your feelings are valid" / "safe space" / "on your journey" / "that resonates"
5. Never assert an emotional state you are not confident in. If uncertain — ask, do not tell.
6. Never introduce a person, event, or fact the user did not mention.
7. Never give advice unless explicitly asked.
8. Never use: "journey", "healing", "space", "valid", "resonate", "nurture", "empower"."""

USER_TURN_TEMPLATE = """REASONING CONTEXT (never quote this, let it inform your words invisibly):
{scratchpad}

MEMORY FROM PAST SESSIONS:
{memory}

ENTITY REGISTER (people and context in this conversation):
{entities}

RETRIEVED TECHNIQUE GUIDANCE (shapes HOW you respond, not WHAT you say):
{exemplars}

CONVERSATION HISTORY:
{history}

USER'S LATEST MESSAGE: "{user_message}"

Write your response now. Be specific. Be human. No templates."""

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
    "thank you for sharing",
    "thank you for trusting",
    "i'm here for you",
    "your feelings are valid",
    "it's okay to",
    "safe space",
    "on your journey",
    "the healing",
    "that resonates",
    "you are valid",
    "so valid",
]


def contains_banned_phrase(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in BANNED_PHRASES)


async def run_generation(
    user_message: str,
    history: list,
    scratchpad: str,
    memory: str = "",
    entities: str = "",
    exemplars: str = "",
    attempt: int = 0
) -> AsyncGenerator[str, None]:

    if attempt >= 3:
        yield "Something about what you said is hard to step past — what's been sitting with you most today?"
        return

    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in history[:-1][-8:]
    )

    user_turn = USER_TURN_TEMPLATE.format(
        scratchpad=scratchpad,
        memory=memory if memory else "No previous session data.",
        entities=entities if entities else "No entities tracked yet.",
        exemplars=exemplars if exemplars else "No exemplars retrieved.",
        history=history_text if history_text else "This is the first message.",
        user_message=user_message
    )

    collected_tokens = []
    full_response = ""

    stream = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_turn}
        ],
        max_tokens=300,
        temperature=0.75,
        stream=True,
    )

    async for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            collected_tokens.append(token)
            full_response += token

    if contains_banned_phrase(full_response):
        async for token in run_generation(
            user_message, history, scratchpad,
            memory, entities, exemplars, attempt + 1
        ):
            yield token
        return

    for token in collected_tokens:
        yield token