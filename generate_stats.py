import requests
import os
import base64
from collections import defaultdict
from datetime import datetime

API_KEY = os.environ.get("WAKATIME_API_KEY")
if not API_KEY:
    raise RuntimeError("WAKATIME_API_KEY not found")

# ✅ CORRECT BASIC AUTH
auth_token = base64.b64encode(f"{API_KEY}:".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {auth_token}"
}

URL = "https://wakatime.com/api/v1/users/current/stats/last_7_days"
resp = requests.get(URL, headers=HEADERS)
resp.raise_for_status()
data = resp.json().get("data", {})

time_blocks = defaultdict(int)
weekdays = defaultdict(int)

# -------- Phase of Day --------
for s in data.get("summaries", []):
    try:
        hour = int(s["range"]["start"][11:13])
        minutes = int(s["grand_total"]["total_seconds"] / 60)
    except Exception:
        continue

    if 5 <= hour < 12:
        time_blocks["Morning"] += minutes
    elif 12 <= hour < 17:
        time_blocks["Daytime"] += minutes
    elif 17 <= hour < 21:
        time_blocks["Evening"] += minutes
    else:
        time_blocks["Night"] += minutes

# -------- Days of Week --------
for d in data.get("days", []):
    try:
        weekdays[d["name"]] = int(d["total_seconds"] / 60)
    except Exception:
        continue


def percent(value, total):
    return round((value / total) * 100) if total > 0 else 0


def bar(y, label, value, total, highlight=False, scale=2, delay=0):
    width = min(max(value // scale, 2), 260)
    pct = percent(value, total)
    hours = round(value / 60, 2)
    cls = "bar highlight" if highlight else "bar"

    return f"""
    <text class="label" x="30" y="{y}">{label}</text>
    <rect class="bar-bg" x="160" y="{y-10}" width="260" height="12" rx="6"/>
    <rect class="{cls}" x="160" y="{y-10}" height="12" rx="6">
      <title>{hours} hrs</title>
      <animate attributeName="width"
               from="0"
               to="{width}"
               dur="0.5s"
               begin="{delay}s"
               fill="freeze"/>
    </rect>
    <text class="value" x="450" y="{y+1}">{pct}%</text>
    """


total_day = sum(time_blocks.values())
total_week = sum(weekdays.values())

today = datetime.utcnow().strftime("%A")
updated = datetime.utcnow().strftime("%d %b %Y • %H:%M UTC")

row_h = 26
svg_height = 250 + (7 * row_h)

svg = f"""
<svg width="520" height="{svg_height}" viewBox="0 0 520 {svg_height}"
     xmlns="http://www.w3.org/2000/svg">

<style>
.frame {{ fill:#050607; stroke:#00ff9c22; stroke-width:1; }}
.title {{ fill:#00ff9c; font-family:monospace; font-size:13px; letter-spacing:1px; }}
.label {{ fill:#00ff9c; font-family:monospace; font-size:12px; }}
.value {{ fill:#9fffe0; font-family:monospace; font-size:11px; text-anchor:end; }}
.bar-bg {{ fill:#0f1a17; }}
.bar {{ fill:#00ff9c; }}
.highlight {{ fill:#4dffd2; }}
.divider {{ stroke:#00ff9c33; stroke-width:1; }}
.footer {{ fill:#00ff9c66; font-family:monospace; font-size:10px; }}
</style>

<rect class="frame" x="6" y="6" rx="18" ry="18"
      width="508" height="{svg_height - 12}"/>

<text class="title" x="30" y="36">PHASE OF DAY</text>
"""

y = 62
delay = 0.05
for k in ["Morning", "Daytime", "Evening", "Night"]:
    svg += bar(y, k, time_blocks[k], total_day, scale=4, delay=delay)
    y += row_h
    delay += 0.05

svg += f"""
<line class="divider" x1="30" y1="{y-10}" x2="490" y2="{y-10}"/>
<text class="title" x="30" y="{y+16}">DAYS OF WEEK</text>
"""

y += 42
for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
    svg += bar(
        y,
        d,
        weekdays[d],
        total_week,
        highlight=(d == today),
        scale=2,
        delay=delay
    )
    y += row_h
    delay += 0.04

svg += f"""
<text class="footer" x="30" y="{svg_height - 20}">
Last updated: {updated}
</text>
</svg>
"""

with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✅ WakaTime dashboard generated with real data")
