#!/usr/bin/env bash
# Runs on vllab14: (1) HY-WorldPlay prompt-switch test, then (2) WorldPlay2 event test; each waits for 4 idle GPUs.
cd /home/wjlyu/Inception
PS="4:First-person view walking along a dirt path through a dense spring forest; the sky has turned dark grey, heavy rain is falling, big drops splashing on the leaves and the path turning to wet shiny mud, gloomy light."
W1=/ssd3/wjlyu/inception_spike/wp_rain
HF_ROOT=/ssd3/wjlyu/hf_cache RESIDENT=true PROMPT_SCHEDULE="$PS" scripts/wait_gpus_and_run.sh 4 "$W1/gen.mp4" -- \
  bash -c 'scripts/spike_worldplay.sh /home/wjlyu/Inception/assets/starters/forest_path_photo.jpg "w-17, right-6, w-8" 125 '"$W1"' "$GPUS"'
W2=/ssd3/wjlyu/inception_spike/wp2_rain
mkdir -p "$W2"
WP2_ROOT=/ssd3/wjlyu/worldplay2 scripts/wait_gpus_and_run.sh 4 "$W2/sample_000.mp4" -- \
  bash -c 'scripts/spike_worldplay2.sh /home/wjlyu/Inception/assets/starters/forest_path_photo.jpg '"$W2"' "$GPUS"'
