#!/usr/bin/env bash
# torchrun --no-python wrapper: give each rank exactly one visible GPU (needed on hosts whose GPUs
# are in Exclusive_Process compute mode, where a rank touching another rank's GPU fails).
IFS=',' read -r -a GPUS <<< "${RANK_GPUS}"
export CUDA_VISIBLE_DEVICES="${GPUS[$LOCAL_RANK]}"
export LOCAL_RANK=0   # each rank now sees exactly one device
exec "$@"
