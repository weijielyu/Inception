#!/usr/bin/env bash
# Usage: _queue_alaya.sh <out_dir> <case> <rounds> [extra inference.run args...]
OUT=$1; CASE=$2; ROUNDS=$3; shift 3
cd /home/wjlyu/Inception; mkdir -p "$OUT"; export ALAYA_ARGS="$*" OUT CASE ROUNDS
scripts/wait_gpus_and_run.sh 2 "$OUT/DONE" 720 3 -- bash -c 'scripts/spike_alaya.sh "$CASE" "$ROUNDS" "$OUT" "$GPUS" $ALAYA_ARGS && ls "$OUT"/*.mp4 >/dev/null 2>&1 && touch "$OUT/DONE"'
