# Offline evals (2026-10-09)

Two loops that measure the agent side without playing through the UI:

- `scripts/gm_eval.py` — runs the merged GM call on a batch of inputs against a fixed world state; prints kind / ruling / dice / narration / shot prompt. ~5 s per input (DeepSeek).
- `scripts/clip_eval.py` — renders each shot prompt from a start frame with Wan2.2 TI2V-5B (640×352, 65 frames, 25 steps ≈ 23 s) and scores it with the VLM judge (0–10: 0.4·continuity + 0.35·action + 0.25·artifact-free).

## GM eval, 8 inputs (forest-path state, DeepSeek `deepseek-chat`)

| input | kind | ruling | notes |
|---|---|---|---|
| 我要开始挖地 | action/dig | conditional d5, d20=17 ✓ | found the hidden compass (uses the hidden fact), hands-digging prompt |
| There is an elephant on the road | declare | allowed | elephant walks into view; recorded as entity |
| 这是哪里？附近有人吗？ | question/look | allowed | answers from facts; calm look-around prompt |
| 我爬上最近的那棵树看看远处 | action/climb | conditional d4, d20=14 ✓ | reveals a fork + turned earth (new facts) |
| 我把背包里的东西都倒出来 | action/empty | allowed | invents plausible inventory |
| 召唤一条龙把这里烧了 | action/summon | **denied** | futile attempt rendered (bird startles, sky empty) |
| It starts to rain heavily | declare | allowed | weather change prompt |
| 我大声喊：有人吗！ | action/shout | allowed | a faint metallic note from the compass direction (hint) |

Verdict: classification, rulings, bilingual narration and prompt structure are all usable as-is. Latency 4–6 s per call.

## Clip eval, same 8 prompts

Start image **mismatched** (snow-field game image vs forest prompts): mean **0.71** — every clip "changes scene drastically". Lesson: the shot prompt must describe the frame it starts from. → added a **perception step** (`Game._caption_view`): the current frame is captioned by the VLM whenever it changes and passed to the GM as CURRENT VIEW.

Start image **matched** (forest-path photo): mean **4.19**
- elephant declaration **8.45** (elephant walks toward the camera) — entity-appears prompts work
- question / look around 6.5 (static), backpack 5.55, shout 3.8, climb 3.3, dragon-futility 3.3
- **dig 1.3, rain 1.3** — hands-doing-things and weather changes fail at this model size/resolution (artifacts, scene drift)

Takeaways for prompt/agent work:
1. Anchor every clip prompt to the current frame (done).
2. "Something enters the frame" is reliable; "hands manipulate the ground" is not with TI2V-5B at 640×352 — prefer camera-level or entity-level descriptions of outcomes (the hole appears, the box is visible) over hand choreography, or render hands with a stronger model.
3. Keep the VLM judge in the loop: it agrees with human judgement on these failures.

## HY-WorldPlay spike (walking renderer candidate)
See `logs/spike_wp1.log` / `/ssd3/wjlyu/inception_sessions/spike/wp1/`. Constraints learned: `num_frames` must match the pose string (1 + 4·latents) and the AR model needs the latent count divisible by 4 (e.g. 125, 189, 253 frames).

## Prompt experiments (2026-10-09, same 8 inputs, forest-path photo start frame)

| variant | mean judge score | time / clip | notes |
|---|---|---|---|
| v1 prompts (hands choreography), 640×352, 25 steps | 4.19 | 23 s | dig 1.3, rain 1.3, elephant 8.5 |
| **(a) v2 prompts: "result + camera", hands at most once** | **5.10** | 23 s | dig 5.2, rain 3.6, elephant 8.0; continuity "consistent/perfect" far more often |
| (b) v2 + best-of-2 seeds (judge picks) | 5.97 (vs 5.62 seed-0 in that run) | 46 s | +0.35 only — not worth 2× latency on its own |
| **(c) v2 at 832×480, 25 steps** | **7.19** | 45 s | dig 7.05, rain 7.15, look-around 10, elephant 7.6; artifacts drop sharply |

Decisions: keep the v2 prompt guidance (in `agents/gm.py`); expose `CLIP_RENDER_SIZE=832x480` (render bigger, downscale to the 640×352 display) — roughly doubles action-clip latency (≈32 s → ≈55 s to screen) for a +2 point quality jump; best-of-N deferred.

## HY-WorldPlay (AR-distilled, 480p, 4× RTX 6000 Ada sp=4) — run on vllab12
This host (vllab13) cannot run it: NVML is broken (driver 550 vs libnvidia-ml 580) so NCCL fails and even the single-GPU OOM path asserts inside PyTorch. On vllab12 (healthy drivers, GPUs 0–3): forest-path **photo** + pose `w-17, right-6, w-8`, 125 frames → coherent, photorealistic walk with a clean right turn, no drift (`logs/sheet_worldplay.jpg`, video `/ssd3/wjlyu/inception_sessions/spike/worldplay_forest.mp4`). Each 16-frame chunk takes ≈5.5 s (4 steps × 1.38 s) → ≈3 fps generated, i.e. ~8× slower than real time at 24 fps; whole run 4:45 incl. ~2 min model load. Memory ~87 GB host RAM, 4 GPUs. Not a live walking renderer as-is, but the only open model so far that keeps a real photo consistent — candidate for pre-generated "walk segments" with memory, or for a faster distilled/fp8 path.

