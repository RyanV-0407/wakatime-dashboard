import requests
import os
import base64
from collections import defaultdict
from datetime import datetime, timedelta, timezone

# ========= AUTH =========
API_KEY = os.environ.get("WAKATIME_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing API key")

auth = base64.b64encode(f"{API_KEY}:".encode()).decode()
HEADERS = {"Authorization": f"Basic {auth}"}

# ========= DATE RANGE =========
end = datetime.utcnow().date()
start = end - timedelta(days=6)

URL = (
    "https://wakatime.com/api/v1/users/current/summaries"
    f"?start={start}&end={end}"
)

summaries = requests.get(URL, headers=HEADERS).json().get("data", [])

# ========= BUCKETS =========
phase_minutes = defaultdict(int)
day_minutes = defaultdict(int)

# ========= PARSE =========
for entry in summaries:
    try:
        # Parse UTC time explicitly
        start_time = datetime.fromisoformat(
            entry["range"]["start"].replace("Z", "+00:00")
        )

        minutes = int(entry["grand_total"]["total_seconds"] / 60)

        # ---- Phase of day (hour-based, correct) ----
        hour = start_time.hour
        if 5 <= hour < 12:
            phase_minutes["Morning"] += minutes
        elif 12 <= hour < 17:
            phase_minutes["Daytime"] += minutes
        elif 17 <= hour < 21:
            phase_minutes["Evening"] += minutes
        else:
            phase_minutes["Night"] += minutes

        # ---- Day of week (date-based, correct) ----
        day_key = start_time.date()
        day_minutes[day_key] += minutes

    except Exception:
        continue

# Convert date → weekday
weekday_minutes = defaultdict(int)
for day, mins in day_minutes.items():
    weekday_minutes[day.strftime("%A")] += mins

# ========= HELPERS =========
def pct(value, total):
    return round((value / total) * 100) if total > 0 else 0

def bar(y, label, percent):
    width = int(260 * percent / 100)
    return f"""
    <text class="label" x="30" y="{y}">{label}</text>
    <rect class="bar-bg" x="160" y="{y-10}" width="260" height="12" rx="6"/>
    <rect class="bar" x="160" y="{y-10}" width="{width}" height="12" rx="6"/>
    <text class="value" x="450" y="{y+1}">{percent}%</text>
    """

# ========= TOTALS =========
phase_total = sum(phase_minutes.values())
week_total = sum(weekday_minutes.values())
updated = datetime.utcnow().strftime("%d %b %Y • %H:%M UTC")

row_h = 26
svg_height = 260 + 7 * row_h

# ========= SVG =========
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
    svg += bar(y, k, pct(phase_minutes[k], phase_total))
    y += row_h

svg += f"""
<line class="divider" x1="30" y1="{y-10}" x2="490" y2="{y-10}"/>
<text class="title" x="30" y="{y+16}">DAYS OF WEEK</text>
"""

y += 42
for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
    svg += bar(y, d, pct(weekday_minutes[d], week_total))
    y += row_h

svg += f"""
<text class="footer" x="30" y="{svg_height - 20}">
Last updated: {updated}
</text>
</svg>
"""

with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✅ Dashboard generated with truthful data")
