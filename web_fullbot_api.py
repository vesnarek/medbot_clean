from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uuid

from app.flow.engine import (
    start_session, step, PROMPTS,
    S_DONE, S_WAIT_FOLLOWUP
)
from app.services.gpt import generate_gpt_response, generate_final_gpt_response

app = FastAPI()

@app.get("/api/ping")
def ping():
    return {"ok": True}


SESS: dict[str, dict] = {}

@app.post("/api/chat")
async def chat(req: Request):
    try:
        data = await req.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Bad JSON")

    sid = data.get("session_id") or str(uuid.uuid4())
    message = (data.get("message") or "").strip()
    st = SESS.get(sid)

    if st is None:
        state, reply, user_data = start_session()
        SESS[sid] = {"state": state, "user_data": user_data}
        return JSONResponse({"session_id": sid, "reply": reply, "done": False})

    state = st["state"]
    user_data = st["user_data"]
    next_state, reply, user_data, special = step(state, message, user_data)

    if special == "DO_GPT1":
        gpt_reply, follow_up = await generate_gpt_response(user_data)
        st["state"] = S_WAIT_FOLLOWUP
        st["user_data"] = user_data
        out = gpt_reply + (f"\n---\n{follow_up}" if (follow_up or "").strip() else "")
        return JSONResponse({"session_id": sid, "reply": out, "done": False})

    if special == "DO_GPT_FINAL":
        final = await generate_final_gpt_response(user_data)
        SESS.pop(sid, None)
        return JSONResponse({"session_id": sid, "reply": final, "done": True})

    st["state"] = next_state
    st["user_data"] = user_data
    if not reply and next_state in PROMPTS:
        reply = PROMPTS[next_state]

    return JSONResponse({"session_id": sid, "reply": reply, "done": next_state == S_DONE})


app.mount("/web", StaticFiles(directory="web_fullbot_static", html=True), name="static")