from groq import AsyncGroq
from dotenv import load_dotenv
import os
import re

load_dotenv()
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

TIER_3_KEYWORDS = [
    "kill myself", "killing myself", "want to die", "want to be dead",
    "end my life", "ending my life", "suicide", "suicidal",
    "self harm", "self-harm", "cutting myself", "hurt myself",
    "hurting myself", "don't want to be here", "dont want to be here",
    "not worth living", "better off dead", "better off without me",
    "no reason to live", "can't go on", "cant go on",
]

TIER_2_KEYWORDS = [
    "burden", "worthless", "hopeless", "pointless", "no point",
    "can't see the point", "cant see the point", "give up", "giving up",
    "nothing matters", "don't care anymore", "dont care anymore",
    "empty inside", "completely empty", "feel nothing",
    "disappear", "everyone would be better",
]

TIER_2_RESPONSES = """
At the end of your response, weave in ONE natural check-in — not as a separate paragraph, not as a hotline dump. 
Integrate it as a genuine question: something like "have you had anyone around you to talk to about this?" or 
"is there someone in your life who knows things have been feeling this heavy?"
Do NOT add hotline numbers. Do NOT break the conversational flow. ONE sentence, woven in naturally.
"""

TIER_3_RESPONSE_INSTRUCTION = """
IMPORTANT: This person may be in crisis. Your response must:
1. First — acknowledge what they said directly and specifically. Do not skip past it.
2. Second — validate that this level of pain is real, without minimising or over-dramatising.
3. Third — gently introduce support: "I want to make sure you have someone to talk to right now — 
   if things feel this heavy, reaching out to a crisis line like iCall (9152987821) or the 
   Vandrevala Foundation (1860-2662-345) can help. They're there specifically for moments like this."
4. Keep your tone warm and human throughout. Do not sound like a safety script.
5. Do not end the conversation. Ask one question after the resource mention.
"""


def detect_safety_tier_fast(text: str) -> int:
    lower = text.lower()

    for phrase in TIER_3_KEYWORDS:
        if phrase in lower:
            return 3

    for phrase in TIER_2_KEYWORDS:
        if phrase in lower:
            return 2

    return 1


async def detect_safety_tier_llm(text: str, scratchpad: str) -> int:
    scratchpad_tier = 1
    tier_match = re.search(r"SAFETY TIER[:\s]+(\d|none)", scratchpad, re.IGNORECASE)
    if tier_match:
        val = tier_match.group(1)
        if val.isdigit():
            scratchpad_tier = int(val)

    fast_tier = detect_safety_tier_fast(text)

    return max(scratchpad_tier, fast_tier)


def get_safety_instruction(tier: int) -> str:
    if tier == 3:
        return TIER_3_RESPONSE_INSTRUCTION
    elif tier == 2:
        return TIER_2_RESPONSES
    else:
        return ""