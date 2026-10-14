# Systems engineering for a real-time AI-generated interactive video world: serving, latency, cost per player-hour, streaming, caching, and real-time audio

State as of 2026-10-09. All prices and latency claims are dated inline where the source gives a date; where a source is undated, the fetch date (Oct 2026) is noted. Everything below is sourced; derived numbers are kept in "Inferences" and labelled as such.

## Key Question 1: GPU inference economics (Oct 2026) and $/stream-hour for a real-time world model

### Takeaway
Neo-cloud on-demand H100s cost $2.60–4.30/GPU-hr, H200 $3.60–4.60, B200 $5.50–7.00, with hyperscalers 2–3x higher; a world-model stream that monopolizes one H100 therefore costs roughly $3–5 per player-hour in raw GPU before utilization overhead. The only public operator statement is Odyssey's "$1–2 per user-hour" (May 2025, H100 clusters); Decart's API prices its Oasis 3 world model at $0.02/s = $72/hr, i.e. the "pay-per-second API" route is ~20x more expensive than self-hosting.

### Cited Findings

**Cloud GPU prices (per GPU-hour, on-demand, USD)**
- Nodus (Oct 8, 2026, vendor-published, compared with Modal): B300 $6.943 / Modal $7.099; B200 $5.50 / $6.25; H200 SXM $3.593 / $4.54; H100 SXM $2.60 / $3.949; A100 80GB $1.09 / $2.498; L40S $0.793 / $1.951; L4 $0.43 / $0.799; RTX 5090 $0.48; RTX 4090 $0.29. Author is a Nodus founder (commercial interest). — [DEV Community, Oct 9 2026](https://dev.to/viswaretas_kotra/gpu-cloud-pricing-october-2026-what-an-h100-h200-b200-or-b300-costs-per-hour-5a25)
- Modal (fetched Oct 2026): per-second billing; B300 $0.001972/s (~$7.10/hr); B200 $0.001736/s (~$6.25/hr); H200 $0.001261/s (~$4.54/hr); H100 $0.001097/s (~$3.95/hr); A100-80GB ~$2.50/hr; L40S ~$1.95/hr; L4 ~$0.80/hr; T4 ~$0.59/hr. Region pinning costs 1.15–1.75x; non-preemptible execution costs 3x base; egress $0.04/GiB; containers start in ~1–2 s; idle timeout 60 s billed. — [Modal pricing](https://modal.com/pricing)
- Lambda (fetched Oct 2026): B200 SXM6 $6.69–6.99; H100 SXM $3.99–4.29; H100 PCIe $3.29; A100 80GB $2.79; GH200 $2.29; 1-Click Clusters (2 wk–1 yr): B200 $9.86→$8.87, H100 $6.16→$5.54 per GPU-hr. No H200/B300/GB200 listed. — [Lambda pricing](https://lambda.ai/pricing)
- RunPod (fetched Oct 2026, structured data): Community/Secure: H100 SXM $2.69/$3.49; H100 PCIe $1.99/$2.89; H200 SXM $3.59/$4.59; B200 $5.98/$6.79; B300 $6.94/$7.89; A100 SXM $1.39/$1.59; L40S $0.79/$1.09; RTX 5090 $0.69/$0.99; RTX 4090 $0.34/$0.74. Serverless (per hr): B300 $9.98, B200 $8.64, H200 $5.93, H100 $4.79, A100 $2.72, RTX 5090 $1.58, RTX 4090 $1.10. No MI300X listed. — [RunPod pricing](https://www.runpod.io/pricing)
- H200 provider sweep (as of Oct 1, 2026): Hyperbolic $3.99; Crusoe $4.29; Vast.ai $4.32 (median, range $3.59–5.09); DigitalOcean $4.47; Modal $4.54; RunPod $4.59; Nebius $5.40; CoreWeave $6.31; AWS $7.91; Oracle $10.00; Azure $10.60; Google Cloud $10.85. B200 range across clouds $5.99–16.11. — [Thunder Compute, Oct 2026](https://www.thundercompute.com/blog/nvidia-h200-pricing)
- CoreWeave H100: 8-GPU HGX node $49.24/hr = $6.16/GPU-hr, spot ~$2.46; 8-GPU minimum. Crusoe H100 $3.90/GPU-hr. Nebius H100 $3.85 on-demand (reviewed Sep 24, 2026), spot ~$2.15. CoreWeave B200 8-GPU node $68.80/hr = $8.60/GPU-hr. — [Spheron (CoreWeave vs Crusoe)](https://www.spheron.network/blog/coreweave-vs-crusoe-h100-and-b200-pricing-2026/); [Thunder Compute (CoreWeave vs Nebius)](https://www.thundercompute.com/blog/coreweave-vs-nebius); [CloudZero CoreWeave](https://www.cloudzero.com/blog/coreweave-pricing/)
- Together AI (July 2026): cluster on-demand HGX H100 $3.99, H200 $5.99, B200 $8.19/GPU-hr; dedicated endpoints H100 $5.49, B200 $8.99; H100 reserved floor $3.09 (91–180-day commit, cut June 2026). — [morphllm Together pricing](https://www.morphllm.com/together-ai-pricing); [usagepricing price-change record](https://usagepricing.com/blueprint/activity/together-ai-2026-06-30-price-change)
- fal.ai (fetched Oct 2026): H100 $4.50/hr list ("as low as" $2.49); H200 $6.00 ($2.99); B200 $7.99 ($5.49). — [fal pricing](https://fal.ai/pricing)
- Replicate (fetched Oct 2026): H100 $0.001525/s ($5.49/hr); A100-80GB $0.0014/s ($5.04/hr); L40S $0.000975/s ($3.51/hr); T4 $0.81/hr; private models billed for all online time incl. setup and idle. — [Replicate pricing](https://replicate.com/pricing)
- Baseten: H100 80GB $0.10833/min (~$6.50/hr); H100 MIG 40GB $0.0625/min; B200 $0.16633/min (~$9.98/hr); idle scale-to-zero replicas free; no published cold-start figures. — [Spheron Baseten pricing 2026](https://www.spheron.network/blog/baseten-pricing-2026-model-serving-cost/); [computeprices Baseten B200](https://computeprices.com/providers/baseten/gpus/b200)
- Hyperscalers: AWS p5 (8xH100) ≈ $6.88/GPU-hr; Azure up to $6.98; AWS B200 ≈ $14.24/GPU-hr on-demand, ~$9.36 capacity blocks; spot 55–65% cheaper (H100 ~$1.03, B200 ~$2.12 in one tracker, flagged as outlier). — [Spheron GPU cloud comparison 2026](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/); [effectstory](https://effectstory.com/en/articles/cloud-gpu-h100-b200-pricing-comparison-2026); [shattered.io](https://shattered.io/h100-h200-b200-cloud-gpu-pricing-2026/)
- Price volatility: one tracker reports an H100 SXM listing more than doubling from $1.50 to $3.19/hr between June and August 2026. — [jarvislabs H200 price](https://jarvislabs.ai/blog/h200-price)

**Operator statements on $ per user-hour**
- Odyssey (May 28, 2025): interactive video runs on "clusters of H100 GPUs in the US and EU", costs "$1–$2 per user-hour, depending on the video quality served", and "this cost is decreasing fast"; streams up to 30 FPS; input-to-frame loop as low as 40 ms; coherent for 5+ minutes; described as "raw, unstable". — [Odyssey, Introducing Interactive Video](https://odyssey.systems/introducing-interactive-video)
- Decart API (fetched Oct 2026): realtime models billed per second of active generation: Lucy 2.5 realtime $0.02/s (720p), fast mode $0.04/s; Lucy Restyle 2 $0.01/s; Oasis 3 Preview (world model / driving sim) $0.02/s with enterprise pricing on request; worked example: 60-s Oasis 3 session = $1.20. Offline video: Lucy 2.5 $0.04/s; Lucy Clip $0.15/s. No volume table published. — [Decart pricing](https://docs.platform.decart.ai/getting-started/pricing)
- Decart MirageLSD: 20 fps at 768x432, <40 ms per frame, tuned for Hopper with architecture-aware pruning and "shortcut distillation" (company claims 16x); hardware per stream not disclosed. — [The Decoder, Jul 2025](https://the-decoder.com/decart-launches-miragelsd-an-ai-model-that-transforms-live-video-feeds-in-real-time); [Crusoe blog](https://crusoe.ai/resources/blog/miragelsd-decarts-real-time-ai-video-model-is-now-available-on-crusoe-cloud)
- Google: Genie 3 is 720p/24 fps; Project Genie launched Jan 29 2026 to US Google AI Ultra subscribers ($249.99/mo) with sessions capped at 60 seconds "due to computational demands"; no per-user cost disclosed. — [DeepMind Genie 3 blog](https://deepmind.google/discover/blog/genie-3-a-new-frontier-for-world-models/); [AOL/Engadget on Project Genie](https://www.aol.com/articles/google-brings-genie-3-world-233137296.html); [ctol.digital](https://www.ctol.digital/news/google-genie-3-launch-high-stakes-ai-bet/)

**Non-GPU silicon**
- Oasis (Decart + Etched, Oct 31 2024): 20 fps, new frame every 0.04 s; page claims once Etched's Sohu ships, "models like Oasis could run in 4K", scale to 100B+ parameters and serve "more than 10x as many users"; no dollar figures. — [oasis-model.github.io](https://oasis-model.github.io/)
- Etched Sohu status: as of mid-2026 "no independent benchmarks exist, the chip hasn't shipped to customers"; first systems reported to ship summer 2026; fixed-function transformer-only. Headline claim: 8-chip server >500k tok/s on Llama 70B. — [fast.io Etched review 2026](https://www.fast.io/resources/etched-ai-review-2026.md); [Tom's Hardware, 2024](https://tomshardware.com/tech-industry/artificial-intelligence/sohu-ai-chip-claimed-to-run-models-20x-faster-and-cheaper-than-nvidia-h100-gpus)
- Groq / Cerebras / SambaNova: no source found making any real-time video-diffusion claim; all three are positioned on LLM inference. — [IntuitionLabs chip comparison](https://intuitionlabs.ai/articles/cerebras-vs-sambanova-vs-groq-ai-chips)

### Inferences
- Raw GPU cost per stream-hour at one H100 per stream: $2.60 (Nodus) to $4.29 (Lambda) on neo-clouds; $5.5–7 on hyperscalers; ~$1–2.5 on spot. At one B200 per stream: $5.5–7.0 (neo-cloud) to $8–14 (CoreWeave/AWS).
- Odyssey's $1–2/user-hour (May 2025) is below one-H100-per-user list prices, which implies either reserved/owned hardware, sub-1-GPU-per-user (batching or lower-quality tier), or both. It should be treated as a floor for a well-optimized small model, not a default.
- Decart's $0.02/s ($72/hr) for Oasis 3 Preview is ~20x the raw neo-cloud H100 rate; API-metered real-time world models are only viable for short sessions or demos until enterprise pricing is negotiated.
- Sohu/Groq/Cerebras/SambaNova should be excluded from a late-2026 feasibility plan; only NVIDIA (and possibly MI300X, for which no pricing was captured) is actionable.

### Gaps
- No GB200/GB300 or MI300X on-demand hourly prices were captured from primary pages (Lambda, RunPod, Nodus do not list them; CoreWeave/Nebius pages were not fetched directly).
- No public statement from Decart or Google on GPUs-per-stream or $ per user-hour for Mirage/Lucy/Genie beyond API list prices.
- No independent verification of any vendor latency or throughput claims.

## Key Question 2: Latency budget — what interactive video systems achieve, what players tolerate, and how to stream generated frames to a browser

### Takeaway
Shipping real-time generative systems converge on a ~40 ms per-frame generation budget (Decart Mirage <40 ms at 20 fps; Odyssey 40 ms loop at up to 30 fps; Oasis 0.04 s/frame; Genie 3 24 fps with no published latency), which, after NVENC (~3–6 ms encode on modern cards) and WebRTC transport, lands end-to-end around 100–200 ms — within the ~100 ms (action games) to ~150 ms (slower genres) thresholds from cloud-gaming research, but well above GeForce NOW's vendor-claimed ~30 ms. WebRTC is the production path; WebTransport+WebCodecs gives more control with comparable latency but no built-in jitter buffer.

### Cited Findings

**Latency achieved by generative systems**
- Decart MirageLSD: each frame processed in under 40 ms; 20 fps; 768x432; limited to a small window of prior frames. — [The Decoder](https://the-decoder.com/decart-launches-miragelsd-an-ai-model-that-transforms-live-video-feeds-in-real-time)
- Odyssey: "as little as 40 ms" input-to-frame; up to 30 FPS; H100 clusters in US and EU (regional placement). — [Odyssey](https://odyssey.systems/introducing-interactive-video)
- Oasis (Decart/Etched): 20 fps, new frame every 0.04 s. — [oasis-model.github.io](https://oasis-model.github.io/)
- Genie 3: 720p, 24 fps, "real time"; consistency "a few minutes", visual memory ~1 minute; limited action space; no latency figure published. — [DeepMind](https://deepmind.google/discover/blog/genie-3-a-new-frontier-for-world-models/)
- Self-Forcing (NeurIPS 2025 spotlight), 1.3B, 832x480, single H100: chunk-wise 17.0 fps with 0.69 s latency; frame-wise 8.9 fps with 0.45 s latency; 4 denoising steps; CausVid same 17 fps / 0.69 s; base Wan2.1 0.78 fps / 103 s. — [arXiv 2506.08009v2](https://arxiv.org/html/2506.08009v2)
- StreamDiffusionV2 (MLSys 2026): first frame within 0.5 s; 58.28 fps (14B) and 64.52 fps (1.3B) on four H100s without TensorRT/quantization; 31.62 fps (14B) at higher step count; 1–4 steps. — [arXiv 2511.07399](https://arxiv.org/abs/2511.07399v1)
- Krea Realtime 14B (Oct 20, 2025): 11 fps on a single B200 at 4 steps; first frames within ~1 s; Apache-2.0. — [HF model card](https://huggingface.co/krea/krea-realtime-video); [Krea blog](https://www.krea.ai/blog/krea-realtime-14b)
- Matrix-Game 2.0 (Aug 2025): 1.8B, 25 fps streaming; Matrix-Game 3.0 (Mar 27 2026): 5B on Wan2.2-TI2V-5B, "720p@40FPS", Apache-2.0, GPU unstated; 2x14B MoE variant without speed figures. — [Matrix-Game 2.0 arXiv](https://arxiv.org/abs/2508.13009v2); [Matrix-Game 3.0 HF](https://huggingface.co/Skywork/Matrix-Game-3.0); [GitHub](https://github.com/SkyworkAI/Matrix-Game)
- Hunyuan-GameCraft-2 reported at 16 fps (secondary source). — [alphaxiv overview](https://alphaxiv.org/overview/2511.23429v1)
- Project Genie consumer sessions capped at 60 s; 20–24 fps at 720p. — [itdaily](https://itdaily.com/news/cloud/google-launches-project-genie)

**Player latency tolerance (cloud gaming research)**
- Players begin to notice ~100 ms delay; subtracting ~20 ms playout/processing leaves ~80 ms as the network threshold where QoE is appreciably affected; ~100 ms recommended for action games, ~150 ms acceptable for slower-paced games; racing identified as the most latency-sensitive genre. — [U. Waterloo edge-cloud study](https://cs.uwaterloo.ca/~bernard/edgecloud)
- Open-internet FPS server: most players in 50–300 ms; players >400 ms much more likely to leave immediately. — [TU Darmstadt LWH+13](https://www.kom.tu-darmstadt.de/papers/LWH+13.pdf?download)
- WPI (2014, non-peer-reviewed): QoE ratings drop ~14% per 100 ms added latency, roughly linear. — [WPI OnLive study](https://web.cs.wpi.edu/~claypool/iqp/onlive/)
- Focus-group study (2020) at 0/150/300 ms identified nine game characteristics that modulate delay tolerance. — [arXiv 2004.05609](https://arxiv.org/pdf/2004.05609)
- CHI PLAY 2021 (n=96): at 180 ms simulated cloud latency, an input-predicting neural network significantly raised scores and hits. — [uni-regensburg](https://epub.uni-regensburg.de/54944/1/3474710.pdf)
- GeForce NOW Blackwell tier (Gamescom Aug 2025): RTX 5080-class, 5K@120 fps; NVIDIA claims ~30 ms end-to-end in Overwatch 2 at 360 fps mode vs 49 ms on PS5 Pro at 120 Hz; uses Reflex-based Low Latency Streaming, packet pacing, Cloud G-Sync, L4S. Vendor numbers; one reviewer measured 11–12 ms network RTT to NVIDIA's NJ datacenter. — [NVIDIA press release](https://investor.nvidia.com/news/press-release-details/2025/NVIDIA-Blackwell-Architecture-Comes-to-GeForce-NOW/default.aspx); [Tom's Guide](https://www.tomsguide.com/gaming/nvidia-geforce-now-gets-its-biggest-upgrade-in-years-rtx-5080-performance-5k-at-120-fps-with-dlss-4-and-more); [lon.tv review](https://blog.lon.tv/?p=4346)

**Encoding (NVENC)**
- Parsec session telemetry: median NVENC H.264 encode latency 5.8 ms vs 15.06 ms on AMD VCE (older post). — [Parsec blog](https://parsec.app/blog/nvidia-nvenc-outperforms-amd-vce-on-h-264-encoding-latency-in-parsec-co-op-sessions-713b9e1e048a)
- Developer reports: ~3 ms for 1920x1200 H.264 on GTX 1050 Ti (Media Foundation); ~23 ms per 4K60 HEVC frame on Jetson. — [NVIDIA forum (MFT)](https://forums.developer.nvidia.com/t/nvenc-h-264-encoder-mft-latency-increases-when-framerate-is-limited/63930); [NVIDIA forum (H265)](https://forums.developer.nvidia.com/t/how-to-lower-latency-on-nvenc-h265/347218)
- 2026 longitudinal NVENC study (Pascal→Blackwell): standard HQ mode holds a 7-frame (~117 ms) end-to-end baseline; UHQ tuning violates cloud-gaming motion-to-photon thresholds (HEVC P1 20 frames, AV1 P1 38 frames). — [arXiv 2605.01187](https://arxiv.org/pdf/2605.01187)

**Transport to browser**
- MSE is "biased more towards providing smooth playback instead of low latency" (W3C, 2015). — [W3C bug 28379](https://www.w3.org/Bugs/Public/show_bug.cgi?id=28379)
- WebRTC playback is handled by the browser stack with limited codec/buffer control; WebTransport pairs with WebCodecs to ship raw H.264/HEVC/AV1/Opus frames you encoded yourself but has no built-in jitter buffer and no P2P. — [videosdk WebRTC vs WebTransport](https://www.videosdk.live/developer-hub/webtransport/webrtc-vs-webtransport); [forasoft](https://www.forasoft.com/learn/video-streaming/articles-streaming/webtransport-whip)
- Fraunhofer FOKUS (Unity remote rendering): WebTransport/HTTP3 achieve latency comparable to WebRTC with less configuration overhead in client-server setups. — [Fraunhofer publica](https://publica.fraunhofer.de/handle/publica/487765)
- Measured glass-to-glass on a WebRTC robotics pipeline: 150–180 ms total, of which camera+USB ~100 ms and WebRTC itself ~10 ms. — [Transitive Robotics](https://discourse.openrobotics.org/t/where-does-latency-in-webrtc-video-streaming-come-from-an-analysis/54566)
- LiveKit: every subscriber uses a jitter buffer; offers playout-delay hints and a "zero jitter buffer" mode (Rust SDK only); "sub-100ms" is marketing copy without methodology. — [LiveKit low-latency docs](https://docs.livekit.io/robotics/media/performance/low-latency/); [zero-jitter](https://docs.livekit.io/robotics/media/performance/low-latency/zero-jitter/)
- LiveKit Cloud pricing (third-party trackers, 2026): Build free (5,000 participant-min, 1,000 agent-min, 50 GB egress); Ship $50/mo (150k participant-min, overage $0.0005/min); Scale $500/mo (~1.5M min, ~$0.0004/min); agent minutes ~$0.01/min extra. — [trtc.io LiveKit pricing 2026](https://trtc.io/blog/details/livekit-pricing-2026); [dailyaifixs](https://dailyaifixs.com/blog/livekit-pricing-2026-the-agent-minute-catch)
- Cloudflare Realtime SFU/TURN: $0.05/GB egress, first 1,000 GB/month free, ingress free. — [Cloudflare pricing](https://developers.cloudflare.com/realtime/sfu/platform/pricing/)
- fal realtime: WebSocket inference with "sub-100ms image generation" claim; 2023 measurements: LCM SD1.5 ~150 ms/image, 355 ms end-to-end with 120 ms GPU time; 3–5 fps over WebSockets; msgpack binary protocol; recommends 512x512 and base64 payloads. — [fal docs real-time](https://docs.fal.ai/documentation/model-apis/inference/real-time); [fal blog 2023](https://blog.fal.ai/building-applications-with-real-time-stable-diffusion-apis/)

### Inferences
- Budget for a 24–30 fps world model: ~35–40 ms generation + ~3–6 ms NVENC + ~10–20 ms WebRTC packetization/jitter + ~20–40 ms network RTT (regional PoP) + ~10–20 ms decode/display ≈ 80–130 ms motion-to-photon. That meets the 100–150 ms research threshold for non-twitch gameplay but not the GeForce NOW-class 30–50 ms bar.
- Self-Forcing-class open models at 0.45–0.69 s latency per chunk are too slow for action-conditioned gameplay; they are fine for "slow exploration" and for pre-rolling clips. Only the vendor systems (Decart, Odyssey) and Matrix-Game 3.0 (if its 40 fps holds on a single GPU) claim per-frame budgets below 50 ms.
- Egress: 720p30 at ~5 Mbps ≈ 2.25 GB/stream-hour → ~$0.11/hr at Cloudflare $0.05/GB or ~$0.09/hr at Modal $0.04/GiB; SFU participant-minutes add ~$0.02–0.03/hr on LiveKit. Transport is <5% of GPU cost.
- Default stack: generate → NVENC H.264/AV1 in-loop on the same GPU → WebRTC (Pion/LiveKit self-hosted, or Cloudflare SFU) with playout-delay hint 0. Consider WebTransport+WebCodecs only if you need custom frame dropping or a browser-side jitter policy.

### Gaps
- No published motion-to-photon measurement for any generative interactive system (Decart, Odyssey, Genie); the ~40 ms figures are per-frame generation only.
- No benchmark comparing WebRTC vs WebTransport vs MSE on identical hardware for synthesized frames.
- No recent encode-only NVENC latency benchmark for Hopper/Blackwell at 720p/1080p.

## Key Question 3: Serving stacks for diffusion/video models and serverless GPU platforms

### Takeaway
The open real-time stack in Oct 2026 is: an autoregressive few-step distilled DiT (Self-Forcing / Matrix-Game 3.0 / Krea Realtime / StreamDiffusionV2) + FP8/INT8 + torch.compile/SageAttention + sequence/pipeline parallelism across 2–4 GPUs; training-free caches (TeaCache up to 4.41x, MagCache 2.1–2.7x, Sparse VideoGen ~2.3x) are complementary but apply to multi-step clip generation, not to 1–4-step streaming. NVFP4/SVDQuant (Nunchaku) is proven on image DiTs (3x over BF16 on Blackwell) but has no published video numbers.

### Cited Findings
- TeaCache (CVPR 2025): training-free timestep-embedding-aware cache; up to 4.41x on Open-Sora-Plan with -0.07% VBench. — [arXiv 2411.19108](https://arxiv.org/abs/2411.19108)
- MagCache (NeurIPS 2025): 2.10–2.68x on Open-Sora, CogVideoX, Wan 2.1, HunyuanVideo; calibrates from a single sample (vs dozens for TeaCache); ~0.5 GB extra memory on Wan 2.1 (secondary summary). — [arXiv 2506.09045](https://arxiv.org/pdf/2506.09045); [alphaxiv overview](https://www.alphaxiv.org/overview/2506.09045)
- Sparse VideoGen (Feb 2025): training-free sparse attention; up to 2.28x on CogVideoX-v1.5 and 2.33x on HunyuanVideo end-to-end. — [arXiv 2502.01776](https://arxiv.org/abs/2502.01776)
- SVDQuant/Nunchaku: NVFP4 on Blackwell gives ~3x over BF16 on FLUX with better quality than INT4; RTX 5090 NVFP4 3.1x vs W4A16; no published video-DiT numbers. Other video quantization: DVD-Quant ~2x on HunyuanVideo; DMPQ (2026) NVFP4+INT8 on CogVideoX 1.92x speed, 3.32x memory reduction. — [MIT Han Lab SVDQuant NVFP4](https://hanlab.mit.edu/blog/svdquant-nvfp4); [arXiv 2411.05007](https://arxiv.org/html/2411.05007v3); [DMPQ arXiv 2603.18742](https://arxiv.org/html/2603.18742v1); [DVD-Quant](https://sotaverified.org/papers/dvd-quant-data-free-video-diffusion)
- xDiT (xfuser): unified sequence parallel = DeepSpeed-Ulysses + Ring attention (2D mesh), plus PipeFusion, data and CFG parallel; PipeFusion not supported for video models; one third-party paper found xDiT-Ring gave "little to no speedup" for video in their setup due to communication overhead; Google Vertex ships an xDiT container with CogVideoX-2b and Wan2.1. FastUSP reports only 1.09–1.16x end-to-end improvement over USP on FLUX/Qwen-Image. — [xDiT GitHub](https://github.com/xdit-project/xdit); [Google Cloud xDiT docs](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/open-models/xdit); [arXiv 2505.14741](https://arxiv.org/pdf/2505.14741); [FastUSP arXiv 2602.10940](https://arxiv.org/pdf/2602.10940)
- StreamDiffusionV2: pipeline-parallel across denoising steps and layers with "near-linear FPS scaling" on 4 H100; supports 1–4 steps; no TensorRT/quantization needed for 58 fps (14B). Livepeer's Scope benchmark says H100 SXM is the best "default" and H200 SXM is ~5–15% faster for real-time pipelines. — [arXiv 2511.07399](https://arxiv.org/abs/2511.07399v1); [Livepeer Scope GPU benchmark](https://livepeer.notion.site/Scope-GPU-Benchmark-Report-2dc0a34856878012b257d8a1702833a9)
- Krea Realtime recommended path: H100 + torch.compile + SageAttention + FP8; 14B F16 weights; Apache-2.0. — [HF card](https://huggingface.co/krea/krea-realtime-video)
- Matrix-Game 3.0 runtime: Python 3.12, FlashAttention, torchrun multi-GPU with optional FSDP, `--use_int8`, `--compile_vae`, async VAE for multi-GPU. — [HF card](https://huggingface.co/Skywork/Matrix-Game-3.0)
- NVIDIA Cosmos: Predict2 14B Video2World clip generation ~33–62 s on B200 vs ~79–176 s on H100 NVL; Transfer2.5-2B 720p/16fps/5-s clip ~286 s (B200), ~719 s (H100 NVL), ~870 s (H100 PCIe), 65.4 GB VRAM; NIM offers "latency" (context-parallel) and "throughput" (replicated) profiles incl. B200/GB200. Not real-time. — [NVIDIA Predict2 model matrix](https://docs.nvidia.com/cosmos/latest/predict2/model_matrix.html); [Transfer2.5 matrix](https://docs.nvidia.com/cosmos/latest/transfer2.5/model_matrix.html); [NIM Cosmos support matrix](https://docs.nvidia.com/nim/cosmos/latest/support-matrix.html)
- Serverless platform economics: Modal $3.95/hr H100 per-second, 1–2 s container spin-up (model load billed); Replicate $5.49/hr, idle billed for private models; Baseten ~$6.50/hr per-minute; RunPod serverless $4.79/hr (or $0.00053/s ≈ $1.91/hr on one listing) and cold-start seconds are billed; fal H100 $4.50 list. Break-even vs dedicated hourly GPU ≈ 70–75% utilization. — [Modal](https://modal.com/pricing); [Replicate](https://replicate.com/pricing); [Spheron Baseten](https://www.spheron.network/blog/baseten-pricing-2026-model-serving-cost/); [gpuperhour serverless](https://gpuperhour.com/blog/serverless-gpu-pricing); [premai serverless list](https://www.premai.io/blog/9-best-serverless-gpu-providers-for-llm-inference-2026/)
- fal.ai real-time: persistent WebSocket skips the queue and keeps a warm runner; first connection may still cold-start. — [fal real-time docs](https://docs.fal.ai/documentation/model-apis/inference/real-time)
- Decart's "Lucy" line: Lucy 2.5 (realtime 30 fps, sub-40 ms per third-party guides), Lucy Restyle 2, Lucy VTON, Oasis 3 preview; Lucy-5B image-to-video on fal at $0.15/video. — [Decart pricing](https://docs.platform.decart.ai/getting-started/pricing); [fal Lucy-5B](https://fal.ai/models/fal-ai/decart/lucy-5b/image-to-video/llms.txt); [aireiter Lucy 2.5 guide](https://aireiter.com/it/blog/lucy-2-5-realtime-video-guide)

### Inferences
- Production-ready today: Self-Forcing / CausVid-style AR distillation (open code, NeurIPS), Krea Realtime 14B (Apache-2.0), Matrix-Game 3.0 (Apache-2.0, MIT code), StreamDiffusionV2 (MLSys 2026, open), TeaCache/MagCache (drop-in for clip generation), xDiT (Google ships it), torch.compile + FP8, Modal/RunPod/fal for serving. Research-only or unproven for video: NVFP4/Nunchaku on video DiTs, FastUSP, Cosmos as a real-time engine, Etched Sohu.
- Per-GPU throughput for a self-hosted world model (Oct 2026): ~17 fps/H100 for a 1.3B AR model (Self-Forcing), ~40 fps claimed for a 5B model (Matrix-Game 3.0, GPU unstated), ~11 fps/B200 for 14B (Krea), ~58 fps for 14B on 4 H100 (StreamDiffusionV2 ≈ 14.5 fps per H100-equivalent). Rule of thumb: one 1–5B stream per H100 at 20–40 fps; a 14B stream needs ~2–4 H100 (or B200) to reach 24+ fps.
- Serverless per-second billing makes sense for the bursty, sub-minute pieces (scene bootstrap, event clips, SFX); for continuous per-player streams at >70% utilization, dedicated hourly GPUs (Nodus/RunPod/Nebius/Lambda) are cheaper by 1.5–2.5x.

### Gaps
- No published cold-start times for 14B video models on Modal/Baseten/Replicate (expect tens of seconds to minutes to load 28 GB of weights; unverified).
- No Nunchaku/NVFP4 benchmarks for Wan/Hunyuan video DiTs.
- Matrix-Game 3.0's 40 fps benchmark GPU and whether it is a single GPU are not stated.

## Key Question 4: Hybrid architectures that cut cost (interpolation, super-resolution, 3D-once-render-cheap, V2V stylization, speculative pre-generation)

### Takeaway
The cheapest robust design is "generate a 3D scene once (Gaussian splats in ~1 min via Marble or seconds via VGGT/DA3), render it on the client or on a $0.4–0.8/hr L4, and invoke video generation only for events"; real-time V2V stylization of that render is available today (Decart Lucy Restyle at $0.01/s, or self-hosted StreamDiffusionV2/Self-Forcing). Frame interpolation (RIFE) is real-time at 1080p on mid-range GPUs, but Real-ESRGAN-class super-resolution to 4K is ~2 fps on an L40S and is not real-time. No paper on speculative generation of game/video branches was found; the closest is HAS branched-video prefetching (ACM MM 2014).

### Cited Findings
- RIFE: 4–27x faster than SuperSlomo/DAIN; SVP's estimated real-time table: RTX 3060+ with TensorRT for 1080p at 60–72 fps, RTX 4080+ for 4K at 48 fps; TensorRT up to 2x faster than ncnn/Vulkan but with long engine build. — [RIFE arXiv 2011.06294](https://ar5iv.labs.arxiv.org/html/2011.06294); [SVP RIFE wiki](https://svp-team.com/wiki/RIFE_AI_interpolation)
- Real-ESRGAN x4 via TensorRT FP16 on an L40S: 960x540→3840x2160 at 2 fps; 512→2048 at 5 fps; ~3–4x faster than non-TensorRT. — [ComfyUI-Upscaler-TensorRT](https://github.com/yuvraj108c/ComfyUI-Upscaler-Tensorrt)
- World Labs Marble: "Draft" tier builds a navigable 3D Gaussian-splat world in about a minute; higher tiers slower; mesh export much slower. — [Scenario Marble essentials](https://help.scenario.com/articles/4774055514-marble-by-world-labs-the-essentials); [UploadVR](https://www.uploadvr.com/marble-turns-an-image-into-a-webxr-volumetric-scene-in-minutes/)
- VGGT (Meta/Oxford): feed-forward; ~0.04 s for 1 frame, ~0.14 s for 10, ~8.75 s for 200 on one H100 (Flash Attention 3). — [VGGT arXiv](https://arxiv.org/html/2503.11651v1); [GitHub](https://github.com/N9nGe/VGGT)
- Depth Anything 3 (Nov 14 2025; DA3-Streaming Dec 11 2025): predicts depth, confidence, camera intrinsics/extrinsics and 3D Gaussian Splats (gsplat), exports ply/glb/3DGS video; streaming inference under 12 GB; Apache-2.0 for Small/Base/Metric/Mono-Large, CC BY-NC 4.0 for Large/Giant/Nested; no official timing. — [DA3 GitHub](https://github.com/ByteDance-Seed/Depth-Anything-3)
- One2Scene (Feb 2026): single image → explorable 3D scene; six-view scaffold in 0.5 s on an H20. — [arXiv 2602.19766](https://arxiv.org/pdf/2602.19766)
- WorldGen (Nov 2025): text → traversable, interactive 3D worlds. — [arXiv 2511.16825](https://arxiv.org/pdf/2511.16825)
- Browser splat rendering: WebSplatter (Feb 2026) WebGPU viewer 1.2–4.5x faster than SOTA web viewers via opacity-aware culling; Visionary (Dec 2025) WebGPU platform with per-frame ONNX; sorting is the dominant cost; no absolute 1080p fps in snippets. — [WebSplatter arXiv](https://arxiv.org/html/2602.03207v1); [Visionary](https://arxiv.org/abs/2512.08478v1)
- V2V stylization: Decart Lucy Restyle 2 realtime $0.01/s; Lucy 2.5 realtime $0.02/s. — [Decart pricing](https://docs.platform.decart.ai/getting-started/pricing)
- Runway Aleph (V2V) API: 28 credits/s at $0.01/credit ≈ $0.28/s, 56-credit minimum (reseller-reported). — [Atlas Cloud](https://www.atlascloud.ai/blog/tips/runway-aleph)
- Wan 2.2 VACE (Fun): offline ComfyUI workflows with pose/depth/canny/trajectory control; some variants need ~60 GB VRAM; no evidence of real-time use. — [stablediffusiontutorials](https://www.stablediffusiontutorials.com/2025/09/wan2.2-vace-fun.html); [Scenario Wan 2.2 VACE](https://help.scenario.com/articles/8905028295-wan-2-2-vace-the-essentials)
- MirageLSD is itself live video-to-video (camera feed → stylized stream at 20 fps). — [The Decoder](https://the-decoder.com/decart-launches-miragelsd-an-ai-model-that-transforms-live-video-feeds-in-real-time)
- Speculative prefetch: "Quality-adaptive Prefetching for Interactive Branched Video using HTTP-based Adaptive Streaming" (ACM MM 2014) prefetches alternative branch chunks so users can defer choices to the last moment; follow-up "Bandwidth-aware Prefetching for Proactive Multi-video Preloading" (ACM MM 2015). Google patents US8341245/US8762490 attach navigation likelihoods to links to gate speculative prefetch. — [LiU mm14](https://www.ida.liu.se/~nikca89/papers/mm14.html); [US8762490](https://patents.google.com/patent/US8762490)
- Input prediction mitigates latency: ANN predicting player inputs at 180 ms latency improved scores (CHI PLAY 2021). — [uni-regensburg](https://epub.uni-regensburg.de/54944/1/3474710.pdf)

### Inferences
- Keyframe + interpolation: generating at 12–15 fps and RIFE-interpolating to 24–30 fps roughly halves world-model GPU cost per stream (e.g., a 17-fps Self-Forcing stream could run two users per H100 at ~8.5 fps each + 2–3x interpolation), at the cost of ~1 extra frame of latency (≈40–80 ms) because interpolation needs the next keyframe. Viable for exploration, not for twitch input.
- Low-res + SR: generating at 432–540p and upscaling 2x with a light ESRGAN/NVIDIA VSR-class model is plausible in-loop (the 4x-to-4K path is not); treat 2x real-time SR as "needs benchmarking", since no published real-time figure was found.
- 3D-once: scene bootstrap costs ~1–5 min of GPU ($0.07–0.35 at H100 rates) or a Marble call; afterwards per-player cost is a splat renderer (client WebGPU = $0; server L4 at $0.43–0.80/hr shared by several streams) plus NVENC. Event clips via commercial APIs at $0.05–0.10/s (Veo Lite/Fast) or self-hosted Wan/LTX.
- Speculative branch pre-generation: no literature on generative branch prediction; borrow the HAS branched-video policies (prefetch top-k branches weighted by estimated choice probability, budgeted by bandwidth/GPU). Cost multiplies by expected branching factor k minus cache hits; this only pays off if branches are shareable across players.

### Gaps
- No real-time (24+ fps) super-resolution benchmark for 720p→1080p/4K on current GPUs.
- No published 1080p fps for WebGPU splat viewers on consumer hardware (3DGS papers' numbers were not fetched).
- No paper found on speculative/predictive pre-generation of generative video branches for games.

## Key Question 5: Real-time audio — TTS, sound effects, video-to-audio, adaptive music (latency, pricing, licenses)

### Takeaway
Voice is solved: ElevenLabs Flash (~75 ms model latency, $40/1M chars), Cartesia Sonic (~80–90 ms, $38–65/1M chars), Kokoro (Apache-2.0, ~45–60 ms first chunk on a GPU), Gemini Live audio ($0.018/min out). Sound effects are near-real-time with Stable Audio 3.0 Small (0.44 s on H200, open weights under $1M revenue) or ElevenLabs SFX ($0.12/min). Video-to-audio (MMAudio 1.23 s per 8-s clip, CC-BY-NC weights; HunyuanVideo-Foley; ThinkSound) works for clips, not per-frame. Adaptive music has exactly one real-time API, Google Lyria RealTime (experimental, WebSocket, 48 kHz PCM, BPM/density/brightness/scale controls, watermarked, no published price), versus clip-based Lyria 3.5 ($0.08/song) or ElevenLabs Music ($0.15/min).

### Cited Findings

**TTS**
- ElevenLabs API (fetched Oct 2026): v4 $0.022/1K chars promo (list $0.08) → $22/1M; v4 Turbo $0.011/1K promo (list $0.04); v3 $0.08/1K; v3 Conversational $0.04/1K; v2 Multilingual $0.08/1K; Flash/Turbo $0.04/1K ($40/1M). Flash latency ~75 ms (model only, excl. network). Speech Engine (conversational) $0.08/min, $0.16/min overage. — [ElevenLabs API pricing](https://elevenlabs.io/pricing/api); [ElevenLabs latency docs](https://elevenlabs.io/docs/eleven-api/guides/how-to/best-practices/latency-optimization)
- Cartesia (fetched Oct 2026): Free 20K credits; Pro $5 (100K); Startup $49 (1.25M, overage $45/1M); Scale $299 (8M, $38/1M); 1 credit = 1 char; Managed Agents $0.06/min; no ms claims on the pricing page. Third-party: Sonic Turbo ~80 ms, Sonic 2 ~90 ms TTFB, a third-party measurement of 166–190 ms; Sonic 2 deprecated June 1 2026, Sonic 3.5 current. — [Cartesia pricing](https://cartesia.ai/pricing); [futureagi comparison](https://futureagi.com/blog/elevenlabs-vs-cartesia-tts-2026/); [invideo TTS pricing Aug 2026](https://invideo.io/blog/ai-voice-model-pricing/)
- OpenAI Realtime: billed per audio token; third-party conversions ≈ $0.019/min in, $0.077/min out (flagship), $0.006/$0.024 (mini); cached audio input $0.40/1M. — [forasoft](https://www.forasoft.com/blog/article/openai-realtime-api-pricing); [eesel](https://www.eesel.ai/en/blog/gpt-realtime-mini-pricing)
- Google Gemini Live (fetched Oct 2026): Gemini 3.8 Live / 3.1 Flash Live: audio in $3.00/1M tokens ≈ $0.005/min, audio out $12.00/1M ≈ $0.018/min (25 tokens/s); Gemini 3.8 Flash TTS $9/1M output tokens ($0.00225 per 10 s; doubles Jan 1 2027); Flash-Lite TTS $6/1M. — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)
- Kokoro-82M: Apache-2.0; ~45 ms first audio chunk on RTX 5090 (hosting vendor), sub-60 ms TTFC via fastkokoro ONNX, <50 ms with TensorRT; older FastAPI README ~300 ms; no voice cloning. — [Kokoro GitHub mirror](https://github.com/captivus/Kokoro-82M); [gigagpu](https://gigagpu.com/?p=1841); [fastkokoro](https://pypi.org/project/fastkokoro/0.6.2/)
- Chatterbox (Resemble): MIT; Turbo 350M claims sub-200 ms and up to 6x real-time; one RTX 4090 measurement 472 ms first chunk. — [Resemble Chatterbox](https://resemble.ai/chatterbox); [Medium measurement](https://medium.com/@vinodpolinati/chatterbox-the-leading-family-of-open-source-ai-voice-models-thats-changing-the-game-150991d5cf8d)

**Sound effects**
- ElevenLabs Sound Effects: $0.12 per minute of output (FAQ says billed per generation — conflict); Music $0.15/min, 5-min cap. — [ElevenLabs API pricing](https://elevenlabs.io/pricing/api)
- Stable Audio 3.0 (May 20 2026): Small SFX 459M, Small 459M, Medium 1.4B open weights under Stability AI Community License (free commercial use under $1M annual revenue; enterprise license above); Large 2.7B closed; Small: 0.44 s inference on H200; Medium 1.31 s; up to 2 min (Small) / 6:20 (Medium); API via Stability and fal. — [The Decoder](https://the-decoder.com/stability-ai-launches-stable-audio-3-0-with-up-to-six-minute-tracks-and-open-weights/); [Digital Music News](https://www.digitalmusicnews.com/2026/05/21/stability-ai-3-0-release/)
- Stable Audio Open 1.0: Stability AI Community License (non-commercial + commercial under $1M revenue). — [HF card](https://huggingface.co/stabilityai/stable-audio-open-1.0); [Stability research page](https://stability.ai/news/stable-audio-open-research-paper)

**Video-to-audio**
- MMAudio (CVPR 2025): 157M params; 1.23 s to generate an 8-s clip (GPU unspecified); ~6 GB VRAM in 16-bit; code MIT, checkpoints CC-BY-NC 4.0, "do not guarantee ... suitable for commercial use". — [arXiv 2412.15322](https://arxiv.org/abs/2412.15322); [GitHub](https://github.com/hkchengrex/MMAudio)
- HunyuanVideo-Foley (Aug 2025): 48 kHz output, self-developed audio VAE, best scores on FD/KL/DeSync vs MMAudio and ThinkSound; no runtime published. — [arXiv 2508.16930](https://arxiv.org/html/2508.16930v1); [GitHub](https://github.com/Tencent-Hunyuan/HunyuanVideo-Foley)
- Native audio in video models: Veo 3.1 (audio always on; $0.05–0.60/s), Kling (native since 2.6), Hailuo H3 (native stereo), LTX-2/2.3/2.5 (synchronized audio, 4K/50 fps, open weights under LTX-2 Community License free under $10M ARR). — [invideo video pricing Aug 2026](https://invideo.io/blog/ai-video-model-pricing); [opensourceforu LTX-2](https://www.opensourceforu.com/2026/01/ltx-2-from-lightricks-delivers-native-4k-audio-video-with-fully-open-weights/); [invideo LTX guide](https://invideo.io/blog/ltx-ai-video-generator/)

**Music**
- Lyria RealTime (`models/lyria-realtime-exp`): experimental; persistent bidirectional WebSocket; 16-bit PCM stereo, spec says 48 kHz (JS sample uses 44.1 kHz); controls: guidance 0–6, bpm 60–200, density 0–1, brightness 0–1, scale enum, mute_bass/mute_drums/only_bass_and_drums, mode QUALITY/DIVERSITY/VOCALIZATION, temperature, top_k, seed; bpm/scale changes need reset_context(); instrumental-only; prompts safety-filtered; output always watermarked; clients must implement robust buffering for "variation in generation latency"; no latency figure; pricing not on the page. — [Google AI Lyria RealTime docs](https://ai.google.dev/gemini-api/docs/realtime-music-generation); [Magenta Lyria RealTime](https://magenta.tensorflow.org/lyria-realtime)
- Lyria 3.5 full song $0.08; Lyria 3 Pro Preview $0.08/song; Lyria 3 Clip Preview $0.04 per 30 s; not on free tier; REST single-turn, MP3/WAV 44.1 kHz. — [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing); [Lyria 3 docs](https://ai.google.dev/gemini-api/docs/music-generation)
- No source found for Suno/Udio real-time or official API pricing in this research (not retrieved).

### Inferences
- Audio budget per player-hour (continuous ambience + occasional dialogue/SFX): self-hosted Kokoro + Stable Audio 3.0 Small on a shared L4/L40S fraction ≈ $0.05–0.20; API route: Gemini Live audio out ≈ $1.08/hr if speaking continuously (realistically 10–20% duty → $0.10–0.25), ElevenLabs Flash at ~1,000 chars/min of dialogue at 15% duty ≈ $0.36/hr, SFX at 5 min/hr ≈ $0.60/hr, ElevenLabs Music continuous ≈ $9/hr (avoid) vs Lyria 3.5 regenerated every ~3 min ≈ $1.60/hr vs Lyria RealTime (unknown).
- Latency fit: TTS (75–100 ms TTFB) and Stable Audio 3.0 Small (0.44 s) fit an event-driven game loop if SFX are triggered ~0.5 s ahead or pre-generated per event type and cached. Per-frame V2A (MMAudio at 1.23 s/8 s ≈ 0.15 real-time factor) is batchable for 2–4-s chunks with ~1–2 s lag, i.e. only for non-synchronous ambience.
- Licenses: commercially clean open stack = Kokoro (Apache-2.0), Chatterbox (MIT, verify repo LICENSE), Stable Audio 3.0 open weights (<$1M revenue), Matrix-Game 3.0 (Apache-2.0), Krea Realtime (Apache-2.0), LTX-2.x (<$10M ARR). Not commercially clean: MMAudio checkpoints (CC-BY-NC), DA3 Large/Giant (CC-BY-NC).

### Gaps
- Lyria RealTime: no latency, pricing, or rate-limit figures published; experimental status means it cannot be relied on for production.
- No runtime numbers for HunyuanVideo-Foley or ThinkSound; no NVIDIA-GPU timing for MMAudio beyond the paper's unspecified-GPU figure.
- Suno/Udio API status and pricing not researched; FMOD/Wwise AI hooks not researched.
- ElevenLabs SFX latency not published.

## Key Question 6: Image-to-scene bootstrap from a user photo/video

### Takeaway
A user photo can become a persistent splat scene in seconds (VGGT 0.04 s/frame; DA3 outputs Gaussians directly; One2Scene 0.5 s scaffold) for geometry-only "look around" worlds, or in ~1–5 minutes via Marble for a fuller explorable world; image-conditioned world models (Matrix-Game 3.0, Genie 3, Odyssey) take the same image as a start frame with no bootstrap step but no persistent geometry.

### Cited Findings
- VGGT: ~0.04 s (1 frame), ~0.14 s (10), ~8.75 s (200) on one H100; zero-shot single-view 3D. — [VGGT GitHub](https://github.com/N9nGe/VGGT)
- Depth Anything 3: depth + pose + 3D Gaussian prediction from any number of views; DA3-Streaming <12 GB; Apache-2.0 for small/base/metric/mono, CC-BY-NC for Large/Giant. — [DA3 GitHub](https://github.com/ByteDance-Seed/Depth-Anything-3)
- One2Scene: 0.5 s six-view scaffold on H20. — [arXiv 2602.19766](https://arxiv.org/pdf/2602.19766)
- Marble Draft ~1 min; other reports 2–5 min for fuller worlds. — [Scenario](https://help.scenario.com/articles/4774055514-marble-by-world-labs-the-essentials); [Medium Isaac Sim guide](https://medium.com/@geedhpruthvi/from-imagination-to-simulation-a-complete-guide-to-importing-world-labs-marble-models-into-nvidia-69dde0ed5d6e)
- Image-conditioned world models: Matrix-Game 3.0 generates from an input image with camera-aware memory "over minute-long sequence"; Genie 3 visual memory ~1 min, consistency "a few minutes"; Odyssey coherent 5+ min on narrow post-training distribution. — [Matrix-Game 3.0 HF](https://huggingface.co/Skywork/Matrix-Game-3.0); [DeepMind](https://deepmind.google/discover/blog/genie-3-a-new-frontier-for-world-models/); [Odyssey](https://odyssey.systems/introducing-interactive-video)

### Inferences
- Bootstrap cost per uploaded photo: VGGT/DA3 path ≈ <1 s GPU (<$0.01); Marble ≈ 1–5 min wall-clock (pricing not captured). For a video upload of N frames, VGGT scales roughly linearly (200 frames ≈ 9 s on H100).
- A single photo only yields a front-facing shell; occluded regions must be hallucinated (One2Scene/WorldGen/Marble-style generative completion), which is where most of the bootstrap time goes.

### Gaps
- No official DA3 or MoGe timing figures; no Marble API pricing captured.

## Key Question 7: Content safety and rights

### Takeaway
Frame-level moderation of a live generated stream is affordable only at low sampling rates: Sightengine ($0.0015–0.002/op; 1 fps ≈ $5.40–7.20/stream-hour, 0.1 fps ≈ $0.55–0.72), Hive ($3/1,000 image requests ≈ $10.80/hr at 1 fps; video rates by quote), AWS Rekognition ($0.001/image ≈ $3.60/hr at 1 fps; $0.10/min stored video). The NO FAKES Act (S.4591) cleared Senate Judiciary June 18 2026 but a Sept 30 floor attempt was blocked, so likeness rights for user-uploaded photos remain a state-law patchwork plus your own ToS.

### Cited Findings
- Sightengine: 1 operation = 1 model x 1 frame; default sampling 1 fps (pricing page) or 1 frame/2 s (FAQ, conflict); Free 2,000 ops/mo; Starter $29 for 10k + $0.002/op; Growth $99 for 40k; Pro $399 for 200k + $0.0015/op, 5 simultaneous streams; live-stream results via per-frame callbacks; no latency figure published. — [Sightengine pricing](https://sightengine.com/pricing); [what is an operation](https://sightengine.com/faq/what-is-an-operation); [live stream guide](https://www.sightengine.com/docs/live-stream-video-moderation-guide)
- Hive (fetched Oct 2026): Visual Moderation $3.00/1,000 requests, 100 req/day default limit; video "special video rates" by contact; Text $0.50/1,000; Audio $0.03/min; OCR video $0.13/min; $50 free credits; "low-latency" claimed, no figure. — [Hive pricing](https://thehive.ai/pricing)
- AWS Rekognition: DetectModerationLabels $0.0010/image (first 1M), $0.0008 (next 4M), $0.0006 (next 30M); stored video content moderation $0.10/min; no streaming moderation rate listed. — [AWS Rekognition pricing](https://aws.amazon.com/rekognition/pricing/)
- Lyria RealTime filters prompts and watermarks all output; Genie/Veo not covered here. — [Lyria RealTime docs](https://ai.google.dev/gemini-api/docs/realtime-music-generation)
- NO FAKES Act of 2026 (S.4591): advanced by Senate Judiciary on June 18 2026; would create a licensable (not assignable in life) digital-replica right covering voice and visual likeness of all individuals; platform notice-and-takedown with actual-knowledge liability; effective 180 days after enactment; Sept 30 2026 floor attempt blocked. — [Blackburn press release](https://www.blackburn.senate.gov/2026/6/blackburn-coons-bipartisan-bill-to-protect-individuals-and-creators-from-deepfakes-passes-senate-judiciary-committee); [Holland & Knight](https://www.hklaw.com/en/insights/publications/2026/06/senate-judiciary-committee-advances-legislation-to-protect-name); [sirency](https://www.sirency.com/blog/no-fakes-act-ai-likeness-laws)
- Current regime: patchwork of state right-of-publicity laws (e.g., Tennessee ELVIS Act); ToS is where licensing happens (Lensa 2022 perpetual license controversy; VSCO June 22 2026 terms claim rights to "name, image, voice, or likeness of any individual included in your Content"). — [PetaPixel Lensa](https://petapixel.com/2022/12/13/lensa-ais-terms-allow-it-to-use-images-without-compensation); [PetaPixel VSCO 2026](https://petapixel.com/2026/05/26/vsco-terms-of-use-explained-why-it-says-it-isnt-stealing-your-photos/)

### Inferences
- A self-hosted lightweight classifier (CLIP/ViT NSFW+violence head) run on the generation GPU on every Nth frame costs essentially nothing marginal and should be the first line; route only flagged frames (or 1 frame per 10–30 s) to Hive/Sightengine. Budget ≈ $0.2–0.7 per player-hour for commercial moderation at 0.1 fps.
- For user-uploaded seed photos: obtain an explicit, revocable, non-training license limited to operating the session; apply face detection to decide whether to require consent attestation; delete seeds after session; design for NO FAKES-style notice-and-takedown now, since the bill may pass in 2027.

### Gaps
- No published per-frame latency for Hive or Sightengine; Hive video-frame rate requires a quote.
- Licensing terms of Genie/Veo/Decart outputs for user-seeded content were not researched.

## Key Question 8: Bottom-up cost model, $ per player-hour (three architectures) and production-readiness flags

### Takeaway
Using the Oct 2026 prices above: (a) a full real-time world model costs ~$4–7 per player-hour self-hosted on one H100 (≈$2–3 on spot/reserved; $72+/hr via Decart's API); (b) a pre-generated-clip service on commercial video APIs costs $90–1,440 per hour of unique footage, so it is only viable with >95% cache reuse across players ($4–70/hr); (c) a hybrid "3D splat scene + event clips" costs ~$1.5–6 per player-hour, dominated by event clips and audio rather than GPU rendering.

### Cited Findings
(Source numbers are those cited in Questions 1–7; key inputs restated with sources.)
- H100 on-demand $2.60–4.29 (neo-cloud), B200 $5.50–6.99, L4 $0.43–0.80, L40S $0.79–1.95. — [DEV/Nodus](https://dev.to/viswaretas_kotra/gpu-cloud-pricing-october-2026-what-an-h100-h200-b200-or-b300-costs-per-hour-5a25); [Lambda](https://lambda.ai/pricing); [RunPod](https://www.runpod.io/pricing); [Modal](https://modal.com/pricing)
- Spot/reserved H100 ~$1.03–2.46. — [CoreWeave spot via Spheron](https://spheron.network/blog/coreweave-h100-h200-pricing-2026); [Nebius spot via Thunder](https://www.thundercompute.com/blog/coreweave-vs-nebius)
- Open world-model throughput: 17 fps/H100 (1.3B), 40 fps claimed (5B), 11 fps/B200 (14B), 58 fps/4xH100 (14B). — [Self-Forcing](https://arxiv.org/html/2506.08009v2); [Matrix-Game 3.0](https://huggingface.co/Skywork/Matrix-Game-3.0); [Krea](https://huggingface.co/krea/krea-realtime-video); [StreamDiffusionV2](https://arxiv.org/abs/2511.07399v1)
- Odyssey $1–2/user-hour; Decart Oasis 3 $0.02/s. — [Odyssey](https://odyssey.systems/introducing-interactive-video); [Decart](https://docs.platform.decart.ai/getting-started/pricing)
- Commercial clip APIs (Aug–Oct 2026): Veo 3.1 Lite $0.05/s (720p), Fast $0.10/s, Standard $0.40/s; Kling 3.0 Turbo ~$0.11/s; LTX-2.3 Fast $0.06–0.24/s; Hailuo H3 Max Turbo on fal $0.025/s; Decart Lucy 2.5 offline $0.04/s; Runway Gen-4 Turbo $0.05/s; Sora 2 $0.10–0.70/s (API sunset Sep 24 2026). — [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing); [invideo Aug 2026](https://invideo.io/blog/ai-video-model-pricing); [fal pricing](https://fal.ai/pricing); [Decart](https://docs.platform.decart.ai/getting-started/pricing); [Atlas Cloud comparison](https://www.atlascloud.ai/blog/case-studies/Top-5-ai-video-apis-compared-speed-latency-and-cost-per-second-2026)
- Transport: Cloudflare $0.05/GB egress; LiveKit ~$0.0004–0.0005/participant-min. — [Cloudflare](https://developers.cloudflare.com/realtime/sfu/platform/pricing/); [trtc.io](https://trtc.io/blog/details/livekit-pricing-2026)
- Audio: Gemini Live out $0.018/min; ElevenLabs Flash $40/1M chars, SFX $0.12/min, Music $0.15/min; Lyria 3.5 $0.08/song; Stable Audio 3.0 Small 0.44 s/clip on H200. — [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing); [ElevenLabs](https://elevenlabs.io/pricing/api); [The Decoder](https://the-decoder.com/stability-ai-launches-stable-audio-3-0-with-up-to-six-minute-tracks-and-open-weights/)
- Moderation: Sightengine $0.0015–0.002/op; Hive $3/1k; AWS $0.001/image. — [Sightengine](https://sightengine.com/pricing); [Hive](https://thehive.ai/pricing); [AWS](https://aws.amazon.com/rekognition/pricing/)

### Inferences

**Shared line items (per player-hour)**
- Egress 720p30 @ ~5 Mbps ≈ 2.25 GB → $0.09–0.11; SFU minutes $0.02–0.03. Total transport ≈ $0.12–0.15.
- Audio, API route (15% dialogue duty via ElevenLabs Flash ≈ $0.36; 5 min SFX ≈ $0.60; music via Lyria 3.5 clips ≈ $1.60) ≈ $2.5; self-hosted route (Kokoro + Stable Audio 3.0 on a shared L4 slice) ≈ $0.05–0.20.
- Moderation at 0.1 fps commercial ≈ $0.36 (AWS) to $0.72 (Sightengine) to $1.08 (Hive); self-hosted classifier ≈ $0.
- Utilization overhead for a consumer service (peak provisioning, warm pools): multiply GPU line by ~1.3–1.5 (assumption, not sourced).

**(a) Full real-time world model (self-hosted, 1–5B AR model at 20–40 fps, one H100 per stream)**
- GPU: $2.60–4.29 x 1.3–1.5 ≈ $3.4–6.4; spot/reserved ≈ $1.3–3.7.
- 14B-class model needing 2–4 H100 or 1 B200 at 11 fps: $7–17 (H100) or $7–10 (B200, below 24 fps).
- Plus transport $0.15, audio $0.2–2.5, moderation $0.4–1.1.
- Total: ≈ $4–7 per player-hour (small model, on-demand); ≈ $2–4 (reserved/spot or Odyssey-class optimization); ≈ $8–20 (14B quality). Via Decart Oasis 3 API: $72 + audio/moderation.

**(b) Pre-generated clips from commercial video APIs**
- Unique-footage cost per hour at 100% fresh: Hailuo H3 Max Turbo $90; Veo 3.1 Lite $180; LTX-2.3 Fast $216; Veo 3.1 Fast $360; Kling 3.0 Turbo $396; Veo 3.1 Standard $1,440. With a branching factor k pre-generated per decision point and cache-hit rate h across players, effective cost ≈ unique-cost x k x (1 - h). At k=3, h=0.95: $13–216/hr; at k=2, h=0.99: $1.8–29/hr.
- Self-hosted open clip model (Wan 2.2 / LTX-2.x on H100): if generation runs at ~2x real time (LTX-Video 0.9.7 claimed HD in ~10 s on H100 for short clips; unverified for 2.x), one H100-hour yields ~1,800 s of video → ~$0.002/s → ~$8/hr of unique footage, i.e. 10–50x cheaper than APIs but with offline quality and 5–20 s decision latency.
- Latency: branch selection lag equals clip generation time (seconds to tens of seconds) unless branches are pre-rolled; interaction is menu/choice-based, not continuous.

**(c) Hybrid 3D scene + event clips**
- Bootstrap: VGGT/DA3 <1 s; Marble ~1–5 min; amortized <$0.05/player-hour.
- Rendering: client WebGPU splat viewer $0; or server L4 shared by ~4 streams ≈ $0.11–0.20/player-hour + NVENC on the same card.
- Optional real-time V2V stylization of the render: Decart Lucy Restyle $36/hr (API) or self-hosted StreamDiffusionV2/Self-Forcing 1.3B on one H100 ≈ $3.4–6.4 (this collapses to case (a) economics; use sparingly, e.g., only during cutscenes).
- Event clips: ~6 events/hr x 8 s = 48 s x $0.05–0.10 (Veo Lite/Fast) ≈ $2.4–4.8; or $0.10–0.20 self-hosted.
- Plus transport $0.15, audio $0.2–2.5, moderation $0.4–1.1.
- Total: ≈ $1.5–3 per player-hour with client rendering and self-hosted audio/moderation; ≈ $4–9 with commercial APIs for clips, audio and moderation.

**Production-ready vs research-only (Oct 2026)**
- Production-ready: NVIDIA H100/H200/B200 rentals on neo-clouds; Modal/RunPod/fal/Replicate/Baseten serving; NVENC + WebRTC (LiveKit, Pion, Cloudflare SFU); Decart Lucy/Oasis 3 APIs (metered, expensive); Self-Forcing/CausVid, Krea Realtime 14B, Matrix-Game 3.0, StreamDiffusionV2 (open code, need your own serving work); TeaCache/MagCache; xDiT; VGGT/DA3 for geometry; Marble for splat worlds; ElevenLabs/Cartesia/Gemini/Kokoro TTS; Stable Audio 3.0 and ElevenLabs SFX; Lyria 3.5 clip music; Sightengine/Hive/AWS moderation; Veo/Kling/LTX/Hailuo clip APIs.
- Research/preview only: Genie 3 (60-s sessions, $249.99/mo consumer tier, no API); Odyssey (demo, "raw, unstable"); Lyria RealTime (experimental, unpriced); Etched Sohu (unshipped); NVFP4 for video DiTs; Cosmos as real-time engine; MMAudio for commercial use (NC weights); real-time 4K super-resolution; speculative generative branch prefetching (no literature).

### Gaps
- Utilization multipliers, cache-hit rates, event frequency and dialogue duty cycles are modelling assumptions, not measured; the parent report should present them as adjustable parameters.
- No source gives a per-stream GPU count for Decart or Odyssey, so (a) is bracketed by open-model throughput rather than vendor efficiency.
- Open clip-model generation speeds for Wan 2.2/LTX-2.x on H100 were not retrieved; the ~$8/hr self-hosted figure in (b) is an order-of-magnitude estimate.
