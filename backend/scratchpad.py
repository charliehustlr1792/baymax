import os
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

SCRATCHPAD_SYSTEM = """You are an internal reasoning engine for an emotional support AI.
Your output is NEVER shown to the user. You reason privately and clinically about what is really happening in the user's message before any response is generated.
Be specific. Name mechanisms, not categories. Your reasoning drives everything downstream."""

SCRATCHPAD_PROMPT = """Analyze the latest user message carefully and answer each section:

1. SURFACE
What is the literal content of the message?

2. UNDERNEATH
What is actually happening emotionally? Name the specific psychological mechanism.
Examples: "emotional numbing as avoidance", "deflection masking distress", "self-blame as control mechanism", "withdrawal signaling hopelessness", "sarcasm as protective distance", "minimisation of significant loss".
Do not write a category. Write the mechanism.

3. LINGUISTIC SIGNALS
Identify any present:
- Deflection markers: "it's whatever", "I don't know", "doesn't matter", "I guess", "anyway"
- Hedge chains: "kind of", "maybe", "sort of", "I suppose", "I think maybe"
- Significance-tone gaps: casual or dismissive framing applied to objectively serious events
- Sarcasm: positive surface language contradicted by negative behavioural content
- Topic abandonment: raising something significant then immediately dismissing it

4. CONFIDENCE
high = mechanism is clear from explicit content or strong linguistic signals
medium = plausible reading but limited direct evidence
low = genuinely ambiguous, multiple valid interpretations

5. RESPONSE MODE
high confidence → interpret: name the mechanism directly, then ask one deepening question
medium/low confidence → explore: reflect what was heard, ask a curious open question, assert nothing about their emotional state

6. ANCHOR WORDS
List the exact words or phrases from the user's message that the response MUST directly engage with.

7. SAFETY TIER
none / 1 (stress, burnout) / 2 (hopelessness, withdrawal, "I'm a burden") / 3 (self-harm, suicidal ideation, crisis)

Conversation history:
{history}

Latest user message: "{user_message}"
"""


async def run_scratchpad(user_message: str, history: list) -> str:
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in history[:-1][-6:]
    )

    prompt = SCRATCHPAD_PROMPT.format(
        history=history_text if history_text else "This is the first message.",
        user_message=user_message
    )

    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SCRATCHPAD_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        max_tokens=400,
        temperature=0.3,
    )

    return response.choices[0].message.content