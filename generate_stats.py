import requests
import os
from collections import defaultdict

API_KEY = os.environ.get("WAKATIME_API_KEY")
if not API_KEY:
    raise RuntimeError("WAKATIME_API_KEY not found")

HEADERS = {"Authorization": f"Basic {API_KEY}"}
URL = "https://wakatime.com/api/v1/users/current/stats/last_7_days"

data = requests.get(URL, headers=HEADERS).json().get("data", {})

time_blocks = defaultdict(int)
weekdays = defaultdict(int)

# -------- Phase of Day --------
for s in data.get("summaries", []):
    try:
        hour = int(s["range"]["start"].split("T")[1][:2])
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


def bar(y, label, value, total, scale=2, delay=0):
    width = min(max(value // scale, 2), 260)
    pct = percent(value, total)

    return f"""
    <text class="label" x="30" y="{y}">{label}</text>
    <rect class="bar-bg" x="160" y="{y-10}" width="260" height="12" rx="6"/>
    <rect class="bar" x="160" y="{y-10}" height="12" rx="6">
      <animate attributeName="width"
               from="0"
               to="{width}"
               dur="0.6s"
               begin="{delay}s"
               fill="freeze"/>
    </rect>
    <text class="value" x="450" y="{y+1}">{pct}%</text>
    """


total_day = sum(time_blocks.values())
total_week = sum(weekdays.values())

svg = """
<svg width="520" height="420" viewBox="0 0 520 420"
     xmlns="http://www.w3.org/2000/svg">

<style>
  .frame { fill:#050607; stroke:#00ff9c44; stroke-width:1; }
  .title { fill:#00ff9c; font-family:monospace; font-size:13px; letter-spacing:1px; }
  .label { fill:#00ff9c; font-family:monospace; font-size:12px; }
  .value { fill:#9fffe0; font-family:monospace; font-size:11px; text-anchor:end; }
  .bar-bg { fill:#0f1a17; }
  .bar { fill:#00ff9c; }
  .divider { stroke:#00ff9c33; stroke-width:1; }
</style>

<rect class="frame" x="6" y="6" rx="18" ry="18" width="508" height="408"/>

<text class="title" x="30" y="36">PHASE OF DAY</text>
"""

y = 62
delay = 0.05
for k in ["Morning", "Daytime", "Evening", "Night"]:
    svg += bar(y, k, time_blocks[k], total_day, scale=4, delay=delay)
    y += 26
    delay += 0.05

svg += """
<line class="divider" x1="30" y1="182" x2="490" y2="182"/>
<text class="title" x="30" y="210">DAYS OF WEEK</text>
"""

y = 236
for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
    svg += bar(y, d, weekdays[d], total_week, scale=2, delay=delay)
    y += 26
    delay += 0.04

svg += "</svg>"

with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✅ SVG generated (height fixed, real percentages)")
