"""Pick an idle GPU at startup (NVML is broken on this host, so use torch's view)."""
from __future__ import annotations

import logging
import os
import threading

import torch

log = logging.getLogger("inception.gpu")
_claimed: set[int] = set()
_lock = threading.Lock()


def pick_gpu(min_free_gb: float = 20.0) -> str:
    """Return 'cuda:N' for the emptiest GPU not yet claimed by this process.

    Honors INCEPTION_GPUS="2,3" to restrict the candidate set."""
    allowed = os.environ.get("INCEPTION_GPUS")
    cands = [int(x) for x in allowed.split(",")] if allowed else list(range(torch.cuda.device_count()))
    best, best_free = None, 0.0
    with _lock:
        for i in cands:
            if i in _claimed:
                continue
            free, total = torch.cuda.mem_get_info(i)
            free_gb = free / 1e9
            if free_gb > best_free:
                best, best_free = i, free_gb
        if best is None or best_free < min_free_gb:
            raise RuntimeError(f"no idle GPU with >= {min_free_gb} GB free (best {best_free:.0f} GB)")
        _claimed.add(best)
    log.info("claimed cuda:%d (%.0f GB free)", best, best_free)
    return f"cuda:{best}"
