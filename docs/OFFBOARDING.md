# Inception 交接文档

写于 2026-10-13。覆盖 10-09 至 10-13 的全部工作。

## 一句话现状

（10-14 更新）Demo 跑在 **vllab14** 上，行走渲染器已换成 AlayaWorld：`ssh -N -L 7861:127.0.0.1:7861 wjlyu@169.236.184.113` 后打开 http://localhost:7861 。占 3 张卡：GPU 0、1 是 AlayaWorld 行走服务（端口 18770），GPU 2 是 Wan 片段。行走不是实时的：每 1.33 秒画面要生成 6–10 秒，靠站着不动时预生成前进画面来缓解。

重启方法（在 vllab14 上）：`scripts/run_alaya_server.sh 0,1 18770`（约 40 秒加载），然后 `scripts/restart_demo.sh 2 7861`。

最新的方向性想法（代码生成布局 + 视频模型只做重绘）还没开始做。

带视频的结果页：https://claude.ai/artifact/DHzor4KxU81BVjw2V8sfqv （私有，只有 wjlyu 能打开；源文件在 `results_page/`，不含 10-14 的 AlayaWorld 结果）

## 项目是什么

玩家给一张图，在生成的第一视角世界里自由走动、打字做任何事。系统推演后果、调度主线事件、记录发生过的事。设计原则是**世界状态存在结构化状态层里，视频只是渲染器**；动作成败由代码掷骰决定，LLM 只填细节。

当前实现的结构（`inception/`）：

- **GM agent**（`agents/gm.py`）：一次 DeepSeek 调用完成输入分类（action / declare / question）、裁决、成功和失败两套后果、叙述、镜头 prompt。代码事后掷骰选一支。
- **Memory**（`agents/memory.py`, `state.py`）：唯一写状态者。`state.json` 是真相源，`events.jsonl` 是事件日志，主线事件按墙上时间触发。
- **Writer**（`agents/writer.py`）：只在开局用，生成前提、风格行、隐藏真相和主线事件表。
- **Display**（`agents/display.py`）：播放缓冲。三种画面来源，优先级 动作片段 > AR 行走 > 空闲。空闲时停在最后一帧，后台生成环境片段后替换。动作片段播放时锁键。
- **QC**（`agents/qc.py`）：像素统计门控，加异步的视觉模型审计（只写日志）。
- **Perception**（`orchestrator.py: _caption_view`）：当前帧变化时让视觉模型描述一句，喂给 GM，让镜头 prompt 锚定屏幕上的真实画面。
- **渲染器**（`renderers/`）：`matrixgame2.py` 行走，`wan_clip.py` 片段，`mock.py` 无 GPU 替身。
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

- **AlayaWorld 的长时间稳定性**：自有照片、键盘动作转相机轨迹（`scripts/make_alaya_case.py`）、慢块原因三项已在 10-14 验证，见 `docs/eval_results.md` 末尾。还没跑的是 32 秒以上的 rollout（`forest_long` 用例已建好，排在 vllab10 上等卡）。
- **AlayaWorld 行走的体验问题**：已接入（`inception/alaya_server.py` 常驻服务，`renderers/alaya_remote.py` 客户端，`agents/display.py` 里的前进预生成）。未解决：比实时慢约 5 倍；预生成只覆盖"直走"，一转向就要从当前帧重新起流（约 5 秒）；行走中没有把文字事件传给 AlayaWorld（`event_prompt` 字段留了但没接）。
- **WorldPlay2 常驻服务**：同上，参考 `third_party/WorldPlay2/reactor/`。需要 4 张卡。
- **代码生成布局 + 视频模型重绘**（用户 10-13 提出）：coding agent 写 three.js 场景承载几何和状态，引擎负责实时交互，视频模型只把粗渲染重绘成照片级。只讨论过，没有任何代码。建议的最小实验见下。
- **计划里后置的模块**：Cache（预生成前/左/右或常见动作）、Audio（旁白和音效）、Memory 的反思摘要。
- **QC 自动重采样**：现在视觉模型审计只写日志，不触发重新生成。
- **后果回写画面**：挖出的坑只存在于状态里，下次经过画面上没有。

## 之后的计划（建议顺序）

2. 决定方向：继续换行走模型，还是转向"代码布局 + 重绘"。用户倾向后者，尚未拍板。
3. 如果走"代码布局 + 重绘"，最小实验约 1–2 天：森林照片 → DA3 深度 → 粗网格和 three.js 场景 → 无头渲染一条 10 秒路径的 RGB 和深度 → Wan2.2-Fun 深度控制离线重绘 → 看闪烁和一致性。过关后再测实时重绘的帧率。
4. 如果继续换行走模型：先补 AlayaWorld 的三项验证，再做常驻服务，接进 Display 作为第三种来源。
5. 把 demo 部署到允许的机器上。

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
| vllab14 | `/ssd3/wjlyu/inception_spike` | 在 vllab14 上跑出的视频 | 33 MB |
| vllab12 | `/ssd1/wjlyu/hf_cache` | HY-WorldPlay 全套 | 122 GB |
| vllab12 | `/ssd1/wjlyu/worldplay2` | 同上 | 183 GB |

vllab13 上的权重现在没用处了（不能在那里跑 GPU），可以删掉腾约 500 GB。demo 要迁移的话需要先把 `inception_models` 拷到目标机器。

HF token 的副本在 `vllab13:/ssd4/wjlyu/hf_cache/token`、`vllab14:/ssd3/wjlyu/hf_cache/token`、`vllab12:/ssd1/wjlyu/hf_cache/token`。这个账号已获得 FLUX.1-Redux-dev 和 Gemma-3 的访问权限。

### 当前运行状态

vllab14 上跑着 AlayaWorld 行走服务（18770）和 demo（7861）。vllab10 上有一个等卡的排队脚本（AlayaWorld 32 秒长 rollout）。vllab13 上没有进程。

## 怎么把东西跑起来

Mock 模式，不占 GPU，可在 vllab13 上跑：

```bash
cd ~/Inception
AR_RENDERER=mock CLIP_RENDERER=mock .venv/bin/python -m inception.web.server --port 7862
```

真实渲染器，需要 2 张空卡，在允许的机器上、权重拷过去之后：

```bash
cd ~/Inception && .venv/bin/python -m inception.web.server --port 7861
# 本地转发：ssh -N -L 7861:127.0.0.1:7861 wjlyu@<那台机器>
```

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

- demo 的主线事件和玩家动作共用一条渲染队列，832×480 下每段约 45 秒，连着来会排队。
- 行走进入近景（树丛、墙面）后画面会卡死在特写里，所有行走模型都有，没有做回避逻辑。
- 视觉模型（OpenRouter 上的 gemini-2.5-flash）偶尔返回 schema 而不是内容，已加一次重试和降级。
- `scripts/download_models.py` 里的仓库列表是早期的，已过时。
- 结果页里 "v2 + 2 个取优" 的 5.97 和 "832×480" 的 7.19 两轮评测写进了同一个输出目录（同一秒启动），832 那轮的文件覆盖了前者的同名文件。分数来自各自的日志，是对的；但目录里的视频只代表 832 那轮。
