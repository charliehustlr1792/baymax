from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import json

from scratchpad import run_scratchpad
from generation import run_generation
from context_assembly import assemble_context, update_entity_register
from memory.session import get_session, clear_session
from memory.crosssession import init_db, write_session_memory


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    messages: List[Message]


class EndSessionRequest(BaseModel):
    user_id: str
    session_id: str


@app.get("/")
def root():
    return {"status": "EchoMind backend running"}


@app.post("/chat")
async def chat(request: ChatRequest):
    history = [m.model_dump() for m in request.messages]
    user_message = history[-1]["content"]

    session = get_session(request.session_id)
    session.add_turn("user", user_message)

    context = await assemble_context(
        user_id=request.user_id,
        session_id=request.session_id,
        user_message=user_message,
    )

    scratchpad = await run_scratchpad(user_message, history)

    await update_entity_register(
        session_id=request.session_id,
        scratchpad=scratchpad,
        turn_number=len(session.turns)
    )

    async def stream():
        full_response = ""

        async for token in run_generation(
            user_message=user_message,
            history=history,
            scratchpad=scratchpad,
            memory=context["memory"],
            entities=context["entities"],
        ):
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        session.add_turn("assistant", full_response)
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/end-session")
async def end_session(request: EndSessionRequest):
    session = get_session(request.session_id)

    if len(session.turns) >= 2:
        await write_session_memory(
            user_id=request.user_id,
            session_id=request.session_id,
            turns=session.turns,
            entities=session.entities,
        )

    clear_session(request.session_id)
    return {"status": "session ended", "turns_saved": len(session.turns)}


@app.get("/memory/{user_id}")
async def get_memory(user_id: str):
    from memory.crosssession import get_user_memory
    memory = await get_user_memory(user_id)
    return memory