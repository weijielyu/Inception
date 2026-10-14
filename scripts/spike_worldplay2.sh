#!/usr/bin/env bash
# Spike: WorldPlay2-Fast (4-step AR, Wan2.2 I2V-A14B base) with scheduled text events.
# Usage: WP2_ROOT=/ssd3/wjlyu/worldplay2 scripts/spike_worldplay2.sh <image> <out_dir> <gpus=3,4,5,7>
#   Actions/prompt schedule come from env ACTION (default "w-16,right-8,w-8") and PROMPT1/PROMPT2
#   (prompt2 applies to the second half: PROMPT_EVENT="prompt1-16,prompt2-16").
set -euo pipefail
IMG=$1; OUT=$2; GPUS=${3:-3,4,5,7}
ROOT=/home/wjlyu/Inception
W=$ROOT/third_party/WorldPlay2
WP2_ROOT=${WP2_ROOT:-/ssd3/wjlyu/worldplay2}
NGPU=$(echo "$GPUS" | tr ',' '\n' | wc -l)
ACTION=${ACTION:-"w-16,right-8,w-8"}
PROMPT_EVENT=${PROMPT_EVENT:-"prompt1-16,prompt2-16"}
PROMPT1=${PROMPT1:-"The scene in the video is: a dirt path through a dense spring forest, young green trees on both sides, dappled sunlight."}
PROMPT2=${PROMPT2:-"The scene in the video is: a dirt path through a dense spring forest, young green trees on both sides. The event is: dark clouds gather and heavy rain begins to fall, the path turns to wet mud."}
PROMPT3=${PROMPT3:-}
mkdir -p "$OUT"
cp "$IMG" "$OUT/input.jpg"
cat > "$OUT/input.json" <<EOF
[
  {"image_path": "input.jpg", "perspective": "fps", "action": "$ACTION", "prompt_event": "$PROMPT_EVENT",
   "prompt1": "$PROMPT1", "prompt2": "$PROMPT2"$( [ -n "$PROMPT3" ] && printf ', "prompt3": "%s"' "$PROMPT3" ), "output_name": "sample_000"}
]
EOF
cd "$W"
source "$ROOT/.venv_wp2/bin/activate"
export PYTHONPATH=$W:${PYTHONPATH:-}
export RANK_GPUS=$GPUS; unset CUDA_VISIBLE_DEVICES    # one GPU per rank (Exclusive_Process-safe)
echo "image=$IMG gpus=$GPUS action=$ACTION events=$PROMPT_EVENT"; date +%T
/usr/bin/time -v torchrun --standalone --nproc_per_node="$NGPU" --no-python "$ROOT/scripts/_rank_wrapper.sh" python generate.py \
  --inference_mode pdd --attention_backend "${ATTENTION_BACKEND:-flash}" \
  --ckpt_dir "$WP2_ROOT/Wan2.2-I2V-A14B" \
  --low_noise_mem_ckpt "$WP2_ROOT/WorldPlay2-Fast/low_noise_model/diffusion_pytorch_model.safetensors" \
  --high_noise_mem_ckpt "$WP2_ROOT/WorldPlay2-Fast/high_noise_model/diffusion_pytorch_model.safetensors" \
  --input_json "$OUT/input.json" --yaw_rotation_speed_deg 3.0 --pitch_rotation_speed_deg 1.0 \
  --height 448 --width 832 --chunk_length 4 --sink_size 1 --temporal_size 1 \
  --sample_steps 4 --sample_shift 7.0 --sample_guide_scale 1.0 --seed 42 \
  --dit_fsdp --t5_fsdp --ulysses_size "$NGPU" --output_dir "$OUT" \
  2>&1 | tee "$OUT/run.log" | grep -v -i -E "warn|it/s\]" | tail -40
date +%T; ls -la "$OUT"
