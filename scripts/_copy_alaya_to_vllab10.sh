#!/usr/bin/env bash
rsync -a --info=progress2 /ssd3/wjlyu/alayaworld/ 169.236.184.153:/ssd1/wjlyu/alayaworld/ && echo RSYNC_DONE
