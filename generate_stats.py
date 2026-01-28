import requests
import os
import base64
from collections import defaultdict
from datetime import datetime, timedelta

API_KEY = os.environ.get("WAKATIME_API_KEY")
if not API_KEY:
    raise RuntimeError("WAKATIME_API_KEY not found")

# ---- AUTH ----
auth = base64.b64encode(f"{API_KEY}:".encode()).decode()
HEADERS = {"Authorization": f"Basic {auth}"}

# ---- DATE RANGE (LAST 7 DAYS) ----
end = datetime.utcnow().date()
start = end - timedelta(days=6)

# ---- ENDPOINTS ----
STATS_URL = "https://wakatime.com/api/v1/users/current/stats/last_7_days"
SUM_URL = (
    "https://wakatime.com/api/v1/users/current/summaries"
    f"?start={start}&end={end}"
)

stats = requests.get(STATS_URL, headers=HEADERS).json().get("data", {})
summaries = requests.get(SUM_URL, headers=HEADERS).json().get("data", [])

time_blocks = defaultdict(int)
weekdays = defaultdict(int)

# ---- PHASE OF DAY (FROM SUMMARIES) ----
for day in summaries:
    for s in day.get("categories", []):
        if s["name"] != "Coding":
            continue

        for h in day.get("grand_total", {}).get("digital", "").split():
            pass

    for h in day.get("hours", []):
        hour = h["hour"]
        minutes = int(h["total_seconds"] / 60)

        if 5 <= hour < 12:
            time_blocks["Morning"] += minutes
        elif 12 <= hour < 17:
            time_blocks["Daytime"] += minutes
        elif 17 <= hour < 21:
            time_blocks["Evening"] += minutes
        else:
            time_blocks["Night"] += minutes

# ---- DAYS OF WEEK (FROM STATS) ----
for d in stats.get("days", []):
    weekdays[d["name"]] = int(d["total_seconds"] / 60)


def percent(value, total):
    return round((value / total) * 100) if total > 0 else 0


def bar(y, label, value, total):
    width = min(max(value // 2, 4), 260)
    pct = percent(value, total)

    return f"""
    <text class="label" x="30" y="{y}">{label}</text>
    <rect class="bar-bg" x="160" y="{y-10}" width="260" height="12" rx="6"/>
    <rect class="bar" x="160" y="{y-10}" width="{width}" height="12" rx="6"/>
    <text class="value" x="450" y="{y+1}">{pct}%</text>
    """


total_day = sum(time_blocks.values())
total_week = sum(weekdays.values())
today = datetime.utcnow().strftime("%A")
updated = datetime.utcnow().strftime("%d %b %Y • %H:%M UTC")

row_h = 26
svg_height = 260 + (7 * row_h)

svg = f"""
<svg width="520" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
<style>
.frame {{ fill:#050607; stroke:#00ff9c22; }}
.title {{ fill:#00ff9c; font-family:monospace; font-size:13px; }}
.label {{ fill:#00ff9c; font-family:monospace; font-size:12px; }}
.value {{ fill:#9fffe0; font-family:monospace; font-size:11px; text-anchor:end; }}
.bar-bg {{ fill:#0f1a17; }}
.bar {{ fill:#00ff9c; }}
.divider {{ stroke:#00ff9c33; }}
.footer {{ fill:#00ff9c66; font-family:monospace; font-size:10px; }}
</style>

<rect class="frame" x="6" y="6" rx="18" width="508" height="{svg_height - 12}"/>
<text class="title" x="30" y="36">PHASE OF DAY</text>
"""

y = 62
for k in ["Morning", "Daytime", "Evening", "Night"]:
    svg += bar(y, k, time_blocks[k], total_day)
    y += row_h

svg += f"""
<line class="divider" x1="30" y1="{y-10}" x2="490" y2="{y-10}"/>
<text class="title" x="30" y="{y+16}">DAYS OF WEEK</text>
"""

y += 42
for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
    svg += bar(y, d, weekdays[d], total_week)
    y += row_h

svg += f"""
<text class="footer" x="30" y="{svg_height - 20}">
Last updated: {updated}
</text>
</svg>
"""

with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✅ WakaTime dashboard generated with REAL data")
