#!/usr/bin/env bash
# Start the demo web server on this host with AlayaWorld walking (server must already run) + Wan clips.
# Usage: run_demo.sh <wan_gpu> [port=7861] [alaya_url=http://127.0.0.1:18770]
cd /home/wjlyu/Inception
AR_RENDERER=alaya AR_PREFETCH_CHUNKS=${AR_PREFETCH_CHUNKS:-4} AR_BUFFER_SECONDS=8 CLIP_RENDERER=wan INCEPTION_GPUS=$1 ALAYA_URL=${3:-http://127.0.0.1:18770} \
  exec .venv/bin/python -m inception.web.server --port "${2:-7861}"
