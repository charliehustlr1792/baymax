import re
from typing import Optional

BANNED_PHRASES = [
    "i hear you",
    "that sounds really hard",
    "i'm sorry to hear that",
    "im sorry to hear that",
    "it sounds like you're going through",
    "it sounds like you are going through",
    "that must be difficult",
    "that must be really",
    "i understand how you feel",
    "i understand how you're feeling",
    "you're not alone",
    "you are not alone",
    "it's okay to feel this way",
    "its okay to feel",
    "i can imagine how",
    "that's completely understandable",
    "thats completely understandable",
    "thank you for sharing",
    "thank you for trusting",
    "i'm here for you",
    "im here for you",
    "your feelings are valid",
    "your emotions are valid",
    "it's okay to",
    "its okay to",
    "safe space",
    "on your journey",
    "the healing",
    "that resonates",
    "you are valid",
    "so valid",
    "i really hear",
    "must be tough",
    "must be so hard",
    "that's so hard",
    "thats so hard",
]

GENERIC_OPENERS = [
    "it seems like",
    "it appears that",
    "i can see that",
    "i can tell that",
    "it's clear that",
    "its clear that",
    "obviously",
    "clearly you",
]


def check_quality(response: str) -> tuple[bool, Optional[str]]:
    """
    Returns (passed: bool, reason: Optional[str])
    passed=True means the response is clean.
    passed=False means it should be regenerated.
    """
    lower = response.lower()

    for phrase in BANNED_PHRASES:
        if phrase in lower:
            return False, f"banned_phrase: '{phrase}'"

    sentences = response.strip().split(".")
    if sentences:
        first_sentence = sentences[0].lower().strip()
        for opener in GENERIC_OPENERS:
            if first_sentence.startswith(opener):
                return False, f"generic_opener: '{opener}'"

    if len(response.strip()) < 30:
        return False, "response_too_short"

    if len(response.strip()) > 800:
        return False, "response_too_long"

    question_count = response.count("?")
    if question_count > 2:
        return False, f"too_many_questions: {question_count}"

    return True, None


def extract_entity_mentions(response: str, known_entities: dict) -> list[str]:
    """
    Check if the response mentions any entities NOT in the known entity register.
    Returns list of suspicious names found.
    """
    words = re.findall(r'\b[A-Z][a-z]+\b', response)

    known_names = set(known_entities.keys())

    common_words = {
        "I", "The", "A", "An", "It", "He", "She", "They", "We",
        "You", "This", "That", "What", "When", "Where", "How",
        "Is", "Are", "Was", "Were", "Have", "Has", "Do", "Does",
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday", "January", "February", "March",
        "April", "May", "June", "July", "August", "September",
        "October", "November", "December",
    }

    suspicious = []
    for word in words:
        if word not in common_words and word not in known_names:
            if len(word) > 3:
                suspicious.append(word)

    return suspicious