import base64, io, sys, time, httpx, numpy as np
from PIL import Image
import imageio.v3 as iio
B = "http://127.0.0.1:18770"
print(httpx.get(B + "/health", timeout=30).json())
img = base64.b64encode(open("/home/wjlyu/Inception/assets/starters/forest_path_photo.jpg", "rb").read()).decode()
t = time.time(); r = httpx.post(B + "/start", json={"image_b64": img, "prompt": "A dirt path through a dense spring forest, walking forward between young green trees with dappled sunlight, no people in view."}, timeout=600); print("start", r.status_code, r.json(), round(time.time()-t, 1))
frames = []
for k, ctl in enumerate([dict(forward=1), dict(forward=1), dict(forward=1, yaw=1), dict(forward=1, yaw=1), dict(forward=1), dict()]):
    t = time.time(); r = httpx.post(B + "/step", json=ctl, timeout=600); j = r.json()
    print(k, ctl, r.status_code, "frames", len(j.get("frames", [])), "gen", j.get("generate_s"), "total", j.get("total_s"), "wall", round(time.time()-t, 1))
    frames += [np.asarray(Image.open(io.BytesIO(base64.b64decode(f)))) for f in j["frames"]]
iio.imwrite("/ssd3/wjlyu/inception_spike/alaya_server_test.mp4", np.stack(frames), fps=24, codec="libx264", plugin="pyav")
print("saved", len(frames))
