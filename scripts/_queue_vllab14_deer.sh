#!/usr/bin/env bash
# HY-WorldPlay prompt switch #2: an entity-appears event instead of weather.
cd /home/wjlyu/Inception
PS="4:First-person view walking along a dirt path through a dense spring forest; a large brown deer with antlers walks out of the trees onto the path right in front of the viewer and stops, looking at the camera."
W=/ssd3/wjlyu/inception_spike/wp_deer; mkdir -p "$W"
printf '%s' "First-person view walking along a dirt path through a dense spring forest; young green trees on both sides, dappled sunlight on the ground, calm and quiet." > "$W/prompt.txt"
HF_ROOT=/ssd3/wjlyu/hf_cache RESIDENT=true PROMPT_SCHEDULE="$PS" scripts/wait_gpus_and_run.sh 4 "$W/gen.mp4" -- \
  bash -c 'scripts/spike_worldplay.sh /home/wjlyu/Inception/assets/starters/forest_path_photo.jpg "w-17, right-6, w-8" 125 '"$W"' "$GPUS"'
