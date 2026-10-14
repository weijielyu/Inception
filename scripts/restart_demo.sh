#!/usr/bin/env bash
# Restart the demo web server on this host. Usage: restart_demo.sh <wan_gpu> [port=7861]
cd /home/wjlyu/Inception; P=logs/demo_$(hostname).pid
[ -f $P ] && kill $(cat $P) 2>/dev/null; fuser -k ${2:-7861}/tcp 2>/dev/null; sleep 2
nohup scripts/run_demo.sh "$1" "${2:-7861}" > logs/server_$(hostname).log 2>&1 < /dev/null &
echo $! > $P; echo "demo restarted pid $(cat $P)"
