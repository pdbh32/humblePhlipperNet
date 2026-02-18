from __future__ import annotations

import requests

from humblePhlipperPython.config import settings

BLUE = 5814783

def send(
        num_users: int,
        total_profit: int,
        combined_runtime_secs: int,
        session_runtime_sec: int) -> None:
    
    if not settings.DISCORD_WEBHOOK_URL: return

    data = {
        "content":  f"Total Profit: {_format_profit(total_profit)}",
        "username": "humblePhlipper",
        "avatar_url": "https://i.postimg.cc/W4DLDmhP/humble-Phlipper.png",
        "tts": False,
        "embeds": [
            {
                "title": "Statistics",
                "fields": [
                    {"name": "Contributing Instances", "value": str(num_users), "inline": False},
                    {"name": "Total Profit", "value": f"{total_profit:,}", "inline": False},
                    {"name": "Combined Runtime", "value": _format_runtime_sec(combined_runtime_secs), "inline": False},
                    {"name": "Session Runtime", "value": _format_runtime_sec(session_runtime_sec), "inline": False},
                    {"name": "Session gp/hr", "value": f"{total_profit / (session_runtime_sec/3600):,.0f}", "inline": False},
                ],
                "color": BLUE
            }
        ]
    }
    
    requests.post(settings.DISCORD_WEBHOOK_URL, json=data)

def _format_runtime_sec(runtime_sec: int) -> str:
    return " ".join(filter(None, [
        f"{d}d" if (d := runtime_sec // 86400) else None,
        f"{h}h" if (h := (runtime_sec % 86400) // 3600) else None,
        f"{m}m" if (m := (runtime_sec % 3600) // 60) else None,
    ])) or "0m"

def _format_profit(profit: float) -> str:
    if profit == 0:
        return "0"
    sign = "+" if profit > 0 else "-"
    a = abs(profit)
    return sign + (
        f"{a/1_000_000_000:.1f}b" if a >= 1_000_000_000 else
        f"{a/1_000_000:.1f}m"     if a >= 1_000_000 else
        f"{a/1_000:.0f}k"         if a >= 100_000 else
        f"{a/1_000:.1f}k"         if a >= 1_000 else
        f"{a:.0f}"
    )