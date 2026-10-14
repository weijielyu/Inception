# Spike results (2026-10-09, 1× RTX 6000 Ada 48 GB, torch 2.11+cu128, no flash-attn → SDPA shim)

## Matrix-Game 2.0 (universal distilled, 640×352, 3 latent frames / block = 12 px frames)
- Load: 46 s (VRAM after load 6.1 GB). First `start()` (image encode + compile): 52 s.
- Blocks 0–6: 2.5–5 s/block (torch.compile warm-up of flex_attention / VAE decoder).
- Steady state (block ≥7): **0.89 s per 12-frame block ≈ 13.5 fps**, VRAM peak 13.9 GB.
- Keyboard: w/s/a/d one-hot [4]; mouse: [pitch, yaw] with ±0.1 per block. Horizon: 360 latents (~1437 px frames ≈ 90 s at 16 fps), then re-seed.
- Seed: real photo (desk with letters). See `logs/sheet_mg2.jpg`.

## Wan2.2 TI2V-5B (DiffSynth, 640×352, 65 frames, 25 steps)
- Load: 39–41 s. VRAM peak 25.6 GB.
- idle prompt: 45.4 s (0.70 s/frame incl. VAE warm-up); dig prompt: **35.2 s (0.54 s/frame)**.
- See `logs/sheet_wan_dig.jpg`, `logs/sheet_wan_idle.jpg`.

## Decisions
- Walk renderer = Matrix-Game 2.0 on one GPU (real-time budget met: 13.5 fps generated vs 16 fps display → display plays at generated pace / buffers).
- Clip renderer = Wan2.2 TI2V-5B on a second GPU; action clip ≈ 35 s at 25 steps; idle loop uses fewer steps (12) to stay ≈ 15–20 s.
- Both fit on the same 48 GB card if needed (14 + 26 GB), but separate cards avoid contention.
