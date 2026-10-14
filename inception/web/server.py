"""FastAPI front door: upload a scene, stream frames over WebSocket, send keys and actions.

    python -m inception.web.server --port 7860
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from ..agents.display import Subscriber
from ..config import settings
from ..orchestrator import Game
from ..renderers.base import Keys

log = logging.getLogger("inception.web")
app = FastAPI(title="Inception")
GAME: Game | None = None
AR = CLIP = None   # renderers are created once (GPU models) and reused across games
INDEX_PATH = Path(__file__).parent / "index.html"
STARTERS = Path(__file__).resolve().parent.parent.parent / "assets/starters"


@app.get("/")
def index():
    return HTMLResponse(INDEX_PATH.read_text())   # re-read per request: UI fixes need no restart


@app.get("/starters")
def starters():
    return sorted(p.name for p in STARTERS.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))


@app.get("/starters/{name}")
def starter_file(name: str):
    p = STARTERS / Path(name).name
    if not p.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(p)


@app.post("/start")
async def start(image: UploadFile | None = File(None), starter: str = Form(""), premise: str = Form(""), tone: str = Form("calm exploration")):
    global GAME, AR, CLIP
    from ..orchestrator import make_renderers
    if AR is None:
        AR, CLIP = make_renderers(settings.video_width, settings.video_height, settings.display_fps)
    if GAME is not None:
        GAME.display.stop()
    GAME = Game(ar=AR, clip=CLIP)
    if image is not None and image.filename:
        tmp = GAME.session.frames / ("upload" + Path(image.filename).suffix)
        tmp.write_bytes(await image.read())
    elif starter and (STARTERS / Path(starter).name).exists():
        tmp = STARTERS / Path(starter).name
    else:
        return JSONResponse({"error": "pick a starter image or upload one"}, status_code=400)
    opening = await asyncio.to_thread(GAME.start, str(tmp), premise, "", tone)
    GAME.display.event({"type": "session", "id": GAME.session_id, "age_min": 0, "started": True})
    return {"session": GAME.session_id, "opening": opening}


@app.post("/act")
async def act(payload: dict):
    if GAME is None:
        return JSONResponse({"error": "No world yet: pick a starter image and click Start world"}, status_code=400)
    if not GAME.started:
        return JSONResponse({"error": "The world is still being built; wait for the opening narration"}, status_code=409)
    text = (payload.get("text") or "").strip()
    if not text:
        return JSONResponse({"error": "empty"}, status_code=400)
    GAME.act(text)
    return {"ok": True}


@app.get("/events")
def events(last: int = 60):
    return GAME.session.events(last) if GAME else []


@app.websocket("/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    loop = asyncio.get_running_loop()
    q: asyncio.Queue = asyncio.Queue(maxsize=64)

    def on_frame(data: bytes):
        if q.qsize() < 48:   # drop frames rather than build latency
            loop.call_soon_threadsafe(q.put_nowait, data)

    def on_event(payload: dict):
        loop.call_soon_threadsafe(q.put_nowait, json.dumps(payload, ensure_ascii=False))

    sub = Subscriber(on_frame=on_frame, on_event=on_event)
    game = GAME
    if game is not None:
        game.subscribe(sub)
        age = (time.time() - game.session.state.started_at) / 60 if game.session.state.started_at else 0
        on_event({"type": "session", "id": game.session_id, "age_min": round(age, 1), "started": game.started})

    async def sender():
        while True:
            item = await q.get()
            if isinstance(item, bytes):
                await ws.send_bytes(item)
            else:
                await ws.send_text(item)

    send_task = asyncio.create_task(sender())
    try:
        while True:
            msg = await ws.receive_text()
            data = json.loads(msg)
            if GAME is not None and game is not GAME:      # a new game started: re-subscribe
                game = GAME
                game.subscribe(sub)
            if "keys" in data and GAME is not None:
                k = data["keys"]
                GAME.set_keys(Keys(w=bool(k.get("w")), a=bool(k.get("a")), s=bool(k.get("s")), d=bool(k.get("d")),
                                   dx=float(k.get("dx", 0)), dy=float(k.get("dy", 0))))
    except WebSocketDisconnect:
        pass
    finally:
        sub._dead = True
        send_task.cancel()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7860)
    ap.add_argument("--host", default="0.0.0.0")
    a = ap.parse_args()
    uvicorn.run(app, host=a.host, port=a.port, log_level="info")


if __name__ == "__main__":
    main()
