# Inception 交接文档

写于 2026-10-13，更新于 2026-10-14。覆盖 10-09 至 10-14 的全部工作。

## 一句话现状

**结论（10-14，用户已认可）：用视频模型逐帧生成行走这条路，在现有开源模型和 48 GB 卡上走到头了。** 实时的 Matrix-Game 2.0 画面会崩；不崩的 AlayaWorld、WorldPlay 系列比实时慢 4–10 倍。下一步转向"代码生成布局 + 视频模型只做重绘"，行走交给引擎实时渲染。这个新方向还没有任何代码。

Demo 跑在 **vllab14** 上，行走渲染器是 AlayaWorld：`ssh -N -L 7861:127.0.0.1:7861 wjlyu@169.236.184.113` 后打开 http://localhost:7861 。它能走、画面不崩，但走走停停：实测按住 W 40 秒，约 11 秒在动。占 3 张卡：GPU 0、1 是 AlayaWorld 行走服务（端口 18770），GPU 2 是 Wan 片段。

重启方法（在 vllab14 上）：`scripts/run_alaya_server.sh 0,1 18770`（约 40 秒加载），然后 `scripts/restart_demo.sh 2 7861`。新方向不需要这套服务时可以直接停掉，把卡还回去。

带视频的结果页：https://claude.ai/artifact/DHzor4KxU81BVjw2V8sfqv （私有，只有 wjlyu 能打开；源文件在 `results_page/`，不含 10-14 的 AlayaWorld 结果）

## 项目是什么

玩家给一张图，在生成的第一视角世界里自由走动、打字做任何事。系统推演后果、调度主线事件、记录发生过的事。设计原则是**世界状态存在结构化状态层里，视频只是渲染器**；动作成败由代码掷骰决定，LLM 只填细节。

当前实现的结构（`inception/`）：

- **GM agent**（`agents/gm.py`）：一次 DeepSeek 调用完成输入分类（action / declare / question）、裁决、成功和失败两套后果、叙述、镜头 prompt。代码事后掷骰选一支。
- **Memory**（`agents/memory.py`, `state.py`）：唯一写状态者。`state.json` 是真相源，`events.jsonl` 是事件日志，主线事件按墙上时间触发。
- **Writer**（`agents/writer.py`）：只在开局用，生成前提、风格行、隐藏真相和主线事件表。
- **Display**（`agents/display.py`）：播放缓冲。三种画面来源，优先级 动作片段 > AR 行走 > 空闲。空闲时停在最后一帧，后台生成环境片段后替换。玩家动作从输入到片段播完期间锁键；主线事件不锁键，也不在行走中触发。行走模型由一个常驻线程独占，状态始终接着上一帧，只有播完片段或丢弃预生成画面时才重新起步；站着不动时会预生成几段直走画面。
- **QC**（`agents/qc.py`）：像素统计门控，加异步的视觉模型审计（只写日志）。
- **Perception**（`orchestrator.py: _caption_view`）：当前帧变化时让视觉模型描述一句，喂给 GM，让镜头 prompt 锚定屏幕上的真实画面。
- **渲染器**（`renderers/`）：行走有 `alaya_remote.py`（现用，连 `inception/alaya_server.py` 常驻服务）和 `matrixgame2.py`；片段是 `wan_clip.py`；`mock.py` 是无 GPU 替身。由 `.env` 或环境变量 `AR_RENDERER`、`CLIP_RENDERER` 选择。
- **Web**（`web/server.py`, `web/index.html`）：FastAPI + WebSocket，界面全英文。

`agents/` 下的 `interact.py`、`prediction.py`、`prompt.py`、`film.py`、`cache.py` 以及 `app.py`、`film_server.py` 是第一版拆分式实现的遗留，不在关键路径上。`prediction.py` 里的 `StateDelta` 仍被 GM 和 Memory 引用，不能删。

## 做过的实验和结果

详细数字在 `docs/eval_results.md` 和 `docs/spike_results.md`。

