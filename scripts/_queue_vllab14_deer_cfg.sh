#!/usr/bin/env bash
# Verification: non-distilled HY-WorldPlay AR model with CFG (guidance 6.0, 30 steps) + deer prompt switch at chunk 4.
cd /home/wjlyu/Inception
until grep -q DONE logs/dl_ar_model_vllab14.log 2>/dev/null; do sleep 15; done
S=$(ls -d /ssd3/wjlyu/hf_cache/hub/models--tencent--HY-WorldPlay/snapshots/*)
PS="4:First-person view walking along a dirt path through a dense spring forest; a large brown deer with antlers walks out of the trees onto the path right in front of the viewer and stops, looking at the camera."
W=/ssd3/wjlyu/inception_spike/wp_deer_cfg; mkdir -p "$W"
printf '%s' "First-person view walking along a dirt path through a dense spring forest; young green trees on both sides, dappled sunlight on the ground, calm and quiet." > "$W/prompt.txt"
HF_ROOT=/ssd3/wjlyu/hf_cache RESIDENT=true PROMPT_SCHEDULE="$PS" FEW_STEP=false STEPS=30 ACTION_CKPT="$S/ar_model/diffusion_pytorch_model.safetensors" \
  scripts/wait_gpus_and_run.sh 4 "$W/gen.mp4" -- \
  bash -c 'scripts/spike_worldplay.sh /home/wjlyu/Inception/assets/starters/forest_path_photo.jpg "w-17, right-6, w-8" 125 '"$W"' "$GPUS"'
