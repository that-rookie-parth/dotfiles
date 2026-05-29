#!/usr/bin/env python3
import sys
import io
import json
import math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stdin  = io.TextIOWrapper(sys.stdin.buffer,  encoding="utf-8")

def k(n):
    return f"{math.ceil(n / 1000)}k"

def colored(text, code):
    return f"\033[{code}m{text}\033[0m"

cyan   = lambda t: colored(t, "0;36")
yellow = lambda t: colored(t, "0;33")
green  = lambda t: colored(t, "0;32")
red    = lambda t: colored(t, "0;31")
dim    = lambda t: colored(t, "2")

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

parts = []

# Model name
model = (data.get("model") or {}).get("display_name", "Unknown")
parts.append(cyan(model))

# Effort level — only on reasoning models
effort = (data.get("effort") or {}).get("level")
if effort:
    parts.append(f"effort:{yellow(effort)}")

# Context usage
ctx        = data.get("context_window") or {}
used_pct   = ctx.get("used_percentage")
total_tok  = ctx.get("total_input_tokens")
ctx_size   = ctx.get("context_window_size")

if used_pct is not None and total_tok is not None and ctx_size is not None:
    pct = round(used_pct)
    pct_colored = (red if pct >= 85 else yellow if pct >= 60 else green)(f"{pct}%")
    parts.append(f"ctx:{pct_colored} ({k(total_tok)}/{k(ctx_size)})")

# Rate limits — Claude.ai subscribers only
rl      = data.get("rate_limits") or {}
five_hr = (rl.get("five_hour") or {}).get("used_percentage")
seven_d = (rl.get("seven_day")  or {}).get("used_percentage")
rate    = " ".join(filter(None, [
    f"session:{round(five_hr)}%" if five_hr is not None else None,
    f"7d:{round(seven_d)}%"      if seven_d is not None else None,
]))
if rate:
    parts.append(rate)

# Session cost
cost = (data.get("cost") or {}).get("total_cost_usd")
if cost is not None:
    parts.append(yellow(f"${cost:.3f}"))

print(dim(" │ ").join(parts), end="")
