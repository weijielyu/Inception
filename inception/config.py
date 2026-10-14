"""Runtime configuration. Everything comes from environment variables / .env so that
providers and backends can be swapped without touching code."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _read_key(env_name: str) -> str | None:
    """Return an API key from ENV, or from a file named by ENV_FILE (never logged)."""
    val = os.environ.get(env_name)
    if val:
        return val.strip()
    file_var = os.environ.get(env_name + "_FILE")
    if file_var and Path(file_var).expanduser().exists():
        return Path(file_var).expanduser().read_text().strip()
    return None


class Settings:
    # ---- LLM (text agents) ----
    # "deepseek" (OpenAI-compatible) or "anthropic" (official SDK)
    llm_provider: str = os.environ.get("LLM_PROVIDER", "deepseek")
    deepseek_api_key: str | None = _read_key("DEEPSEEK_API_KEY")
    deepseek_base_url: str = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    anthropic_model: str = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5-5")
    anthropic_effort: str = os.environ.get("ANTHROPIC_EFFORT", "low")

    # ---- Vision judge (QC agent / scene captioning) ----
    # "openrouter" (any VLM behind an OpenAI-compatible API), "anthropic", or "none"
    vlm_provider: str = os.environ.get("VLM_PROVIDER", "openrouter")
    openrouter_api_key: str | None = _read_key("OPENROUTER_API_KEY")
    openrouter_base_url: str = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    vlm_model: str = os.environ.get("VLM_MODEL", "google/gemini-2.5-flash")

    # ---- Film (video generation) ----
    # "mock" (no GPU, PIL zoom clip) or "http" (talk to inception.film_server)
    film_backend: str = os.environ.get("FILM_BACKEND", "mock")
    film_server_url: str = os.environ.get("FILM_SERVER_URL", "http://127.0.0.1:8765")
    video_width: int = int(os.environ.get("VIDEO_WIDTH", "640"))     # aligned with Matrix-Game 2.0
    video_height: int = int(os.environ.get("VIDEO_HEIGHT", "352"))
    video_frames: int = int(os.environ.get("VIDEO_FRAMES", "65"))
    video_fps: int = int(os.environ.get("VIDEO_FPS", "16"))
    video_steps: int = int(os.environ.get("VIDEO_STEPS", "25"))

    # ---- renderers (hybrid display) ----
    ar_renderer: str = os.environ.get("AR_RENDERER", "mock")          # mock | matrixgame2
    clip_renderer: str = os.environ.get("CLIP_RENDERER", "mock")      # mock | wan
    display_fps: int = int(os.environ.get("DISPLAY_FPS", "16"))
    clip_seconds: float = float(os.environ.get("CLIP_SECONDS", "4"))
    idle_seconds: float = float(os.environ.get("IDLE_SECONDS", "3"))
    clip_render_size: str = os.environ.get("CLIP_RENDER_SIZE", "")   # e.g. "832x480": render bigger, downscale to display
    idle_steps: int = int(os.environ.get("IDLE_STEPS", "12"))
    key_release_s: float = float(os.environ.get("KEY_RELEASE_S", "1.5"))
    mock_clip_latency_s: float = float(os.environ.get("MOCK_CLIP_LATENCY_S", "3"))
    matrixgame2_dir: str = os.environ.get("MATRIXGAME2_DIR", str(ROOT / "models/Skywork/Matrix-Game-2.0"))
    wan_model_dir: str = os.environ.get("WAN_MODEL_DIR", str(ROOT / "models/Wan-AI/Wan2.2-TI2V-5B"))

    # ---- QC / cache ----
    qc_enabled: bool = os.environ.get("QC_ENABLED", "1") == "1"
    qc_min_score: float = float(os.environ.get("QC_MIN_SCORE", "5"))
    qc_max_retries: int = int(os.environ.get("QC_MAX_RETRIES", "1"))
    cache_enabled: bool = os.environ.get("CACHE_ENABLED", "0") == "1"
    cache_top_k: int = int(os.environ.get("CACHE_TOP_K", "2"))

    narration_lang: str = os.environ.get("NARRATION_LANG", "English")
    plot_idle_pause_s: float = float(os.environ.get("PLOT_IDLE_PAUSE_S", "120"))
    record_stream: bool = os.environ.get("RECORD_STREAM", "1") == "1"
    sessions_dir: Path = Path(os.environ.get("SESSIONS_DIR", str(ROOT / "sessions")))


settings = Settings()
