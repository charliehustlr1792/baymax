from typing import Optional
import json


class SessionMemory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.turns = []
        self.entities = {}
        self.unresolved_pronouns = []

    def add_turn(self, role: str, content: str):
        self.turns.append({"role": role, "content": content})

    def get_history(self, last_n: int = 8) -> list:
        return self.turns[-last_n:] if len(self.turns) > last_n else self.turns

    def update_entities(self, new_entities: dict):
        for name, data in new_entities.items():
            if name in self.entities:
                self.entities[name]["mentions"] += data.get("mentions", 1)
                self.entities[name]["valence"] = data.get("valence", self.entities[name]["valence"])
                self.entities[name]["last_turn"] = data.get("last_turn", self.entities[name]["last_turn"])
                if "context" in data:
                    self.entities[name]["context"] = data["context"]
            else:
                self.entities[name] = data

        # keep only 5 most recently mentioned
        if len(self.entities) > 5:
            sorted_entities = sorted(
                self.entities.items(),
                key=lambda x: x[1].get("last_turn", 0),
                reverse=True
            )
            self.entities = dict(sorted_entities[:5])

    def add_unresolved_pronoun(self, pronoun: str, context: str):
        entry = f"{pronoun} — turn {len(self.turns)} — {context}"
        if entry not in self.unresolved_pronouns:
            self.unresolved_pronouns.append(entry)
        if len(self.unresolved_pronouns) > 3:
            self.unresolved_pronouns = self.unresolved_pronouns[-3:]

    def format_entities_for_prompt(self) -> str:
        if not self.entities and not self.unresolved_pronouns:
            return "No entities tracked yet."

        lines = []
        for name, data in self.entities.items():
            valence = data.get("valence", "unknown")
            mentions = data.get("mentions", 1)
            context = data.get("context", "")
            line = f"- {name}: valence={valence}, mentioned {mentions}x"
            if context:
                line += f", context: {context}"
            lines.append(line)

        if self.unresolved_pronouns:
            lines.append("")
            lines.append("Unresolved pronouns (resolve in context, ask if unclear):")
            for p in self.unresolved_pronouns:
                lines.append(f"  - {p}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "turns": self.turns,
            "entities": self.entities,
            "unresolved_pronouns": self.unresolved_pronouns,
        }


# in-memory store: session_id → SessionMemory
_sessions: dict[str, SessionMemory] = {}


def get_session(session_id: str) -> SessionMemory:
    if session_id not in _sessions:
        _sessions[session_id] = SessionMemory(session_id)
    return _sessions[session_id]


def clear_session(session_id: str):
    if session_id in _sessions:
        del _sessions[session_id]