#!/usr/bin/env bash
# AlayaWorld case runner with auto-install of missing modules.
# Usage: scripts/spike_alaya.sh <case_prefix> <rounds> <out_dir> [gpus=4,5] [extra args...]
set -uo pipefail
CASE=$1; ROUNDS=$2; OUT=$3; GPUS=${4:-4,5}; shift 4 || shift $#
ROOT=/home/wjlyu/Inception
cd $ROOT/third_party/AlayaWorld && source $ROOT/.venv_alaya/bin/activate
mkdir -p "$OUT"
for try in 1 2 3 4 5 6 7 8; do
  echo "START try $try $(date +%T)"
  ALAYA_TEXT_DEVICE=cuda:1 PYTORCH_ALLOC_CONF=expandable_segments:True CUDA_VISIBLE_DEVICES=$GPUS \
    /usr/bin/time -v python -m inference.run --input "$CASE" --seed 1234 --rounds "$ROUNDS" --output-dir "$OUT" "$@" > "$OUT/run.log" 2>&1
  rc=$?
  echo "END try $try rc=$rc $(date +%T)"
  [ $rc -eq 0 ] && break
  m=$(grep -oP "No module named '\K[^']+" "$OUT/run.log" | tail -1)
  [ -z "$m" ] && { grep -E "Error|error:" "$OUT/run.log" | tail -3; break; }
  echo "installing missing module: $m"; uv pip install -q "${m%%.*}" 2>&1 | tail -1
done
ls -la "$OUT"
