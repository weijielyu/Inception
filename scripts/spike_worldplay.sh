#!/usr/bin/env bash
# Spike: HY-WorldPlay (AR distilled, 480p) batch generation with a keyboard pose string.
# Usage: [HF_ROOT=...] [RESIDENT=true] [PROMPT_SCHEDULE='4:text']  scripts/spike_worldplay.sh <image> <pose> <num_frames> <out_dir> [gpus=2,3,4,5]
#   e.g. scripts/spike_worldplay.sh assets/starters/forest_path_photo.jpg 'w-20, right-6, w-10' 125 /ssd3/wjlyu/inception_sessions/spike/wp1
set -euo pipefail
IMG=$1; POSE=$2; NF=$3; OUT=$4; GPUS=${5:-2,3,4,5}
ROOT=/home/wjlyu/Inception
WP=$ROOT/third_party/HY-WorldPlay
HF_ROOT=${HF_ROOT:-/ssd4/wjlyu/hf_cache}
export HF_HOME=$HF_ROOT HF_HUB_CACHE=$HF_ROOT/hub HF_HUB_OFFLINE=1
H=$(ls -d $HF_HUB_CACHE/models--tencent--HunyuanVideo-1.5/snapshots/*)
S=$(ls -d $HF_HUB_CACHE/models--tencent--HY-WorldPlay/snapshots/*)
NGPU=$(echo $GPUS | tr ',' '\n' | wc -l)
mkdir -p "$OUT"
cd $WP
export PYTHONPATH=$WP:${PYTHONPATH:-}
export CUDA_VISIBLE_DEVICES=$GPUS
PROMPT=$(cat "$OUT/prompt.txt" 2>/dev/null || echo "A first-person view of the scene in the image; the camera moves naturally through it, consistent lighting and geometry.")
echo "image=$IMG pose='$POSE' frames=$NF gpus=$GPUS"
if [ "${PER_RANK_GPU:-1}" = "1" ]; then
  export RANK_GPUS=$GPUS; unset CUDA_VISIBLE_DEVICES
  LAUNCH="$ROOT/.venv_wp/bin/torchrun --nproc_per_node=$NGPU --master_port 29601 --no-python $ROOT/scripts/_rank_wrapper.sh $ROOT/.venv_wp/bin/python hyvideo/generate.py"
else
  LAUNCH="$ROOT/.venv_wp/bin/torchrun --nproc_per_node=$NGPU --master_port 29601 hyvideo/generate.py"
fi
/usr/bin/time -v $LAUNCH \
  --prompt "$PROMPT" --image_path "$IMG" --resolution 480p --aspect_ratio 16:9 --video_length $NF --seed 1 \
  --rewrite false --sr false --pose "$POSE" --output_path "$OUT" --prompt_schedule "${PROMPT_SCHEDULE:-}" \
  --model_path "$H" --action_ckpt "${ACTION_CKPT:-$S/ar_distilled_action_model/diffusion_pytorch_model.safetensors}" --few_step ${FEW_STEP:-true} --num_inference_steps ${STEPS:-4} --model_type ar \
  --use_vae_parallel false --use_sageattn false --use_fp8_gemm false --transformer_resident_ar_rollout ${RESIDENT:-true} \
  2>&1 | tee "$OUT/run.log" | grep -v -i -E "warn|it/s\]" | tail -40
ls -la "$OUT"