Run 2 (vllab12): pose `w-30, left-10, w-23`, 253 frames = 10.5 s @24 fps → still the same forest, clean left turn, slight softening in the last seconds (`logs/sheet_worldplay_10s.jpg`, `/ssd3/wjlyu/inception_sessions/spike/worldplay_forest_10s.mp4`). Wall 5:41 vs 4:45 for 125 frames → marginal ≈ 0.44 s per output frame (≈ 2.3 fps generated), fixed cost ≈ 3:50 (model load ≈ 2 min + first-chunk warm-up). A resident server (load once, keep KV/memory) would bring a 2–3 s walk segment to ≈ 20–30 s of generation on 4 GPUs.

### HY-WorldPlay 1.5 mid-stream prompt switch (vllab14, 4 GPUs, per-rank GPU wrapper + early CUDA claim)
Patched `_ar_rollout_inner` to swap the text embeddings at a scheduled chunk (`--prompt_schedule "4:..."`); the context KV is rebuilt every chunk, so the switch is recached automatically. Result for "walk → heavy rain at chunk 4": the switch is applied (log), the walk and right turn are correct, **but the picture never changes — sunny forest to the end** (`logs/sheet_worldplay_rain.jpg`). Text has little influence once the rollout is anchored on the image + actions in this distilled model; a second test with an entity-appears event (deer) is queued to see whether local changes work better than global weather.
- Entity-appears switch ("a deer walks onto the path" at chunk 4) with the **distilled 4-step** model: no deer, output visually identical to the rain run (`logs/sheet_worldplay_deer.jpg`). Hypothesis: `few_step` forces `guidance_scale=1.0` (no CFG), so text barely influences the rollout once image + actions anchor it. Verification queued: non-distilled `ar_model`, 30 steps, guidance 6.0 (pipeline default), same deer schedule.
- WorldPlay2-Fast (4-step, guide scale 1.0, 4× Ada, FSDP): walk + right turn coherent at 832×448; prompt2 "heavy rain" only dims the light (`logs/sheet_worldplay2_rain.jpg`); ~14 s per 16-frame chunk (≈1.1 fps), ~10 min load (no triton).
- **CFG verification (non-distilled `ar_model`, 30 steps, guidance 6.0, same deer schedule; vllab14 GPUs 2–5, 13 min wall)**: still **no deer**; the image gets softer/painterly vs the distilled model (`logs/sheet_worldplay_deer_cfg.jpg`). Hypothesis refuted: HY-WorldPlay 1.5's text channel is effectively inert mid-stream even with CFG. Text events must come from the clip renderer (Wan) or a model trained for semantic events (WorldPlay2 BI/AR 40-step, AlayaWorld) — untested.

## WorldPlay2 on vllab13 (driver fixed 2026-10-11; 4× RTX 6000 Ada, FSDP + Ulysses, triton working)
- Run 2: 48 latents (189 frames, 832×448), actions w-16 / right-8 / w-24; prompt2 "a deer walks out of the trees onto the path" from latent 16, prompt3 "dark clouds, heavy rain" from latent 32.
- **The deer appears** (frames ~75–112): walks out of the trees onto the path, realistic, scene unchanged → **entity-appears text events work in WorldPlay2** (`logs/sheet_wp2_local2.jpg`). Rain again only darkens the scene. Walk + turn stay coherent; the last seconds walk into dense trees (close-up birch) — steer-away logic needed, as with any world model.
- Speed: 13.3 s per 16-frame chunk (≈1.2 fps) with compile active — compile is not the bottleneck; load ≈ 10 min (two 35 GB experts + FSDP sharding) → resident server mandatory.

## AlayaWorld (v1.0 merged bundle, da3 path) — official case1 on vllab14, 2× RTX 6000 Ada (2026-10-13)
- Setup fixes: torch pinned to 2.7.1+cu128, xformers removed, extra deps (easydict, addict, av, DA3 deps); Gemma text encoder moved to a 2nd GPU (`ALAYA_TEXT_DEVICE=cuda:1`, patch in `alaya/inference/engine.py`) and `spatial_memory.da3_device: cuda:1` + `attention_type: pytorch` in `configs/infer_pt.yaml`; `--compile none` (reduce-overhead compile dies at chunk 5 on Ada: triton "out of resource: shared memory", eager fallback then OOMs).
- Result: 12 chunks = 384 frames, 960×544, 16 s (`logs/sheet_alaya_case1.jpg`, `/ssd3/wjlyu/inception_sessions/spike/alaya_case1.mp4`). Camera walks forward and pans right along the Acropolis terrace with stable geometry and lighting; the end "skill" prompt (a bird of fire descends) **renders clearly in the last ~4 s** → mid-rollout text events work, including a new entity + effect.
- Speed without compile: 9.3–10 s per 32-frame chunk for chunks 1–4 and 9 (≈3.3 fps), 29 s for chunks 5–8, 6.9 s for the 3 skill chunks; load ≈ 60 s; main GPU peak 26–32 GB. With compile, chunks 2–4 were 8.3 s.
