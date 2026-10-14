#!/usr/bin/env bash
# Wait until N GPUs on this host are idle (<500 MiB used), then run a command with GPUS=<list> exported.
# Retries (re-waits) if the command fails, since other users may grab a GPU while models load.
# Usage: wait_gpus_and_run.sh <n_gpus> <done_marker_file> [max_wait_min=240] [max_tries=6] -- <command...>
#   The command sees $GPUS (e.g. "1,4,5,7"). It is considered done when <done_marker_file> exists.
set -uo pipefail
N=$1; DONE=$2; shift 2
MAXMIN=240; TRIES=6
if [ "${1:-}" != "--" ]; then MAXMIN=$1; shift; fi
if [ "${1:-}" != "--" ]; then TRIES=$1; shift; fi
[ "${1:-}" = "--" ] && shift
for ((try=1; try<=TRIES; try++)); do
  for ((t=0; t<MAXMIN*6; t++)); do
    [ -f "$DONE" ] && { echo "$(date +%T) done marker present: $DONE"; exit 0; }
    # idle = little memory used AND no compute process attached (Exclusive_Process hosts: a holder may use ~0 MiB)
    BUSY_UUIDS=$(nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader | sort -u)
    FREE=$(nvidia-smi --query-gpu=index,uuid,memory.used --format=csv,noheader,nounits | awk -F', ' -v busy="$BUSY_UUIDS" 'BEGIN{n=split(busy,b,"\n"); for(i=1;i<=n;i++) bz[b[i]]=1} $3<500 && !($2 in bz){print $1}' | head -n "$N" | paste -sd, -)
    CNT=$(echo "$FREE" | tr ',' '\n' | grep -c .)
    if [ "$CNT" -ge "$N" ]; then
      echo "$(date +%T) $(hostname) try $try: got GPUs $FREE"
      GPUS=$FREE "$@"
      [ -f "$DONE" ] && { echo "$(date +%T) success"; exit 0; }
      echo "$(date +%T) command failed (no $DONE); re-waiting"; sleep 30; break
    fi
    sleep 10
  done
done
echo "$(date +%T) giving up"; exit 1
