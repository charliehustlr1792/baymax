import os
import json
import aiosqlite
from dotenv import load_dotenv
from groq import AsyncGroq

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

DB_PATH = "echomind.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                narrative_summary TEXT DEFAULT '',
                verbal_highlights TEXT DEFAULT '[]',
                entity_history TEXT DEFAULT '{}',
                session_count INTEGER DEFAULT 0,
                last_updated TEXT DEFAULT ''
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS session_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                turn_count INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def get_user_memory(user_id: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT narrative_summary, verbal_highlights, entity_history, session_count FROM user_profiles WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {
                    "narrative_summary": "",
                    "verbal_highlights": [],
                    "entity_history": {},
                    "session_count": 0,
                }
            return {
                "narrative_summary": row[0] or "",
                "verbal_highlights": json.loads(row[1] or "[]"),
                "entity_history": json.loads(row[2] or "{}"),
                "session_count": row[3] or 0,
            }


async def format_memory_for_prompt(user_id: str) -> str:
    memory = await get_user_memory(user_id)

    if not memory["narrative_summary"] and not memory["verbal_highlights"]:
        return ""

    lines = []

    if memory["narrative_summary"]:
        lines.append("What you know about this person from past sessions:")
        lines.append(memory["narrative_summary"])

    if memory["verbal_highlights"]:
        lines.append("")
        lines.append("Their most emotionally significant past statements (exact words):")
        for highlight in memory["verbal_highlights"]:
            lines.append(f'  "{highlight}"')

    return "\n".join(lines)


SUMMARY_PROMPT = """You are writing a psychological memory summary for an emotional support AI.
This summary will be injected into future conversations so the AI can provide continuity.

Based on this conversation, write a concise summary (max 150 words) covering:
- Key stressors or problems the person is dealing with
- Their emotional patterns and coping style (how they talk about hard things)
- Important people in their life and the emotional valence of those relationships
- Any unresolved threads — things raised but not resolved
- How they tend to communicate (direct, deflective, minimising, etc.)

Be specific and clinical. Write in third person. Do not use the person's name.

Previous summary (if any — incorporate and update, do not just replace):
{previous_summary}

Conversation to summarise:
{conversation}

Write the updated summary now:"""

HIGHLIGHTS_PROMPT = """You are identifying the most emotionally significant statements from a conversation.

Select 3-5 utterances from the USER that are the most emotionally loaded, revealing, or significant.
These should be statements that capture something true and specific about this person's inner experience.
Prefer statements that show: coping mechanisms, self-perception, relationship patterns, or moments of genuine vulnerability.
Do NOT select generic statements. Select the ones that would be most useful to remember.

Conversation:
{conversation}

Return ONLY a JSON array of strings — the exact user utterances, no modifications.
Example format: ["statement one", "statement two", "statement three"]
Return only the JSON array, nothing else."""


async def write_session_memory(
    user_id: str,
    session_id: str,
    turns: list,
    entities: dict
):
    if len(turns) < 2:
        return

    conversation = "\n".join(
        f"{t['role'].upper()}: {t['content']}"
        for t in turns
    )

    existing = await get_user_memory(user_id)

    summary_response = await client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": SUMMARY_PROMPT.format(
                previous_summary=existing["narrative_summary"] or "None yet.",
                conversation=conversation
            )
        }],
        max_tokens=200,
        temperature=0.3,
    )
    new_summary = summary_response.choices[0].message.content.strip()

    highlights_response = await client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": HIGHLIGHTS_PROMPT.format(conversation=conversation)
        }],
        max_tokens=200,
        temperature=0.2,
    )

    raw = highlights_response.choices[0].message.content.strip()
    try:
        new_highlights = json.loads(raw)
        if not isinstance(new_highlights, list):
            new_highlights = []
    except json.JSONDecodeError:
        new_highlights = []

    all_highlights = existing["verbal_highlights"] + new_highlights
    all_highlights = all_highlights[-8:]

    merged_entities = {**existing["entity_history"], **entities}

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_profiles (user_id, narrative_summary, verbal_highlights, entity_history, session_count, last_updated)
            VALUES (?, ?, ?, ?, 1, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                narrative_summary = excluded.narrative_summary,
                verbal_highlights = excluded.verbal_highlights,
                entity_history = excluded.entity_history,
                session_count = session_count + 1,
                last_updated = excluded.last_updated
        """, (
            user_id,
            new_summary,
            json.dumps(all_highlights),
            json.dumps(merged_entities),
        ))

        await db.execute("""
            INSERT INTO session_log (user_id, session_id, turn_count)
            VALUES (?, ?, ?)
        """, (user_id, session_id, len(turns)))

        await db.commit()