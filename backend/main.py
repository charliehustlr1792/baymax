from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import json

from scratchpad import run_scratchpad
from generation import run_generation

app = FastAPI()

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
    session_id: str
    messages: List[Message]


@app.get("/")
def root():
    return {"status": "EchoMind backend running"}


@app.post("/chat")
async def chat(request: ChatRequest):
    history = [m.model_dump() for m in request.messages]
    user_message = history[-1]["content"]

    scratchpad = await run_scratchpad(user_message, history)

    async def stream():
        async for token in run_generation(
            user_message=user_message,
            history=history,
            scratchpad=scratchpad,
        ):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")