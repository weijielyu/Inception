#!/usr/bin/env bash
cd /home/wjlyu/Inception
ALAYA_BANK_TAEHV=1 scripts/_queue_alaya.sh /ssd3/wjlyu/inception_spike/alaya_taehv playground/inception/forest 6 --cfg configs/infer_pt.yaml --compile none --skill-sec 0