### 行走渲染器

| 模型 | GPU | 速度 | 加载 | 结果 |
|---|---|---|---|---|
| Matrix-Game 2.0（demo 现用） | 1 | 13.5 fps | 约 1 分钟 | 真实照片几秒后变游戏风，约 30 秒后崩。游戏风起始图正常 |
| Wan2.2 5B 逐段接龙 | 1 | 4.8 秒 / 2 秒段 | 约 40 秒 | 约 6 秒后偏色，12 秒后崩。步数加到 20 崩得更快 |
| HY-WorldPlay 1.5（蒸馏 AR） | 4 | 2.3 fps | 约 2 分钟 | 真实照片 10 秒稳定。文字完全无效，换非蒸馏模型开 CFG 也无效 |
| WorldPlay2-Fast | 4 | 1.2 fps | 约 10 分钟 | 稳定。"鹿走到路上"有效，"下雨"只变暗 |
| AlayaWorld v1.0 | 2 | 960×544：约 1.1–3.3 fps；640×352：约 3.7 fps | 约 1 分钟 | 官方示例和自有森林照片 16 秒都稳定。"火鸟"清楚出现；"鹿"要用强一点的 prompt 才出现，且又小又远 |

没跑成的：Matrix-Game 3.0（权重下过，推理代码未开源，本机权重已删）；LongLive 2.0（公开权重只有文生视频，没有图生视频）；Yume（只看了代码，没跑）。

MG2 的两个工程改动值得保留：`renderers/_flash_attn_shim.py`（没有 flash-attn wheel 时用 SDPA 顶替），以及 `matrixgame2.py` 里只编码 33 个 latent 再复制末帧，起流从 24 秒降到约 2 秒，实测数值与完整编码相同。

### 动作片段（Wan2.2 TI2V-5B）

同样 8 句输入，视觉模型判官 0–10 分：

| 设置 | 平均分 | 每段耗时 |
|---|---|---|
| v1 prompt（描述手部动作），640×352 | 4.19 | 23 秒 |
| v2 prompt（描述结果和镜头），640×352 | 5.10 | 23 秒 |
| v2 + 2 个 seed 取优 | 5.97（同轮单 seed 5.62） | 46 秒 |
| v2，832×480 | 7.19 | 45 秒 |

v2 规则已写进 GM 的系统 prompt，832×480 已通过 `.env` 的 `CLIP_RENDER_SIZE` 启用。

规律：有东西进入画面最稳（大象 8 分左右）；手部操作一般；"物体 A 变成物体 B"做不了，GM 现在会改写成"B 从 A 后面走出来"；一句话里多个连续事件只能演第一个。

起始帧必须和 prompt 描述一致，否则全部崩（起始图不匹配时平均 0.71），这是加 Perception 环节的原因。

### GM prompt

`scripts/gm_eval.py` 的 8 句输入全部分类和裁决正确，每次 4–6 秒。这只是 8 个样本，不是系统评测。

## 没做的事

**新方向（下一步的主线）**

- **代码生成布局 + 视频模型重绘**：coding agent 写 three.js 场景承载几何、碰撞和物体状态；引擎负责实时行走；视频模型只把粗渲染重绘成照片级。玩家说"路上有头大象"就是往场景里加一个物体，挖的坑是几何上真的少一块。只讨论过，没有代码。已知风险：重绘的帧间闪烁；同一面墙两次看到纹理不同；agent 生成的布局和用户照片对不上；会动的角色需要资产。

**旧方向里停在半路的**（转向后大多不必再做，列出来备查）

- AlayaWorld 行走比实时慢约 6 倍，没有解决办法。预生成只覆盖直走，转向要从当前帧重新起步（约 5 秒）。
- 行走中没有把文字事件传给 AlayaWorld。它自己能响应"实体出现"类 prompt（见实验结果），`renderers/alaya_remote.py` 里留了 `event_prompt` 字段但没接。
- AlayaWorld 32 秒以上的 rollout 没跑成。用例 `forest_long` 已建好，10-14 在 vllab10 上试了 3 次都因为抢卡报 cuDNN 初始化失败。
- WorldPlay2 没做常驻服务（需要 4 张卡，加载 10 分钟）。

