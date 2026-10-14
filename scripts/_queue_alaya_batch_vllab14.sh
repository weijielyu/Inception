#!/usr/bin/env bash
# Sequential AlayaWorld follow-ups on vllab14: event retry + speed variants with spatial memory on.
cd /home/wjlyu/Inception; B=/ssd3/wjlyu/inception_spike
scripts/_queue_alaya.sh $B/alaya_deer2      playground/inception/forest_deer 8 --cfg configs/infer_pt.yaml --compile none --skill-sec 5.4
scripts/_queue_alaya.sh $B/alaya_cdefault   playground/inception/forest 6 --cfg configs/infer_pt.yaml --compile default --skill-sec 0
scripts/_queue_alaya.sh $B/alaya_noflex     playground/inception/forest 6 --cfg configs/infer_pt.yaml --compile none --no-flex-attn --skill-sec 0
