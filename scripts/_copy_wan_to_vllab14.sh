#!/usr/bin/env bash
ssh -o BatchMode=yes 169.236.184.113 'mkdir -p /ssd3/wjlyu/inception_models/Wan-AI /ssd3/wjlyu/inception_sessions'
rsync -a --info=progress2 /ssd3/wjlyu/inception_models/Wan-AI/ 169.236.184.113:/ssd3/wjlyu/inception_models/Wan-AI/ && echo RSYNC_DONE