**和方向无关、仍然有用的**

- Cache（预生成常见动作）、Audio（旁白和音效）、Memory 的反思摘要。
- QC 自动重采样：现在视觉模型审计只写日志，不触发重新生成。
- 后果回写画面：挖出的坑只存在于状态里，下次经过画面上没有。新方向下这一条由几何直接解决。

## 之后的计划

1. 最小实验，约 1–2 天，需要 1–2 张卡：
   - 森林照片 → DA3 深度（环境 `.venv_alaya` 里已装好）→ 粗网格，写一个能 WASD 走的 three.js 场景，加一个大象代理体。
   - 无头渲染一条 10 秒路径的 RGB 和深度。
   - 用 Wan2.2-Fun 深度控制离线重绘，照片作参考，看闪烁和一致性。
   - 和 AlayaWorld 同路径的结果并排比（`logs/sheet_alaya_forest_352.jpg`）。
2. 离线重绘过关后，测实时重绘在 48 GB 卡上的帧率（候选：StreamDiffusionV2、Krea Realtime；Decart Lucy 是付费 API）。
3. 可行的话，把现有的 GM / Memory / Display 接到新渲染路径上：GM 的状态差分改为同时驱动场景代码；Display 的"行走"来源换成引擎画面。GM、Memory、QC、评测脚本和 Web 前端都可以原样复用。

## 机器和约束

- **不要在 vllab13 上跑 GPU 任务或 demo**（用户 10-13 明确要求，别人要用）。代码和这个会话都在 vllab13 上，CPU 工作可以。
- 可用：vllab9（`vllab9.ucmerced.edu`，169.236.184.236）、vllab10（`vllab10.ucmerced.edu`，169.236.184.153，10-14 起用户允许）、vllab12（.110）、vllab14（.113）、vllab15（.111）。**不要用 vllab11**。
- 短主机名不解析，用 IP。home 是 NFS 共享的，各机器路径相同。
- vllab14 的 GPU 是 Exclusive_Process 模式，多卡任务要用 `scripts/_rank_wrapper.sh` 让每个 rank 只看到一张卡。
- 这些机器经常被占满。`scripts/wait_gpus_and_run.sh` 会等到有 N 张真正空闲的卡再启动，失败自动重试。
- **`/home` 只有 200 GB 配额**，大文件一律放 `/ssd*/wjlyu/`。
- 重启 7861 的 demo 不需要问用户。

## 文件在哪里

### 代码（`/home/wjlyu/Inception`，NFS）

| 路径 | 内容 |
|---|---|
| `inception/` | 主程序，见上文结构 |
| `scripts/gm_eval.py`, `clip_eval.py` | 离线评测：GM 输出；Wan 渲染加判官打分 |
| `scripts/smoke_ws.py` | 对运行中的服务做端到端冒烟测试 |
| `scripts/spike_mg2.py`, `spike_wan_clip.py`, `spike_bidir_walk.py` | MG2、Wan 片段、Wan 接龙的测速脚本 |
| `scripts/spike_worldplay.sh`, `spike_worldplay2.sh`, `spike_alaya.sh` | 三个候选行走模型的运行脚本 |
| `scripts/run_alaya_server.sh`, `run_demo.sh`, `restart_demo.sh` | 启动 AlayaWorld 行走服务和 demo |
| `scripts/make_alaya_case.py`, `test_alaya_server.py` | 键盘动作串转 AlayaWorld 用例；行走服务的客户端测试 |
| `scripts/wait_gpus_and_run.sh`, `_rank_wrapper.sh`, `_queue_*.sh` | 等卡、多卡包装、排队 |
| `docs/eval_results.md`, `spike_results.md` | 实验数字和结论 |
| `reports/生成式开放世界游戏技术调研.md` | 最初的调研报告 |
| `research_notes/` | 调研的六份原始笔记 |
| `results_page/` | 结果网页的源文件和压缩视频 |
| `logs/` | 运行日志，`sheet_*.jpg` 是各实验的抽帧拼图 |
| `assets/starters/` | 起始图：MG2 自带的游戏风图和一张森林照片 |
| `.env` | 运行配置。API key 通过文件路径引用，文件在 `~/Agentese/api_keys/` |
| `~/.claude/plans/hidden-launching-grove.md` | 用户批准的 MVP 计划 |

