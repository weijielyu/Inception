#!/usr/bin/env bash
cd /home/wjlyu/Inception
until grep -q RSYNC_DONE logs/rsync_alaya_vllab10.log 2>/dev/null; do sleep 20; done
scripts/_queue_alaya.sh /ssd1/wjlyu/inception_spike/alaya_forest_long playground/inception/forest_long 24 --cfg configs/infer_pt_ssd1.yaml --compile none --skill-sec 0
