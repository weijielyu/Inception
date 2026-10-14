"""Headless end-to-end smoke test against a running web server.
   python scripts/smoke_ws.py http://127.0.0.1:7861 assets/test_game.png [--walk 20] [--wait 90]"""
import argparse
import asyncio
import json
import time

import httpx
import websockets

ap = argparse.ArgumentParser()
ap.add_argument("base"); ap.add_argument("image")
ap.add_argument("--walk", type=float, default=20, help="seconds to hold W")
ap.add_argument("--wait", type=float, default=90, help="seconds to wait for the action clip")
ap.add_argument("--action", default="我要开始挖地")
ap.add_argument("--pre-wait", type=float, default=2, help="idle seconds before walking")
a = ap.parse_args()
ws_url = a.base.replace("http", "ws") + "/stream"


async def main():
    t0 = time.time()
    el = lambda: f"[{time.time()-t0:6.1f}s]"
    with open(a.image, "rb") as f:
        r = httpx.post(a.base + "/start", files={"image": ("seed.png", f, "image/png")}, data={"premise": ""}, timeout=900)
    print(el(), "/start ->", r.status_code, r.json().get("opening", "")[:120])
    frames, modes, events = 0, [], []
    async with websockets.connect(ws_url, max_size=None) as ws:
        async def reader():
            nonlocal frames
            async for msg in ws:
                if isinstance(msg, bytes):
                    frames += 1
                else:
                    m = json.loads(msg)
                    if m["type"] == "mode":
                        modes.append((round(time.time() - t0, 1), m["mode"], m["keys_locked"]))
                    elif m["type"] in ("narration", "status"):
                        events.append((round(time.time() - t0, 1), m["type"], m["text"][:100]))
        task = asyncio.create_task(reader())
        await asyncio.sleep(a.pre_wait)
        print(el(), f"hold W for {a.walk}s"); await ws.send(json.dumps({"keys": {"w": True}}))
        f0 = frames; await asyncio.sleep(a.walk); print(el(), f"  {frames-f0} frames while walking")
        await ws.send(json.dumps({"keys": {"w": False}}))
        print(el(), "release; wait 3s"); await asyncio.sleep(3)
        print(el(), "act:", a.action)
        httpx.post(a.base + "/act", json={"text": a.action}, timeout=30)
        await asyncio.sleep(2)
        await ws.send(json.dumps({"keys": {"d": True}}))   # should be ignored while locked
        t_wait = time.time()
        while time.time() - t_wait < a.wait and not any(m[1] == "clip" for m in modes):
            await asyncio.sleep(1)
        print(el(), "clip started" if any(m[1] == "clip" for m in modes) else "clip NOT seen")
        await asyncio.sleep(8)
        await ws.send(json.dumps({"keys": {"d": False}}))
        task.cancel()
    dur = time.time() - t0
    print(f"frames received: {frames} in {dur:.0f}s (~{frames/dur:.1f} fps avg)")
    print("mode transitions:", modes)
    for e in events:
        print("  event", e)
    ev = httpx.get(a.base + "/events?last=80", timeout=30).json()
    for e in ev:
        if e["event"] in ("ar_started", "ar_reseed", "ar_error", "clip", "idle_rendered", "action_done", "action_error", "vlm_audit", "clip_done"):
            print("  log", e["agent"], e["event"], {k: v for k, v in e.items() if k not in ("ts", "turn", "agent", "event")})


asyncio.run(main())