### Python 环境（都在项目目录下）

| 环境 | 用途 |
|---|---|
| `.venv` | 主程序、MG2、Wan。py3.12，torch 2.11 |
| `.venv_wp` | HY-WorldPlay。py3.10，torch 2.6 |
| `.venv_wp2` | WorldPlay2。py3.10，torch 2.6，flash-attn 2.7.4 |
| `.venv_alaya` | AlayaWorld。py3.10，torch 必须是 2.7.1+cu128，不能装 xformers |

### 改过的第三方代码（`third_party/`，都标了 `[inception patch]`）

- `HY-WorldPlay/hyvideo/generate.py`：加 `--prompt_schedule`；进程启动即占住 GPU。
- `HY-WorldPlay/hyvideo/pipelines/worldplay_video_pipeline.py`：按块切换 prompt。
- `AlayaWorld/alaya/inference/engine.py`：环境变量 `ALAYA_TEXT_DEVICE` 把 Gemma 放到第二张卡。
- `AlayaWorld/configs/infer_pt.yaml`：新增的配置，PyTorch 注意力后端，DA3 放第二张卡。

`third_party/` 不在 git 里。这些改动的 diff 和各上游仓库的 commit 存在 `third_party_patches/`，重新 clone 上游后 `git apply` 即可恢复。

AlayaWorld 在 48 GB 卡上要加 `--compile none`，否则第 5 块编译失败后爆显存。

### 模型权重和输出

| 机器 | 路径 | 内容 | 大小 |
|---|---|---|---|
| vllab13 | `/ssd3/wjlyu/inception_models` | MG2、Wan2.2 TI2V-5B（`models/` 软链接到这里） | 52 GB |
| vllab13 | `/ssd3/wjlyu/inception_sessions` | 所有局的状态、日志、录像；`spike/` 是实验视频，`eval/` 是评测片段（`sessions/` 软链接到这里） | 25 GB |
| vllab13 | `/ssd3/wjlyu/worldplay2` | WorldPlay2-Fast 和 Wan2.2 I2V-A14B | 183 GB |
| vllab13 | `/ssd3/wjlyu/alayaworld` | AlayaWorld、v1.1 LoRA、DA3、Gemma | 70 GB |
| vllab13 | `/ssd4/wjlyu/hf_cache` | HY-WorldPlay 全套依赖，HF token | 190 GB |
| vllab14 | `/ssd3/wjlyu/hf_cache` | HY-WorldPlay 全套，含非蒸馏 AR 权重 | 153 GB |
| vllab14 | `/ssd3/wjlyu/worldplay2` | 同上 | 183 GB |
| vllab14 | `/ssd3/wjlyu/alayaworld` | 同上 | 70 GB |
| vllab14 | `/ssd3/wjlyu/inception_models/Wan-AI` | Wan2.2 TI2V-5B（demo 用） | 32 GB |
| vllab14 | `/ssd3/wjlyu/inception_sessions` | vllab14 上 demo 的各局状态和录像 | 小 |
| vllab14 | `/ssd3/wjlyu/inception_spike` | 在 vllab14 上跑出的实验视频 | 小 |
| vllab10 | `/ssd1/wjlyu/alayaworld` | AlayaWorld 全套 | 70 GB |
| vllab12 | `/ssd1/wjlyu/hf_cache` | HY-WorldPlay 全套 | 122 GB |
| vllab12 | `/ssd1/wjlyu/worldplay2` | 同上 | 183 GB |

