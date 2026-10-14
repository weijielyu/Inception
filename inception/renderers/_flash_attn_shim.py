"""Minimal `flash_attn` stand-in built on torch SDPA, for GPUs/torch builds without a
prebuilt flash-attn wheel (RTX 6000 Ada + torch 2.11 here). Installed into sys.modules only
when the real package is missing. Semantics follow flash_attn 2.x:

    flash_attn_func(q, k, v, dropout_p=0, softmax_scale=None, causal=False, ...)
        q: [B, Lq, H, D]  k/v: [B, Lk, H, D]  ->  [B, Lq, H, D]
    flash_attn_varlen_func(q, k, v, cu_seqlens_q, cu_seqlens_k, max_seqlen_q, max_seqlen_k, ...)
        q: [total_q, H, D]  k/v: [total_k, H, D]  ->  [total_q, H, D]
"""
from __future__ import annotations

import importlib.machinery
import sys
import types

import torch
import torch.nn.functional as F


def _sdpa(q, k, v, causal, scale):
    # [B, L, H, D] -> [B, H, L, D]
    q, k, v = (t.transpose(1, 2) for t in (q, k, v))
    if k.shape[1] != q.shape[1]:  # GQA: repeat kv heads
        rep = q.shape[1] // k.shape[1]
        k, v = k.repeat_interleave(rep, dim=1), v.repeat_interleave(rep, dim=1)
    o = F.scaled_dot_product_attention(q, k, v, is_causal=causal, scale=scale)
    return o.transpose(1, 2)


def flash_attn_func(q, k, v, dropout_p=0.0, softmax_scale=None, causal=False, window_size=(-1, -1),
                    softcap=0.0, alibi_slopes=None, deterministic=False, return_attn_probs=False):
    out = _sdpa(q, k, v, causal, softmax_scale)
    return (out, None) if return_attn_probs else out


def flash_attn_varlen_func(q, k, v, cu_seqlens_q, cu_seqlens_k, max_seqlen_q=None, max_seqlen_k=None,
                           dropout_p=0.0, softmax_scale=None, causal=False, window_size=(-1, -1),
                           softcap=0.0, alibi_slopes=None, deterministic=False, return_attn_probs=False, **kw):
    cq = cu_seqlens_q.tolist()
    ck = cu_seqlens_k.tolist()
    outs = []
    for i in range(len(cq) - 1):
        qi = q[cq[i]:cq[i + 1]].unsqueeze(0)
        ki = k[ck[i]:ck[i + 1]].unsqueeze(0)
        vi = v[ck[i]:ck[i + 1]].unsqueeze(0)
        outs.append(_sdpa(qi, ki, vi, causal, softmax_scale)[0])
    out = torch.cat(outs, dim=0)
    return (out, None) if return_attn_probs else out


def install() -> bool:
    """Register the shim as `flash_attn` if the real package is absent. Returns True if shimmed."""
    try:
        import flash_attn  # noqa: F401
        return False
    except ModuleNotFoundError:
        mod = types.ModuleType("flash_attn")
        mod.flash_attn_func = flash_attn_func
        mod.flash_attn_varlen_func = flash_attn_varlen_func
        mod.__version__ = "0.0-sdpa-shim"
        mod.__spec__ = importlib.machinery.ModuleSpec("flash_attn", None)  # keeps importlib.util.find_spec happy
        sys.modules["flash_attn"] = mod
        return True
