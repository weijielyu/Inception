#!/usr/bin/env bash
# Start the resident AlayaWorld walk server on this host. Usage: run_alaya_server.sh <gpuA,gpuB> [port=8770] [cfg=configs/infer_pt_352.yaml]
GPUS=$1; PORT=${2:-8770}; CFG=${3:-configs/infer_pt_352.yaml}
cd /home/wjlyu/Inception/third_party/AlayaWorld && source ../../.venv_alaya/bin/activate
ALAYA_TEXT_DEVICE=cuda:1 PYTORCH_ALLOC_CONF=expandable_segments:True CUDA_VISIBLE_DEVICES=$GPUS \
  exec python ../../inception/alaya_server.py --cfg "$CFG" --port "$PORT"
