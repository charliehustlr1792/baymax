from memory.session import get_session
from memory.crosssession import format_memory_for_prompt


async def assemble_context(
    user_id: str,
    session_id: str,
    user_message: str,
) -> dict:
    session = get_session(session_id)

    cross_session_memory = await format_memory_for_prompt(user_id)
    entities_formatted = session.format_entities_for_prompt()
    history = session.get_history(last_n=8)

    return {
        "history": history,
        "memory": cross_session_memory,
        "entities": entities_formatted,
        "session": session,
    }


async def update_entity_register(
    session_id: str,
    scratchpad: str,
    turn_number: int
):
    """
    Parse entity mentions from the scratchpad reasoning and update the session register.
    We use simple heuristic extraction here — the scratchpad already names entities.
    A future improvement would be a dedicated NER call.
    """
    session = get_session(session_id)

    lines = scratchpad.lower().split("\n")
    pronouns_to_watch = ["he", "she", "they", "him", "her", "them"]

    for line in lines:
        for pronoun in pronouns_to_watch:
            if f" {pronoun} " in line and "unresolved" in line:
                session.add_unresolved_pronoun(pronoun, line.strip()[:80])