vllab13 上的权重现在没用处了（不能在那里跑 GPU），可以删掉腾约 500 GB。转向新方向后，各机器上的 HY-WorldPlay 和 WorldPlay2 权重（合计约 800 GB）也可以删。

HF token 的副本在 `vllab13:/ssd4/wjlyu/hf_cache/token`、`vllab14:/ssd3/wjlyu/hf_cache/token`、`vllab12:/ssd1/wjlyu/hf_cache/token`。这个账号已获得 FLUX.1-Redux-dev 和 Gemma-3 的访问权限。

### 当前运行状态

vllab14 上跑着 AlayaWorld 行走服务（18770，GPU 0、1）和 demo（7861，GPU 2）。vllab10、vllab12、vllab13 上没有这个项目的进程。

## 怎么把东西跑起来

Mock 模式，不占 GPU，可在 vllab13 上跑：

```bash
cd ~/Inception
AR_RENDERER=mock CLIP_RENDERER=mock .venv/bin/python -m inception.web.server --port 7862
```

真实渲染器（AlayaWorld 行走 + Wan 片段），需要 3 张空卡，目前部署在 vllab14：

```bash
cd ~/Inception
scripts/run_alaya_server.sh 0,1 18770 > logs/alaya_server.log 2>&1 &   # 等日志出现 "model ready"
scripts/restart_demo.sh 2 7861
# 本地转发：ssh -N -L 7861:127.0.0.1:7861 wjlyu@169.236.184.113
```

换机器需要那台机器的 SSD 上有 `/ssd3/wjlyu/alayaworld` 和 `/ssd3/wjlyu/inception_models/Wan-AI`（路径不同就改 `third_party/AlayaWorld/configs/` 下的配置，vllab10 用的 `/ssd1` 版本是 `infer_pt_ssd1.yaml`）。改回 Matrix-Game 2.0 行走：`AR_RENDERER=matrixgame2`，只需 2 张卡。

离线评测：

```bash
.venv/bin/python scripts/gm_eval.py --out logs/exp/x.jsonl
INCEPTION_GPUS=<id> .venv/bin/python scripts/clip_eval.py --cases logs/exp/x.jsonl --image assets/starters/forest_path_photo.jpg --size 832x480
```

AlayaWorld 官方示例，在 vllab14 上：

```bash
cd ~/Inception && scripts/_queue_alaya.sh /ssd3/wjlyu/inception_spike/alaya2 playground/case1/case1 12 --cfg configs/infer_pt.yaml --compile none
```

## 已知的坑

- 玩家动作和主线事件共用一条 Wan 渲染队列，832×480 下每段约 45 秒，连着来会排队。玩家动作期间键盘一直锁着。
- vllab14 的 GPU 是独占模式：服务一停，卡可能马上被别人占走；别人的进程刚启动时显存接近 0，按显存判断空闲会撞车（`wait_gpus_and_run.sh` 已同时检查有无进程）。
- 在同一条 shell 命令里用 `pkill -f <模式>` 会把自己这条命令也杀掉，远程启动服务时尤其容易中招；用 pid 文件或 `scripts/restart_demo.sh`。
- 行走进入近景（树丛、墙面）后画面会卡死在特写里，所有行走模型都有，没有做回避逻辑。
- 视觉模型（OpenRouter 上的 gemini-2.5-flash）偶尔返回 schema 而不是内容，已加一次重试和降级。
- `scripts/download_models.py` 里的仓库列表是早期的，已过时。
- 结果页里 "v2 + 2 个取优" 的 5.97 和 "832×480" 的 7.19 两轮评测写进了同一个输出目录（同一秒启动），832 那轮的文件覆盖了前者的同名文件。分数来自各自的日志，是对的；但目录里的视频只代表 832 那轮。
