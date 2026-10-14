# Competitive & Prior-Art Landscape: Generative "Do-Anything" Interactive Worlds (state as of 2026-10-09)

Scope note: this covers products, startups, demos and research that attempt "an open-ended game/experience where the player can do anything and the world/video/story is generated on the fly." Everything is dated; status is tagged SHIPPED (publicly usable), GATED (paid/waitlist/limited), DEMO (research preview / tech demo), or DEFUNCT. Research was done via web search on 2026-10-09; several facts come from secondary coverage and are flagged as such.

## Landscape map: who is doing what (summary table, Oct 2026)

### Takeaway
As of October 2026 no company has shipped a mass-market "do-anything" game built on real-time generated video; the real-time-video layer exists only as gated previews (Project Genie, Runway GWM Worlds 2, Odyssey, PixVerse R1, Mirage 2) or as mocked tech demos (Oasis, WHAMM Quake II), while the "do-anything" story layer exists only in text (AI Dungeon/Voyage, Hidden Door, Character.ai Scenes). Nobody found combines a multi-agent LLM director with real-time generated video in a playable product.

### Cited Findings
| Entry | Team / founded / funding | What user experiences | Tech | "Do anything"? | Story/memory | Status Oct 2026 | Negatives |
|---|---|---|---|---|---|---|---|
| Project Genie / Genie 3 | Google DeepMind; Genie 1 Mar 2024, 2 Dec 2024, 3 Aug 2025; web app Jan 29 2026 | Real-time first-person video world from text/image, 720p 24fps, WASD | 11B spatiotemporal transformer, autoregressive latent video — [Wikipedia Genie](https://en.wikipedia.org/wiki/Genie_(world_model)) | Can walk anywhere + "promptable world events"; no game rules | ~1 minute visual memory; 60-second session cap — [Wikipedia Project Genie](https://en.wikipedia.org/wiki/Project_Genie_(website)) | GATED: US AI Ultra subscribers only at launch; Street View mode "global AI Ultra users" May 19 2026 | "too choppy" 24fps (Fast Company); slow (Verge); no API/export (Cybernews) |
| Oasis (Decart + Etched) | Decart (Israel, 2023); $300M at ~$4B May 2026, >$450M total | Minecraft-like generated frames, 360-720p, 20fps, 5-min sessions | 500M-param diffusion transformer trained on Minecraft video, open weights — [Decoder/InfoQ](https://www.infoq.com/news/2024/11/decart-etched-oasis) | Can "do" Minecraft actions but no persistent logic | No object permanence; "dementia Minecraft" meme — [Wikipedia Oasis](https://en.wikipedia.org/wiki/Oasis_(Minecraft_clone)) | DEMO (Oct 2024); successor "Oasis 2.0" is a Minecraft restyle mod, not a generated game — [oasis2.decart.ai](https://oasis2.decart.ai/) | Togelius: "an answer in search of a question" |
| Mirage / Mirage 2 (Dynamics Lab) | Dynamics Lab; demos Jul–Aug 2025 | GTA-like "Urban Chaos" and Forza-like "Coastal Drift"; Mirage 2 turns any image into WASD-explorable world, text edits mid-play | Autoregressive diffusion transformer, cloud-streamed, ~16fps SD (claims) — [the-decoder](https://the-decoder.com/mirage-2-allows-users-to-turn-sketches-and-photos-into-interactive-game-worlds/) | Free roam + text changes; no rules | Unknown; reported ~10+ min sessions at ~200ms latency (single outlet) | DEMO / "research preview"; no 2026 news found | "struggles with precise controls and visual stability" |
| Odyssey | Odyssey (Menlo Park, 2023); $310M Series B at $1.45B Jun 17 2026, $337M total — [TechCrunch](https://techcrunch.com/2026/06/17/world-model-maker-odyssey-nabs-1-45b-valuation-backed-by-amazon-and-other-big-names/) | Streaming interactive video you steer by keys/joystick; Odyssey-2 (Oct/Nov 2025) adds open text prompting mid-stream at 20fps; Odyssey-2 Pro (Jan 2026) 720p ~22fps | Diffusion world model, H100 clusters, 40ms latency claim — [aiwiki](https://aiwiki.ai/wiki/odyssey_2) | Camera/nav + text; no game | Layouts didn't stay consistent when turning (TechCrunch via aiwiki) | GATED research previews; AWS/Trainium partner | blurry/distorted (TechCrunch, 2025) |
| Runway GWM-1 / GWM Worlds 2 | Runway; $315M Series E at $5.3B Feb 10 2026 — [TechCrunch](https://techcrunch.com/2026/02/10/ai-video-startup-runway-raises-315m-at-5-3b-valuation-eyes-more-capable-world-models/) | 720p 24fps continuous video+48kHz audio, text actions + camera; first/third person; "no fixed session length" | Autoregressive diffusion, "WorldPrompt" architecture — [atlasworldmodel](https://atlasworldmodel.com/gwm-worlds-2) | Text-addressed actions to subjects/scene | Persistent world context + action stream (claimed) | DEMO: research preview Sep 3 2026, contact-form only, no API | No quantitative evals published |
| Microsoft Muse / WHAM / WHAMM | Microsoft Research + Ninja Theory; Muse Feb 19 2025; WHAMM Quake II Apr 2025 | 640x360, 10+fps generated Quake II in Copilot Labs | WHAM 1.6B autoregressive; WHAMM MaskGIT parallel decoding — [MS Research](https://www.microsoft.com/en-us/research/project/wham/wham-rt/) | Shoot/move in one level | 0.9s context; enemies become "blobs" | DEMO; no 2026 update found | "barely-glorified image simulator", "mimicry with holes" (Austin Walker) |
| PixVerse R1 | PixVerse (Singapore); launched Jan 12 2026 | Continuous interactive audiovisual stream, shared multi-user worlds + avatars (Apr 2026) | Unified token stream, 1–4 sampling steps — [PixVerse blog](https://pixverse.ai/en/blog/pixverse-launches-r1-real-time-world-model) | Prompt-driven; no rules | Not documented | SHIPPED (free "for a limited time" at realtime.pixverse.ai) | Resolution claims disputed (480p vs 1080p) |
| World Labs Marble | World Labs (Fei-Fei Li); $1B raise Feb 2026 at ~$5B | Text/image → persistent explorable 3D Gaussian-splat world, exports to Unity/Unreal | 3D generation (not video) — [World Labs blog](https://www.worldlabs.ai/blog/announcing-the-world-api) | Static scenes; no NPCs/rules | Persistent geometry (true memory, by construction) | SHIPPED Nov 12 2025; API Jan 21 2026; Marble 1.1 Apr 2 2026 | Credit cost per world; static |
| Tencent Hunyuan-GameCraft / HY-World | Tencent; GameCraft Jun 2025, GameCraft-2 Nov 2025, HY-World 1.5 "WorldPlay" Dec 2025, HY-World 2.0 Apr 16 2026 | Image + keyboard/mouse → game-like video | Built on HunyuanVideo MM-DiT, >1M clips from 100+ AAA games, open weights — [arXiv](https://arxiv.org/html/2506.17201v1) | Camera movement only | Hybrid history conditioning | DEMO/open-source | License excludes EU/UK/KR |
| Skywork Matrix-Game 1.0→3.5 | Skywork AI; 2.0 Aug 2025, 3.0 Mar 2026, 3.5 Aug 2026 | 25fps keyboard/mouse controlled video, 720p in 3.5 | 17B open world model, GTA5/UE data — [GitHub](https://github.com/SkyworkAI/Matrix-Game) | Navigation only | 3.0 adds "long-horizon memory"; 3.5 "patch memory" | DEMO/open-source | — |
| General Intuition (MIRA) | NY/NL, sister of Medal; $133.7M seed Oct 2025, $320M A Jun 2026, $220M at $6.2B Oct 2026 — [GamesBeat](https://gamesbeat.com/?p=335876) | MIRA: playable multiplayer Rocket League world model (with Kyutai, Epic) | Trained on 2B+ Medal clips/yr with action labels | n/a (agents are the product) | — | DEMO; "world model is the gym, not the product" | — |
| AI Dungeon / Voyage (Latitude) | Latitude (Utah, 2019) | Text (+ "See mode" images); Voyage = creator-built persistent text worlds | GPT-2→GPT-3→own Wayfarer/Harbinger models; Voyage uses Gemini — [Respawn](https://respawn.outlookindia.com/amp/story/gaming/gaming-news/design-your-own-world-latitude-unveils-voyage-ai-rpg) | Yes (free text) | Weak memory historically; Voyage "World Engine tracks logic" | SHIPPED (AI Dungeon); Voyage expanded beta Apr 21 2026 | Peaked ~2021 (Lantz); content-moderation crisis 2021 |
| Hidden Door | Hilary Mason + Matt Brandwein, 2020; $9M | Illustrated text RPG in licensed IP; Atlas user worlds (2026) | Proprietary narrative engine + LLMs | "You can steer, remix, and choose — you cannot conjure" — [Arcanum](https://arcanumrpgs.com/blog/hidden-door-review/) | Designed around constraints | SHIPPED Aug 2025; Atlas + daily remixes Jul 30 2026 | — |
| Character.ai Scenes | Character.ai; Scenes Oct 2025 | Community-authored chat scenarios | LLM chat | Open chat within scenario | Chat memories | SHIPPED | — |
| Suck Up! (Proxima) | indie, 2023 | Voice-talk your way into houses as a vampire | Speech→LLM→TTS | Open speech, fixed goal | Per-session | SHIPPED | token monetization "players hit a wall" (Mason via search) |
| Vaudeville (Bumblebee) | indie, 2023 | Interrogate AI suspects | LLM dialogue | Open dialogue | Weak | SHIPPED, "Mixed" on Steam | "polarized… evenly split between enthusiasts and haters" (dev) |
| 1001 Nights (Ada Eden) | indie | Tell stories to an AI king; words become weapons | LLM + image gen | Constrained | — | DEMO (Steam demo only) | — |
| Death by AI | indie | Jackbox-style AI judge party game | LLM + TTS | Free text answers | n/a | SHIPPED, ~77.6K monthly visits (directory est.) | "nearly went bankrupt" on OpenAI/ElevenLabs costs (Lantz) |
| Infinite Craft (Neal.fun) | Neal Agarwal, Jan 2024 | Combine word-elements; LLM invents results | LLM | Open combinatorics | n/a | SHIPPED, viral | Lantz: "doesn't change his view" |
| Fable Showrunner | Fable Studio; Amazon Alexa Fund investment mid-2025 | Prompt → 2–16 min animated episodes | SHOW-1/SHOW-2 multi-agent | Prompting episodes, not playing | Consistent characters | SHIPPED (animation only); no 2026 news found | "soulless and unfunny" (Christos Gage, 2023) |
| Utopai Studios | Utopai; PAI model Mar 2026, "Story Agent" Apr 2026 | 3-min continuous 4K narrative sequences | Agentic long-form video — [Wikipedia](https://en.wikipedia.org/wiki/Utopai_Studios) | Filmmaking, not playable | Narrative continuity tracking | SHIPPED (film tool) | — |
| Netflix Bandersnatch (non-AI baseline) | Netflix 2018 | Branching live-action film | Hand-authored | Fixed branches | Fixed | DEFUNCT (removed May 2025) | "technology was very limiting… capped" (Mike Verdu) |

### Inferences
- The table splits cleanly into two families that have not merged: (a) real-time video world models with navigation but no story/rules/memory, and (b) text LLM games with story and (some) memory but no generated visuals beyond stills. The user's concept lives in the empty cell between them.
- The most "shipped" real-time video product is PixVerse R1 (free, multi-user), but it is positioned as creative video, not a game.

### Gaps
- No single primary source confirms current (Oct 2026) live status of Dynamics Lab's Mirage demos; all coverage is Jul–Aug 2025.

## Q1. Real-time generative video "games": what exists, what launched publicly in 2026?

### Takeaway
2026 saw the first *public* access to real-time generated worlds (Project Genie Jan 29 2026 for paid US subscribers; PixVerse R1 Jan 12 2026 free; Runway GWM Worlds 2 Sep 2026 contact-only), but every one is a navigable video stream with a short memory horizon and no game rules; none is sold or framed as a finished game.

### Cited Findings
**Google Genie 3 / Project Genie**
- Project Genie "was released on January 29, 2026" as a Google Labs site letting AI Ultra subscribers use Genie 3; worlds are 720p/24fps; "Exploration is capped at 60 seconds"; DeepMind said "extending the limit would add relatively little testing value" while raising compute cost — [Wikipedia: Project Genie](https://en.wikipedia.org/wiki/Project_Genie_(website))
- Genie 3 has a one-minute memory vs 10–20 seconds for Genie 2; Genie 2 ran at 360p; Genie 1 produced one frame per second — [Wikipedia: Genie](https://en.wikipedia.org/wiki/Genie_(world_model))
- Eligibility at launch: US-based AI Ultra subscribers aged 18+ on personal accounts; Google said it would expand territories with no timeline — [Dataconomy](https://dataconomy.com/2026/01/30/google-launches-project-genie-create-interactive-worlds-with-ai/); [Mobilesyrup](https://mobilesyrup.com/2026/01/30/google-debuts-project-genie-that-can-generate-interactive-worlds/)
- May 19 2026: Street View integration, "goes live for global AI Ultra users" (Engadget via Wikipedia) — [Wikipedia: Project Genie](https://en.wikipedia.org/wiki/Project_Genie_(website))
- Reception: The Verge (Jay Peters) found performance slow; Fast Company called 24fps "too choppy for real-world use"; TechCrunch noted it cannot generate copyrighted material; one review says "no commercial or developer API… nor any export option" — [Wikipedia: Project Genie](https://en.wikipedia.org/wiki/Project_Genie_(website)); [Cybernews review](https://cybernews.com/ai-tools/google-project-genie-review/)
- Market reaction: Unity fell 24.22%, Roblox 13.17%, major publishers 5–15% after the Jan 29 announcement — [Cybernews](https://cybernews.com/ai-tools/google-project-genie-review/) (secondary; Bloomberg cited by Wikipedia also reports game stocks fell)
- Genie 3 was trained on "over 30,000 hours of gameplay footage" — [Cybernews](https://cybernews.com/ai-tools/google-project-genie-review/)
- Genie 3 "can only sustain a few minutes of continuous interaction, while proper agent training would need hours" — [TechCrunch Aug 2025](https://techcrunch.com/2025/08/05/deepmind-reveals-genie-3-a-world-model-that-could-be-the-key-to-reaching-agi)

**Decart Oasis / Etched**
- Oasis announced Oct 31 2024; trained on Minecraft footage; players could move, chop trees, place blocks "but the game often deviates… placing a block of dirt might lead to an entirely new environment" — [Deeplearning.ai The Batch](https://www.deeplearning.ai/the-batch/ai-creates-an-interactive-minecraft-like-world-in-real-time)
- Ran 360p–720p at 20fps, no sound, "could only be played for five minutes at a time before restarting"; players nicknamed it "dementia Minecraft"; Julian Togelius: "an answer in search of a question" — [Wikipedia: Oasis](https://en.wikipedia.org/wiki/Oasis_(Minecraft_clone))
- Etched claimed 8 H100s serve 5 Oasis users while 8 Sohu chips would serve 65; Sohu targeted 100B-param models at 4K; these are vendor claims and the demo actually ran on H100s — [InfoQ](https://www.infoq.com/news/2024/11/decart-etched-oasis); [TechPowerUp](https://techpowerup.com/news-tags/Sohu)
- Decart raised $300M at ~$4B on May 18 2026 led by Radical Ventures with Nvidia, Adobe, Toyota; total >$450M; valuation path $500M (Dec 2024) → $3.1B (Aug 2025) → ~$4B — [SiliconANGLE](https://siliconangle.com/2026/05/18/decart-raises-300m-ai-optimization-software-world-models/); [Calcalist](https://www.calcalistech.com/ctechnews/article/sjt9ncukgl)
- Decart's 2026 product lines: "Lucy" (real-time video-to-video for try-on/livestream/ads, <30ms), "Oasis" (now repositioned toward physical AI/robotics), and DOS inference stack; Lucy2 runs on AWS Trainium3 — [TheNextWeb](https://thenextweb.com/news/decart-300-million-radical-ventures-world-models)
- "Oasis 2.0" (2025) is a Fabric Minecraft mod that restyles real Minecraft frames via Decart's video-to-video model at 1080p/30fps — i.e., it is not a generated game — [oasis2.decart.ai](https://oasis2.decart.ai/); [CurseForge](https://www.curseforge.com/minecraft/mc-mods/oasis2)
- An "AI agent breaks AI-generated Minecraft" write-up documents how trivially the Oasis world collapses under non-human input — [elefant.gg blog](https://blog.elefant.gg/p/ai-agent-breaks-ai-generated-minecraft)

**Dynamics Lab Mirage / Mirage 2**
- Mirage (Jul 2025) GTA-style "Urban Chaos" and Forza-style "Coastal Drift" demos; pitched as "first real-time generative engine for live UGC gameplay"; autoregressive diffusion transformer; a promotional page claims 16fps SD cloud-streamed — [Product Hunt](https://www.producthunt.com/products/mirage-11); [iNEWS](https://inf.news/en/game/f5211c3b4010b1ca574ad42441287ba5.html)
- Mirage 2 (Aug 2025): upload any image (crayon drawing, concept art, painting photo) + prompt → WASD-explorable world; text commands change the world mid-play; "still struggles with precise controls and visual stability"; a reviewer said Genie 3 "is far ahead on precise controls and visual stability" — [the-decoder](https://the-decoder.com/mirage-2-allows-users-to-turn-sketches-and-photos-into-interactive-game-worlds/); [Gigazine](https://www.gigazine.net/gsc_news/en/20250825-ai-generative-world-mirage-2)
- Sources conflict on whether it runs in the cloud or on a single local GPU; ~200ms latency and 10+ min sessions reported by one outlet only — [Korben](https://korben.info/en/mirage-2-ai-game-engine-generates-worlds-real-time.html)

**Odyssey**
- Research preview May 2025: "watch, interact, and directly influence the video as it plays, with just a keystroke, swipe, or joystick"; up to 30fps from H100 clusters, 40ms keypress-to-frame — [eWeek](https://www.eweek.com/news/odyssey-ai-interactive-video/); [aiwiki](https://aiwiki.ai/wiki/odyssey_2)
- CEO Oliver Cameron: "every frame is absolutely generated by a diffusion model we've trained"; post-trained on a small set of densely captured places, "trading generality for stability"; TechCrunch (2025) reported blurry, distorted environments whose layouts did not stay the same when turning — [aiwiki](https://aiwiki.ai/wiki/odyssey_2) (secondary)
- Odyssey-2 (Oct 27 or Nov 3 2025 depending on source): open text prompting during a running stream at 20fps; Odyssey-2 Pro (Jan 23 2026) 720p ~22fps — [Product Hunt](https://www.producthunt.com/products/odyssey-5/launches/odyssey-2-3); [Stork](https://www.stork.ai/tool/odyssey-2-pro) (aggregators)
- Jun 17 2026: $310M Series B at $1.45B led by Natural Capital with Amazon, AMD Ventures, GV, EQT, IQT; founded 2023 by Oliver Cameron (ex-Cruise) and Jeff Hawke (ex-Wayve); targets "video-game creation to robotics"; article gives no traction numbers — [TechCrunch](https://techcrunch.com/2026/06/17/world-model-maker-odyssey-nabs-1-45b-valuation-backed-by-amazon-and-other-big-names/)
- An "Odyssey-3" launch on Sep 15 2026 is claimed by one blog only; unverified — [explainx](https://explainx.ai/blog/odyssey-3-world-model-launch-2026)

**Runway GWM-1 / GWM Worlds 2**
- GWM-1 released Dec 2025; Runway raised $315M Series E at $5.3B Feb 10 2026 to "pretrain the next generation of world models" — [TechCrunch](https://techcrunch.com/2026/02/10/ai-video-startup-runway-raises-315m-at-5-3b-valuation-eyes-more-capable-world-models/)
- GWM Worlds 2 (research preview, Sep 3 2026): 720p/24fps video + 48kHz audio, no fixed session length, text actions addressed to subjects/scene plus camera motion, first/third person walking/driving/flying; three modes (ahead-of-time filmmaking, turn-based visual novel, real-time game); access via business contact form only, no API, no GA date — [atlasworldmodel](https://atlasworldmodel.com/gwm-worlds-2); [explainx](https://explainx.ai/blog/runway-gwm-worlds-2-interactive-world-model-2026) (secondary)
- Criticism: "Runway has not published a robotics benchmark, a sim-to-real transfer result, or any quantitative evaluation at all" — [atlasworldmodel](https://atlasworldmodel.com/gwm-worlds-2)

**Microsoft Muse / WHAM / WHAMM**
- Muse announced Feb 19 2025 (WHAM-1.6B, trained on 7 years of Ninja Theory *Bleeding Edge* gameplay, ~1 image/sec, 300x180); Microsoft said it was developing a real-time version for Copilot Labs — [MS Research blog](https://www.microsoft.com/en-us/research/blog/introducing-muse-our-first-generative-ai-model-designed-for-gameplay-ideation/); [Xbox Wire](https://news.xbox.com/en-us/2025/02/19/muse-ai-xbox-empowering-creators-and-players/)
- WHAMM (Apr 2025): MaskGIT parallel decoding, 10+ fps, 640x360, trained on one week of Quake II data from one level; playable in Copilot Labs — [MS Research WHAM-RT](https://www.microsoft.com/en-us/research/project/wham/wham-rt/); [the-decoder](https://the-decoder.com/microsoft-releases-real-time-ai-generated-playable-demo-of-quake-ii/)
- Reception: ~10fps, blurry, delayed hit feedback; "context length is only 0.9 seconds… if a player turns away from an object, the AI will forget about it"; "pitch-black void or… deformed enemy blobs"; Austin Walker: "mimicry with holes"; developers: "barely-glorified image simulator"; >3MW power cited — [GameRant](https://gamerant.com/microsoft-quake-2-ai-tech-demo-backlash-poor-performance-dev-impact/); [GadgetGuy](https://www.gadgetguy.com.au/game-developers-react-microsoft-quake-ii-muse-generative-ai-preservation/); [BBN Times](https://www.bbntimes.com/technology/microsoft-s-ai-powered-quake-ii-a-glimpse-of-innovation-marred-by-limitations)
- No 2026 Muse/WHAM update was found in any search; Xbox's 2026 AI roadmap news is "Gaming Copilot" (an assistant), not generated games — [Windows Central](https://www.windowscentral.com/gaming/xbox/microsofts-xbox-ai-assistant-gaming-copilot-is-coming-to-consoles-this-year-and-not-stopping-there)

**PixVerse R1**
- Launched Jan 12 2026 in Singapore as "first real-time world model for interactive AI video"; continuous stream reacting to input, unified text/image/audio/video token stream, 1–4 sampling steps; Apr 2026 update added multi-user shared livestream worlds and photo-based avatars "with no session limits"; free "for a limited time" — [PixVerse blog](https://pixverse.ai/en/blog/pixverse-launches-r1-real-time-world-model); [Bernama](https://mrem.bernama.com/viewsm.php?idm=53905)
- Resolution claims conflict (1080p marketing vs "up from 480p" update) — [Atlas Cloud](https://www.atlascloud.ai/blog/guides/pixverse-r1)

**World Labs Marble (3D, not video)**
- GA Nov 12 2025; World API Jan 21 2026; Marble 1.1 / 1.1 Plus Apr 2 2026 (1,500 credits per world, "dynamic cubes" +300 credits each); exports to Blender/Unreal/Unity/Houdini — [World Labs blog](https://www.worldlabs.ai/blog/announcing-the-world-api); [NYU Shanghai RITS](https://rits.shanghai.nyu.edu/ai/world-labs-releases-marble-1-1-auto-expanding-3d-world-generation/)
- $1B raise Feb 18 2026 at ~$5B; acquired SceniX Jul 21 2026 — [valueaddvc](https://valueaddvc.com/blog/world-labs-valuation-what-fei-fei-lis-spatial-intelligence-startup-is-worth-at-5b) (secondary)

**Tencent / Nvidia**
- Hunyuan-GameCraft (Jun 2025): image+prompt → video controlled by keyboard/mouse "as camera movement"; trained on >1M recordings from >100 AAA games; open-source — [arXiv 2506.17201](https://arxiv.org/html/2506.17201v1); [OfficeChai](https://officechai.com/ai/chinas-tencent-releases-hunyuan-gamecraft-an-open-source-world-generating-model-like-genie-3/)
- HunyuanWorld-1.5 "WorldPlay" (Dec 2025, "real-time world creation and play") and HY-World 2.0 (Apr 16 2026) — [GitHub HunyuanWorld](https://github.com/Tencent-Hunyuan/HunyuanWorld-1.0)
- Nvidia Cosmos 3 (May 31 2026, GTC Taipei) is aimed at robotics/AV/vision agents, not games — [DataNorth](https://datanorth.ai/news/nvidia-launches-cosmos-3)

### Inferences
- Across all vendors the shipped memory horizon is ~1 minute (Genie 3) and session lengths are capped (60s Genie, 5 min Oasis) chiefly for compute cost; every public negative review cites either framerate/latency or forgetting. The "do-anything" promise is therefore currently "walk anywhere for a minute."
- Decart's repositioning of "Oasis" toward robotics and of its consumer product toward video restyling (Lucy, Oasis 2.0 mod) suggests the Minecraft-style generated game was a marketing demo without a retention path.
- PixVerse R1 is the only unrestricted free public real-time world model as of Oct 2026, but with no game framing.

### Gaps
- No primary Dynamics Lab announcement or funding data was retrievable; Mirage's current availability is unknown.
- No source reports user counts, retention or revenue for Project Genie, Odyssey, Runway GWM, or PixVerse R1.
- Could not confirm whether Etched's Sohu ever shipped or whether Oasis ever ran on it.

## Q2. Text/LLM-driven "do-anything" games: products and what they learned about player expectations

### Takeaway
The text layer is the only place "do anything" has actually shipped (AI Dungeon since 2019, Hidden Door 2025, Character.ai Scenes 2025, Latitude Voyage 2026), and the consistent lesson from practitioners (Mason, Lantz, Vaudeville's dev) is that unconstrained freedom is not fun: the durable designs give players a concrete goal and boundaries, while cost-per-call and model drift make pure open-ended LLM play economically and experientially unstable.

### Cited Findings
**AI Dungeon / Latitude**
- Lantz: AI Dungeon was built on GPT-2 in Dec 2019, "peaked around 2021, then declined"; he sees it as a lightweight wrapper whose appeal was mostly the novelty of text generation — [Lantz, Why No AI Games?](https://franklantz.substack.com/p/why-no-ai-games)
- Latitude's own models: Wayfarer-12B / Wayfarer Large 70B ("isn't afraid to let you die"), Wayfarer-2-12B, Harbinger-24B on Hugging Face; Latitude self-reports players "reacted even more positively than we expected" — [HF Wayfarer-12B](https://huggingface.co/LatitudeGames/Wayfarer-12B); [HF Wayfarer-Large](https://huggingface.co/LatitudeGames/Wayfarer-Large-70B-Llama-3.3)
- AI Dungeon "See mode" generates images during play (Stable Diffusion, default 50 steps) — [Latitude Notion](https://latitudegames.notion.site/The-See-Mode-9ddc00b08b94485b8e1e153e83934943)
- Voyage launched expanded beta Apr 21 2026: creators describe a world in natural language, a "World Engine" tracks logic, Gemini models power storytelling; "completely unscripted, persistent worlds"; a third-party directory lists $15/$30/$50 tiers and open beta "later in 2026" — [Respawn/Outlook India](https://respawn.outlookindia.com/amp/story/gaming/gaming-news/design-your-own-world-latitude-unveils-voyage-ai-rpg); [Latitude news](https://latitude.io/news/what-is-voyage)

**Hidden Door**
- Founded 2020 by Hilary Mason and Matt Brandwein; $9M raised; public launch Aug 2025 with licensed worlds (Call of Cthulhu, Pride and Prejudice, Wizard of Oz, The Crow) — [Tracxn](https://tracxn.com/d/companies/hidden-door/__DEEpimT5lup2Ka4OsbHxTGewc-6mqkwjQXwWx_E49y4); [GamesBeat](https://gamesbeat.com/hidden-door-reveals-its-ai-powered-narrative-game-building-platform/)
- PC Gamer preview: "convinced me of its potential for storytelling" — [PC Gamer](https://www.pcgamer.com/hidden-door-ai-game-narrative-rpg/)
- 2026 review: "A Narrative Engine, Not a Simulation… you can steer, remix, and choose — you cannot conjure" — [Arcanum](https://arcanumrpgs.com/blog/hidden-door-review/)
- Atlas (2026): anyone can build and share an interactive world; 30% of subscription revenue shared with world creators; "daily remixes + Atlas" post Jul 30 2026 — [Hidden Door blog](https://www.hiddendoor.co/blog/atlas-worldbuilding-interactive-world-builder-storytelling-rpg); [Hidden Door blog index](https://www.hiddendoor.co/blog/early-access)

**Hilary Mason's lessons (Medium essay "The State of AI-Native Games: Lessons from the Frontier"; direct fetch returned 403 — quotes below are from search-indexed excerpts)**
- "Constrained creativity wins. Give players boundaries to push against, not an empty void." Suck Up! and Retail Mage work because the player has a concrete goal — [Mason, Medium](https://medium.com/@hmason/the-state-of-ai-native-games-lessons-from-the-frontier-3e696a9e3279)
- Suck Up! reportedly generated 50M+ social views with zero marketing, 20M YouTube views in month one; "token-based monetization is a cautionary tale: players hit a wall and the fun stops" — [Mason, Medium](https://medium.com/@hmason/the-state-of-ai-native-games-lessons-from-the-frontier-3e696a9e3279)

**Frank Lantz, "Why No AI Games?" (Mar 2 2026)**
- "there haven't been any significant new AI-based game experiences"; three causes: business model ("The incentives are all wrong" – developers minimize model calls; model updates change the game unpredictably), culture ("a well-established, non-negotiable taboo" among gamers), and the nature of fun ("Starting with a bunch of surprising complexity doesn't lead to even more fun, it just short-circuits the whole process") — [Lantz](https://franklantz.substack.com/p/why-no-ai-games)
- Death by AI "nearly went bankrupt because of OpenAI and ElevenLabs costs"; Suck Up! is "a 'funny' improv game" with an LLM; Genie 3 and viral AI-Minecraft look like "clunkier, sloppier versions of run-of-the-mill video games"; "I think I was wrong" about dream-logic gameplay — [Lantz](https://franklantz.substack.com/p/why-no-ai-games)

**Vaudeville, 1001 Nights, Suck Up!, Death by AI, Infinite Craft**
- Vaudeville (2023): Steam "Mixed (255 reviews)" snapshot; developer pre-mortem: negative reviews "regarding the limitations of the AI… evenly split between enthusiasts and haters"; preview: "solving the actual mystery is frustrating" — [Steam](https://store.steampowered.com/app/2240920/Vaudeville); [Game Developer pre-mortem](https://www.gamedeveloper.com/press-release/vaudeville-a-pre-mortem); [KeenGamer](https://keengamer.com/articles/previews/vaudeville-preview-the-ai-questioning-to-nowhere/)
- 1001 Nights: IGF 2024 entry, still "demo stage and undergoing active development"; praised by SIGGRAPH Asia as "real-time co-creative storytelling" — [Steam](https://store.steampowered.com/app/2542850/1001_Nights/); [itch.io](https://ada-eden.itch.io/1001-nights-official)
- Death by AI: free Jackbox-style AI game-master party game; ~77.6K monthly visits per a tool directory (unverified) — [itch.io](https://bobbodev.itch.io/death-by-ai); [aichief](https://aichief.com/alternatives/death-by-ai/)
- Infinite Craft (Neal Agarwal, early 2024) went viral; LLM decides combination results; 200,000 combinations discovered collectively (developer-reported) — [Dexerto](https://www.dexerto.com/gaming/what-is-infinite-craft-how-to-play-the-addictive-new-game-2536960/); [KnowYourMeme](https://amp.knowyourmeme.com/memes/sites/infinite-craft)

**Inworld, Convai, Artificial Agency, Ego, Bitmagic, Rosebud, Nvidia ACE, Ubisoft**
- Inworld Origins (Steam Next Fest Jun 2023, UE5) is a detective "playable short"; Inworld's CPO called it "a case study for game developers"; still listed on Steam May 2026; no 2026 successor found — [Axios](https://www.axios.com/2023/08/07/inworld-ai-origins-demo); [Steam](https://steamcommunity.com/app/2199920)
- Artificial Agency: Behavior Engine with Unity support (Mar 2026), acquired Reflection Tree (Apr 2026), Owlchemy Labs collaboration on *Dimensional Double Shift* single-player mode (Sep 2026) — [artificial.agency](https://www.artificial.agency/)
- Convai: voice NPCs for Unity/Unreal/web, free-to-start; Ego (ego.live): "generative AI simulation engine" of LLM characters in 3D, seed-stage ($6.7M latest, $14.7M cumulative per PitchBook); Bitmagic: waitlist-gated per one roundup; Rosebud AI: added Steam publishing May 2026 — [unite.ai roundup](https://www.unite.ai/best-ai-game-generators/); [Crunchbase Ego](https://www.crunchbase.com/organization/ego-be46); [PitchBook Ego AI](https://pitchbook.com/profiles/company/528243-13)
- Nvidia ACE in *Mecha BREAK* (Minitron 4B, 2GB VRAM): responses "reasonably life-like… not particularly immersive"; "still feel like those of a typical NPC" — [Tom's Hardware](https://tomshardware.com/tech-industry/artificial-intelligence/nvidias-first-ai-npc-debuts-in-mecha-break-minitron-4b-model-only-requires-2gb-of-vram); [HotHardware](https://hothardware.com/news/first-nvidia-ace-game-mecha-break)
- Ubisoft Neo NPCs (GDC Mar 2024, with Nvidia + Inworld); successor "Teammates" FPS prototype in closed playtest (late 2025); CEO: tools "in active production"; PC Gamer headline: "it could be the start of a fantastic paradigm shift, but… it probably won't"; Sep 2026 "Motherbrain" internal AI branding — [Variety](https://variety.com/2025/gaming/news/ubisoft-generative-ai-game-teammates-neo-npc-developers-1236588038/); [PC Gamer](https://www.pcgamer.com/software/ai/ubisoft-shows-off-ai-powered-neo-npcs-at-gdc-it-could-be-the-start-of-a-fantastic-paradigm-shift-but-lets-be-honest-it-probably-wont/); [Nintendo Life](https://www.nintendolife.com/news/2026/09/random-motherbrain-returns-as-ubisofts-genai-gaming-initiative)
- Character.ai "Scenes" (Oct 2025): creator-defined setting/backstory/goals, "Any Character" vs "Main Character" styles; c.ai+ $9.99/mo in 2026 — [blockchain.news](https://blockchain.news/news/character-ai-launches-scenes-enhanced-storytelling-experience); [mezha](https://mezha.net/eng/?p=2984553)
- NovelAI Text Adventure Module: legacy ">" action syntax; custom modules only on older models — [NovelAI docs](https://docs.novelai.net/text/textadventure.html)

### Inferences
- Every surviving text product has moved *toward* structure: Hidden Door licensed IP and "cannot conjure", Latitude's Voyage "World Engine tracks the logic", Character.ai Scenes adds creator-defined goals. Pure freeform (2019-era AI Dungeon) is treated by its own successors as a failed design.
- Monetization is a design constraint: per-call costs push developers to cache/limit (Lantz) and token walls kill sessions (Mason), which argues for a cheap always-on world state with expensive generation used sparingly.

### Gaps
- Mason's essay could not be fetched directly (HTTP 403; mirror unreachable); only indexed excerpts are cited.
- No user-count data for AI Dungeon, Hidden Door, Voyage, Character.ai Scenes was found.
- "Sentient / Project Genesis", "Volley" (voice games), and "Chaos Theory"-style LLM NPC games returned no relevant results; status unknown.
- Bitmagic status conflicts across roundups (waitlist vs free).

## Q3. Image/video-generated adventure experiences and the interactive-film baseline

### Takeaway
Per-turn image generation is an add-on feature (AI Dungeon See mode, Unbounded research), per-choice *video* adventures exist only as pre-rendered hobby projects with acknowledged continuity drift, and the non-AI baseline (Netflix interactive) was shut down in 2024–25 because the format was "very limiting… capped."

### Cited Findings
- AI Dungeon See mode generates images mid-adventure with Stable Diffusion — [Latitude Notion](https://latitudegames.notion.site/The-See-Mode-9ddc00b08b94485b8e1e153e83934943)
- PlayCYOA (indie, ~Sep 2026): branching video adventure where "a depth-3 tree is only 7 clips, generated once and then served as static files"; "Each clip is generated independently, so characters drift between branches"; workaround: frame each scene as a change of location; prepaid balance, generation pauses when funds run out — [dev.to](https://dev.to/qingqiu/i-built-a-choose-your-own-adventure-site-where-every-choice-is-an-ai-generated-video-2p92)
- Native Kling/Veo clips run ~15 seconds, so multi-scene interactive film needs stitching — [Higgsfield](https://higgsfield.ai/ai-video)
- Utopai Studios: PAI model (Mar 2026) tracks narrative continuity, character consistency across multi-shot sequences; "Story Agent" (Apr 2026) renders continuous 3-minute 4K sequences; ~$11M ARR per Wikipedia citing Forbes; filmmaking-focused, not playable — [Wikipedia Utopai](https://en.wikipedia.org/wiki/Utopai_Studios)
- Fable Showrunner: SHOW-1 (2023) multi-agent episode generator; Showrunner announced Jun 2024; 2–16 minute episodes with consistent characters; Amazon Alexa Fund invested mid-2025; SHOW-2 proprietary model; animation only; Christos Gage called SHOW-1 episodes "soulless and unfunny" — [Variety](https://variety.com/2025/digital/news/netflix-of-ai-amazon-invests-fable-showrunner-launch-1236471989/); [Cined](https://www.cined.com/the-netflix-of-ai-fables-showrunner-platform-lets-users-create-custom-episodes/); [Wikipedia Fable Studio](https://en.wikipedia.org/wiki/Fable_Studio)
- Netflix Bandersnatch: 2.9M hours watched in H1 2023 (Kimmy vs the Reverend 300K hrs); Netflix delisted nearly all interactive titles from Dec 1 2024 and the last two (Bandersnatch, Kimmy) on May 12 (2025); games head Mike Verdu: "the technology was very limiting and the potential… was kind of capped" — [Lowpass](https://lowpass.beehiiv.com/p/interactive-tv-trivia-triviaverse-chive-atmosphere-netflix); [What's on Netflix](https://www.whats-on-netflix.com/news/netflix-no-longer-making-interactive-shows-and-movies); [Dark Horizons](https://www.darkhorizons.com/?p=184199); [MovieMaker](https://www.moviemaker.com/a-fond-farewell-to-netflix-interactive-content/)
- Dream Agents newsletter (Sep 14 2026) frames the real-time-video future as "a show that changes based on what viewers ask characters to do" but names no shipped example; core problem stated: "every single minute someone watches costs compute" — [Dream Agents](https://dreamagents.substack.com/p/ai-video-goes-real-time-making-the)

### Inferences
- The per-choice video approach today forces pre-rendering (cost) and produces continuity drift; the only fixes found are structural (scene cuts that hide drift) — the same lesson as world-model memory failures.
- Netflix's exit shows hand-authored branching has a ceiling; AI promises to lift it, but no AI interactive film has shipped to replace it.

### Gaps
- No Discord/TikTok bot generating video per choice with measurable traction was found.
- "Infinite Backrooms" returned only generic image generators; no product found.
- No 2026 reporting on Showrunner's traction or new shows was found.

## Q4. Academic / open-source generative-agent sandboxes and generative-game research

### Takeaway
Research has produced the memory/planning primitives (Generative Agents' memory stream/reflection/planning, Voyager's skill library, Project Sid's 1,000-agent societies, Unbounded's LLM game engine + consistent character images) and, in 2026, benchmarks that quantify the exact failure (R2M-Bench: world models forget on revisit), but none of these is a playable game with users.

### Cited Findings
- Generative Agents (Stanford/Google, UIST 2023 Best Paper): 25 agents in Smallville; architecture = memory stream, reflection, planning; crowd evaluators found agents "more believable than humans pretending to be agents" — [ACM](https://dl.acm.org/doi/fullHtml/10.1145/3586183.3606763); [AI Business](https://aibusiness.com/nlp/generative-ai-bots-learn-to-plan-party-and-talk-politics-in-smallville-)
- AI Town (a16z-infra): open-source deployable starter kit inspired by Generative Agents; Convex backend, Llama 3 or other LLMs — [SourcePulse](https://www.sourcepulse.org/projects/1323585); [Cognitive Revolution](https://www.cognitiverevolution.ai/why-a16z-built-a-town-for-ai-people/)
- Voyager (NeurIPS 2023 / TMLR 2024): GPT-4 black-box, automatic curriculum + executable skill library + iterative prompting; 3.3x more unique items, 2.3x distance, 15.3x faster tech-tree; open source — [arXiv 2305.16291](https://arxiv.org/abs/2305.16291v2); [voyager.minedojo.org](https://voyager.minedojo.org/)
- Project Sid (Altera, now Fundamental Research Labs, fall 2024): up to 1,000 agents in Minecraft formed alliances, gem currency, a religion with "designated priests"; run lasted 4 wall-clock hours (12 in-game days) — [Tom's Guide](https://tomsguide.com/ai/a-company-gave-1000-ai-agents-access-to-minecraft-and-they-built-a-society); [Science Focus](https://www.sciencefocus.com/future-technology/ai-agents-village); [Emergence World arXiv 2606.08367](https://arxiv.org/html/2606.08367v1)
- Unbounded (arXiv 2410.18975, ICLR 2025; authors incl. Nataniel Ruiz, Michael Rubinstein): "first interactive generative infinite game" where an LLM game engine generates mechanics/narrative and a regional image-prompt adapter keeps the character visually consistent; contrasts itself with Genie/GameNGen which "mainly generate platformers with diffuse mechanics or regenerate one pre-existing game" — [arXiv](https://arxiv.org/pdf/2410.18975); [project page](https://generative-infinite-game.github.io/)
- GameGen-X: first diffusion transformer for generating and interactively controlling open-world game video (two-stage training on gameplay clips) — [awesome-game-generation](https://github.com/JingyeChen/awesome-game-generation); AnimeGamer (2025) infinite anime life sim via next-game-state prediction — [arXiv 2504.01014](https://arxiv.org/pdf/2504.01014)
- "Model as a Game" (2025) studies numerical and spatial consistency for generative games — [arXiv 2503.21172](https://arxiv.org/html/2503.21172v1)
- Open-source playable world models: Matrix-Game 2.0 (Aug 2025, 25fps, ~1,200 h UE/GTA5 data, open weights), 3.0 (Mar 2026, long-horizon memory), 3.5 (Aug 2026, 720p, patch memory); Hunyuan-GameCraft / GameCraft-2 (Nov 2025) — [GitHub Matrix-Game](https://github.com/SkyworkAI/Matrix-Game); [arXiv 2508.13009](https://arxiv.org/html/2508.13009v4); [arXiv 2511.23429](https://arxiv.org/pdf/2511.23429); AlayaWorld (2026) "long-horizon and playable video world generation" — [arXiv 2607.06291](https://arxiv.org/pdf/2607.06291)
- R2M-Bench (Aug 27 2026): 300 leave-and-return instances across 7 action-conditioned world models; "High similarity between first-visit and return frames does not necessarily show that a video world model remembered the scene"; proposes MemoryGain/NMR; NMR correlates with human judgments at ρ=0.547 — [arXiv 2608.27328](https://arxiv.org/abs/2608.27328)
- BadWorld (2026): adversarial attacks on world models (Oasis cited) — [arXiv 2606.16519](https://arxiv.org/pdf/2606.16519)
- Emergence World (2026): platform for evaluating long-horizon multi-agent autonomy, compares to Smallville and Project Sid durations — [arXiv 2606.08367](https://arxiv.org/html/2606.08367v1)
- RPGAgent (CHI 2026): multi-agent LLM system with separate narrative, scene and mechanics agents, Unity renders; designers shift to a "director" role — [ACM](https://dl.acm.org/doi/10.1145/3772318.3790326)
- Curated tracker of AI-native games — [Yuan-ManX/AI-Native-Game](https://github.com/Yuan-ManX/AI-Native-Game)

### Inferences
- The research split mirrors industry: LLM-agent sandboxes (Smallville, Sid, Voyager) have memory and goals but symbolic/engine-rendered worlds; video world models have visuals but are only now being benchmarked for memory. Unbounded and RPGAgent are the closest academic templates for "LLM engine + generated visuals."
- The 2026 appearance of memory benchmarks (R2M-Bench, Matrix-Game 3.x "memory") signals that revisit consistency is recognized as the central unsolved problem.

### Gaps
- No peer-reviewed player study of Unbounded or any Genie-like open-source clone as a *game* was found.
- Per-model R2M-Bench scores were not visible in the abstract.

## Q5. Big-company stated roadmaps (DeepMind, Microsoft, Nvidia, Tencent, NetEase, miHoYo, Sony, EA/Ubisoft)

### Takeaway
No major platform holder has announced a dated generative-world *game* product; DeepMind frames Genie as an AGI/robotics stepping stone, Microsoft's 2026 roadmap is an assistant (Gaming Copilot) rather than Muse, Nvidia's Cosmos targets physical AI, Tencent ships open models, and Sony/Ubisoft describe NPC and production tooling.

### Cited Findings
- DeepMind: world models are "a key stepping stone to AGI" via endless simulated training scenarios; Genie 3 used to generate worlds for the SIMA agent; lead author Jack Parker-Holder aims for a "Move 37 moment" for embodied agents; critics note DeepMind "doesn't yet know the model's most valuable use case" — [TechCrunch](https://techcrunch.com/2025/08/05/deepmind-reveals-genie-3-a-world-model-that-could-be-the-key-to-reaching-agi); [BDTechTalks](https://bdtechtalks.com/2025/08/07/deepmind-genie-3/); [BDTechTalks substack](https://bdtechtalks.substack.com/p/a-critical-look-at-deepminds-genie)
- Waymo World Model (Feb 2026) built on Genie 3 for robotaxi edge cases — [Wikipedia Genie](https://en.wikipedia.org/wiki/Genie_(world_model))
- a16z podcast with DeepMind Genie 3 researchers (Aug 2025) covered gaming and robotics applications — [a16z](https://a16z.com/podcast/google-deepmind-lead-researchers-on-genie-3-the-future-of-world-building/)
- Microsoft: Gaming Copilot (voice assistant, coaching, recommendations) coming to current-gen Xbox consoles in 2026, announced GDC Mar 2026; beta on mobile since May 2025; privacy concerns over default-on screenshot/OCR; next-gen hardware codename "Project Helix" — [Windows Central](https://www.windowscentral.com/gaming/xbox/microsofts-xbox-ai-assistant-gaming-copilot-is-coming-to-consoles-this-year-and-not-stopping-there); [WinBuzzer](https://winbuzzer.com/2026/03/16/microsoft-gaming-copilot-ai-xbox-consoles-2026-xcxwbn/)
- Microsoft's Feb 2025 Muse stated uses: developer ideation and game preservation ("adapting older Xbox games for modern devices"); open-sourced weights; real-time version promised via Copilot Labs — [GeekWire](https://www.geekwire.com/2025/microsoft-reveals-new-gaming-focused-generative-ai-model-muse-that-could-revive-classic-games/)
- Nvidia Cosmos 3 (May 31/Jun 1 2026): open world foundation model for physical AI (robotics, AV, vision agents), Super 32B / Nano 8B, "Cosmos Coalition" — [DataNorth](https://datanorth.ai/news/nvidia-launches-cosmos-3)
- Tencent: HY-World 2.0 (Apr 16 2026), HunyuanWorld-1.5 WorldPlay (Dec 2025); 36Kr describes Tencent/NetEase/miHoYo in a "covert technological battle" over AI games (Tencent Hunyuan Game visual platform, NetEase AI UGC in *Egg Party*, miHoYo real-time multimodal dialogue); miHoYo has used MiniMax models in *Honkai: Star Rail* since 2023 — [GitHub HunyuanWorld](https://github.com/Tencent-Hunyuan/HunyuanWorld-1.0); [36Kr](https://eu.36kr.com/en/p/3394131222956417); [Outlook Respawn](https://respawn.outlookindia.com/gaming/gaming-news/chinese-gaming-sector-backs-generative-ai-push)
- Sony: Bandai Namco generative-AI "collaborative initiative" (FY2025/26 briefing); internal Mockingbird facial-animation tool; PlayStation CEO Hideaki Nishino calls AI an "important foundational piece"; leaked internal Aloy prototype used Whisper/GPT-4/Llama 3 — [TweakTown](https://tweaktown.com/news/112457/sony-declares-ai-as-core-part-of-future-game-development-at-playstation/index.html); [letsdatascience](https://letsdatascience.com/news/playstation-launches-generative-ai-collaborative-initiative-d0365548); [ElOtroLado](https://www.elotrolado.net/noticias/juegos/playstation-ia-aloy)
- Ubisoft: CEO called AI "as big a revolution for our industry as the shift to 3D"; Neo NPCs "out of prototyping", "all our studios" working with it — [PC Gamer](https://www.pcgamer.com/gaming-industry/ubisoft-says-ai-is-as-big-a-revolution-for-our-industry-as-the-shift-to-3d-its-magical-ai-npcs-are-out-of-prototyping-and-you-bet-its-got-all-our-studios-working-with-the-tech/)
- Amazon: invested in Fable (Alexa Fund) and is preferred cloud for both Odyssey and Decart (Trainium) — [Variety](https://variety.com/2025/digital/news/netflix-of-ai-amazon-invests-fable-showrunner-launch-1236471989/); [TechCrunch Odyssey](https://techcrunch.com/2026/06/17/world-model-maker-odyssey-nabs-1-45b-valuation-backed-by-amazon-and-other-big-names/); [TheNextWeb Decart](https://thenextweb.com/news/decart-300-million-radical-ventures-world-models)
- a16z (Jonathan Lai, "14 Big Ideas for 2026"): world models "will likely give rise to not just a single game, but an entire new category of generative world experiences," e.g., a D&D-style infinite fantasy world with friends — [speedrun substack](https://speedrun.substack.com/p/14-big-ideas-for-2026)
- Forbes: VCs committed >$3B to world-model startups in H1 2026 — [Forbes](https://www.forbes.com/sites/josipamajic/2026/06/30/world-model-startups-raise-3-billion-vcs-bet-beyond-llms/)

### Inferences
- The strategic center of gravity for world models in 2026 is robotics/AV/physical AI (DeepMind-Waymo, Nvidia Cosmos, Decart "Oasis for robotics", General Intuition "agents are the product"); games are the training-data source and demo venue, not the declared product. That leaves the consumer generative-game slot open to startups.
- EA returned no generative-world announcement in searches.

### Gaps
- No NetEase or miHoYo generative *world* model product or date found.
- No dated Microsoft plan to productize Muse/WHAM found after 2025.

## Q6. Critical reception and failure modes: why these aren't "real games" yet

### Takeaway
Critics, players and researchers converge on five failure modes: visual memory/consistency collapse, latency/framerate, absence of rules and stakes ("agency illusion"), unsustainable compute cost per played minute, and rapid novelty wear-off; the only quantitative player evidence found (a 2026 Stardew Valley study, a 130-player RCT) suggests LLM NPCs raise cognitive load and can *reduce* engagement for experienced players.

### Cited Findings
**Consistency / memory**
- Oasis: "lack of object permanence"; structures vanish when the player looks away; looking at the sky "teleports" the player — [TechSpot forum](https://www.techspot.com/community/topics/oasis-is-an-interactive-ai-experience-that-turns-minecraft-into-a-nightmarish-hallucination.289027/); [KnowYourMeme](https://knowyourmeme.com/memes/ai-generated-minecraft)
- WHAMM: 0.9-second context; "looking down and then up again can leave you in a completely different place" — [GameRant](https://gamerant.com/microsoft-quake-2-ai-tech-demo-backlash-poor-performance-dev-impact/); [Yahoo/Tech](https://tech.yahoo.com/gaming/articles/fans-mock-microsofts-unplayable-ai-142134222.html)
- Odyssey preview: layouts "did not always stay the same when the viewer turned around" (TechCrunch, 2025, via aiwiki) — [aiwiki](https://aiwiki.ai/wiki/odyssey_2)
- R2M-Bench (2026) formalizes revisit memory as a distinct, under-measured property — [arXiv 2608.27328](https://arxiv.org/abs/2608.27328)

**Latency / fidelity**
- Genie 3 "too choppy" at 24fps; WHAMM ~10fps "unplayable at times"; Oasis 360p — see Q1 citations ([Wikipedia Project Genie](https://en.wikipedia.org/wiki/Project_Genie_(website)); [GameRant](https://gamerant.com/microsoft-quake-2-ai-tech-demo-backlash-poor-performance-dev-impact/))

**Agency illusion / no rules or stakes**
- Lantz: fun comes from "simple, deterministic rules that generate emergent complexity"; LLM games "short-circuit" that; generated worlds are "clunkier, sloppier versions of run-of-the-mill video games" — [Lantz](https://franklantz.substack.com/p/why-no-ai-games)
- Austin Walker on WHAMM: reveals "a fundamental misunderstanding of how games work… mimicry with holes" — [GadgetGuy](https://www.gadgetguy.com.au/game-developers-react-microsoft-quake-ii-muse-generative-ai-preservation/)
- igor'sLAB: what is called an "AI game" is "a model that predicts visual states rather than a traditional engine-based game with fixed rules" — [igorslab](https://www.igorslab.de/en/?p=307891)
- Togelius (IEEE Spectrum): "We do not have general game AI"; LLM-generated levels are "too trivial or impossible" — [IEEE Spectrum](https://spectrum.ieee.org/ai-video-games-llms-togelius)
- Hidden Door's design response: "you cannot conjure" — [Arcanum](https://arcanumrpgs.com/blog/hidden-door-review/)
- Practitioner: fully AI-generated game "just wasn't fun… a collection of features that had never met each other" — [dev.to](https://dev.to/seagamesai/my-first-ai-generated-game-looked-great-on-paper-and-boring-on-screen-5eo4)

**Cost per hour**
- WHAMM demo reportedly needed >3MW; "no perceived advantage over playing the original game while consuming considerably more energy" — [BBN Times](https://www.bbntimes.com/technology/microsoft-s-ai-powered-quake-ii-a-glimpse-of-innovation-marred-by-limitations)
- Genie session cap justified by compute cost — [Wikipedia Project Genie](https://en.wikipedia.org/wiki/Project_Genie_(website))
- Death by AI near-bankruptcy on API costs; developers "hit the model as little as possible" — [Lantz](https://franklantz.substack.com/p/why-no-ai-games)
- Suck Up! token walls — [Mason](https://medium.com/@hmason/the-state-of-ai-native-games-lessons-from-the-frontier-3e696a9e3279)
- "every single minute someone watches costs compute" — [Dream Agents](https://dreamagents.substack.com/p/ai-video-goes-real-time-making-the)

**Novelty wear-off / player studies**
- 2026 Stardew Valley LLM-NPC study: experienced players' behavioral involvement and empathy scores *fell* after LLM integration while new players' rose; authors conclude LLM NPCs interact with expectations rather than uniformly improving experience — [ACM "Beyond Pre-Defined Scripts"](https://dl.acm.org/doi/pdf/10.1145/3742413.3789221)
- 130-player randomized study: LLM NPCs raised cognitive load without significantly improving overall experience (seen via secondary index) — [Arcanum research index](https://arcanumrpgs.com/research/)
- Players "commended… prolonged, open-ended conversations" but "relayed issues related to LLM hallucinations and lack of NPC memory between interactions"; VR study: LLM "occasionally disclosed critical information prematurely, undermining the intended narrative" — [CESCG paper](https://cescg.org/wp-content/uploads/2025/04/A-Quest-for-Information-Enhancing-Game-Based-Learning-with-LLM-Driven-NPCs-2.pdf); [arXiv 2510.25820](https://arxiv.org/pdf/2510.25820)
- Player-driven emergence study (n=28): valued each playthrough feeling different; some reported repetitive responses — [arXiv 2404.17027](https://arxiv.org/pdf/2404.17027)
- Inworld survey: 52% of gamers dislike repetitive NPC dialogue (industry, not peer-reviewed) — [Curiouser Institute](https://medium.com/curiouserinstitute/ai-powered-npcs-hype-or-hallucination-11ddfc530e33)

**Audience hostility**
- "almost universal disdain for AI-generated games" in coverage of ARK's AI trailer and AI Minecraft/Quake clones — [80.lv](https://80.lv/articles/ai-generated-game-concepts-become-the-laughingstock-of-the-internet); Lantz: audience "decided, almost unanimously, that they don't want generative AI in their games" — [Lantz](https://franklantz.substack.com/p/why-no-ai-games)
- Oasis/Sora Minecraft fan reactions: "unsettling and scary", "cursed" — [Sportskeeda](https://www.sportskeeda.com/minecraft/it-s-unsettling-scary-ai-generated-minecraft-gameplay-leaves-fans-creeped)

### Inferences
- The failure modes are coupled: short memory forces short sessions, which is also what keeps cost tolerable; adding memory and length multiplies cost. A viable product likely needs a cheap persistent symbolic state (LLM/game engine) with generation layered on top, rather than pure frame prediction.
- The novelty curve evidence suggests a generated world must deliver *stakes and consequences* (which experienced players expect) rather than open conversation to retain users beyond first sessions.

### Gaps
- No longitudinal (multi-week) retention study of any LLM or world-model game was found.
- No published postmortem from a shipped world-model experience (Oasis, Genie, Odyssey) with usage metrics was found.

## Q7. Closest-concept startups (multi-agent LLM director + real-time generated video) and 2025–2026 funding

### Takeaway
No startup found combines an LLM multi-agent director/writer with real-time generated video in a playable product; the pieces exist separately (Utopai/Fable on the agentic-story side, Runway/Odyssey/Decart/PixVerse on the real-time video side, Latitude/Hidden Door on persistent text worlds), while 2026 world-model funding exceeded $3B in H1 alone and is overwhelmingly aimed at robotics/physical AI rather than games.

### Cited Findings
- Search for "AI director agents + real-time generated video + interactive story" surfaced no matching startup; closest: Utopai (agentic long-form video, film-focused), 10Six Games' *YOU vs Zombies* (personalized real-time storytelling in an action roguelite, slated Summer 2026 per Google Cloud), Jenova "Roleplay Game Master" (text), RPGAgent (academic) — [Google Cloud](https://cloud.google.com/transform/a-new-era-of-gaming-how-the-next-generation-of-play-is-being-redefined-by-ai-agents); [Wikipedia Utopai](https://en.wikipedia.org/wiki/Utopai_Studios); [ACM RPGAgent](https://dl.acm.org/doi/10.1145/3772318.3790326)
- Runway's GWM Worlds 2 explicitly lists "turn-based (visual novels)" and "real-time (games)" modes — the closest vendor positioning to the concept, but B2B contact-only — [atlasworldmodel](https://atlasworldmodel.com/gwm-worlds-2)
- PixVerse R1's shared multi-user real-time worlds with avatars (Apr 2026) is the closest shipped consumer primitive — [Bernama](https://mrem.bernama.com/viewsm.php?idm=53905)

**Funding rounds 2025–2026 (generative games / world models / interactive video)**
- AMI Labs (Yann LeCun): $1.03B seed at $3.5B (2026) — [Crunchbase News](https://news.crunchbase.com/venture/world-model-ai-lab-ami-raises-europes-largest-seed-round/)
- World Labs: $1B Feb 18 2026 at ~$5B — [valueaddvc](https://valueaddvc.com/blog/world-labs-valuation-what-fei-fei-lis-spatial-intelligence-startup-is-worth-at-5b)
- Runway: $315M Series E at $5.3B, Feb 10 2026 — [TechCrunch](https://techcrunch.com/2026/02/10/ai-video-startup-runway-raises-315m-at-5-3b-valuation-eyes-more-capable-world-models/)
- Odyssey: $310M Series B at $1.45B, Jun 17 2026 — [TechCrunch](https://techcrunch.com/2026/06/17/world-model-maker-odyssey-nabs-1-45b-valuation-backed-by-amazon-and-other-big-names/)
- Decart: $300M at ~$4B, May 18 2026 — [SiliconANGLE](https://siliconangle.com/2026/05/18/decart-raises-300m-ai-optimization-software-world-models/)
- General Intuition: $133.7M seed (Oct 2025), $320M Series A at $2.3B (Jun 2026), $220M at $6.2B (reported Oct 4 2026; backers incl. Valor, Atreides, Seven Seven Six, Point72, Khosla, General Catalyst) — [InvestGame](https://investgame.net/news/general-intuition-raises-220m-at-6-2b-as-game-clips-become-training-data-for-world-model-ai/); [GamesBeat](https://gamesbeat.com/?p=327574)
- Veeda AI (Sanja Fidler, ex-Nvidia): $90M+ seed — [Dealroom](https://dealroom.co/news/146065-ex-nvidia-researchers-raise-90m-seed-for-world-model-startup-veeda/)
- Luma AI: $900M Series C Nov 2025 (video generation) — [aifundingtracker](https://aifundingtracker.com/top-ai-video-generation-startups/)
- Worldmodeldata (UK): £7M seed to package video-game data for world models, no customer contracts yet — [TheNextWeb](https://thenextweb.com/news/worldmodeldata-7m-seed-gaming-world-models)
- Manifold AI (China) reached unicorn status within a year — [Gasgoo](https://autonews.gasgoo.com/articles/news/seeds-jumps-to-world-model-unicorn-in-one-year-manifold-ai-raises-hundreds-of-millions-in-new-funding-2068950382720778241)
- Hidden Door total $9M (pre-seed+seed) — [Tracxn](https://tracxn.com/d/companies/hidden-door/__DEEpimT5lup2Ka4OsbHxTGewc-6mqkwjQXwWx_E49y4); Ego AI $14.7M cumulative — [PitchBook](https://pitchbook.com/profiles/company/528243-13)
- Aggregate: >$3B into world-model startups in H1 2026 (Forbes); six "pure" world-model companies ~$3.05B with World Labs + AMI two-thirds of it — [Forbes](https://www.forbes.com/sites/josipamajic/2026/06/30/world-model-startups-raise-3-billion-vcs-bet-beyond-llms/); [Signals Inbox](https://signalsinbox.com/blogs/news/world-models-top-startups)
- General Intuition: "this world model isn't the product; it's the training environment (the gym)"; public-benefit corporation pledging not to replace game developers — [i-scoop](https://www.i-scoop.eu/general-intuition-bets-billions-that-video-games-can-teach-ai-to-act-in-the-real-world/)

### Inferences
- Capital is flowing to world-model *infrastructure* (video/3D/physics) whose stated customers are robotics and film; none of the well-funded labs has a story/consequence/memory layer or a game loop, so a startup that supplies the "director + persistent world state" layer on top of rented world models (Runway, Odyssey, PixVerse, open Matrix-Game/HY-World weights) would be differentiated rather than competing on pretraining.
- The economics problem is the same for every entrant: per-minute generation cost; the viable path demonstrated by survivors (Hidden Door, Latitude, PlayCYOA) is to pre-structure and cache, generating only at decision points.

### Gaps
- Could not identify any seed-stage startup explicitly pitching "LLM showrunner + real-time video game"; absence in search is not proof of absence (stealth companies likely).
- No funding data for Dynamics Lab, Fable (2026), or Bitmagic was found.
