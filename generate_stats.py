import requests
import os
import base64
from collections import defaultdict
from datetime import datetime, timedelta

# ================= AUTH =================
API_KEY = os.environ.get("WAKATIME_API_KEY")
if not API_KEY:
    raise RuntimeError("WAKATIME_API_KEY missing")

auth = base64.b64encode(f"{API_KEY}:".encode()).decode()
HEADERS = {"Authorization": f"Basic {auth}"}

# ================= DATE RANGE =================
end = datetime.utcnow().date()
start = end - timedelta(days=6)

SUMMARIES_URL = (
    "https://wakatime.com/api/v1/users/current/summaries"
    f"?start={start}&end={end}"
)

summaries = requests.get(SUMMARIES_URL, headers=HEADERS).json().get("data", [])

# ================= DATA BUCKETS =================
phase_of_day = defaultdict(int)
days_of_week = defaultdict(int)

# ================= PARSE SUMMARIES =================
for entry in summaries:
    try:
        # total minutes for that day
        minutes = int(entry["grand_total"]["total_seconds"] / 60)

        # weekday name
        day_name = datetime.fromisoformat(
            entry["range"]["start"].replace("Z", "")
        ).strftime("%A")
        days_of_week[day_name] += minutes

        # hour of activity
        hour = int(entry["range"]["start"][11:13])

        if 5 <= hour < 12:
            phase_of_day["Morning"] += minutes
        elif 12 <= hour < 17:
            phase_of_day["Daytime"] += minutes
        elif 17 <= hour < 21:
            phase_of_day["Evening"] += minutes
        else:
            phase_of_day["Night"] += minutes

    except Exception:
        continue


# ================= HELPERS =================
def percent(v, t):
    return round((v / t) * 100) if t > 0 else 0


def bar(y, label, value, total):
    width = min(max(value * 2, 4), 260)
    pct = percent(value, total)

    return f"""
    <text class="label" x="30" y="{y}">{label}</text>
    <rect class="bar-bg" x="160" y="{y-10}" width="260" height="12" rx="6"/>
    <rect class="bar" x="160" y="{y-10}" width="{width}" height="12" rx="6"/>
    <text class="value" x="450" y="{y+1}">{pct}%</text>
    """


# ================= TOTALS =================
total_phase = sum(phase_of_day.values())
total_week = sum(days_of_week.values())
updated = datetime.utcnow().strftime("%d %b %Y • %H:%M UTC")

row_h = 26
svg_height = 260 + 7 * row_h

# ================= SVG =================
svg = f"""
<svg width="520" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
<style>
.frame {{ fill:#050607; stroke:#00ff9c22; }}
.title {{ fill:#00ff9c; font-family:monospace; font-size:13px; letter-spacing:1px; }}
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
    svg += bar(y, k, phase_of_day[k], total_phase)
    y += row_h

svg += f"""
<line class="divider" x1="30" y1="{y-10}" x2="490" y2="{y-10}"/>
<text class="title" x="30" y="{y+16}">DAYS OF WEEK</text>
"""

y += 42
for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
    svg += bar(y, d, days_of_week[d], total_week)
    y += row_h

svg += f"""
<text class="footer" x="30" y="{svg_height - 20}">
Last updated: {updated}
</text>
</svg>
"""

# ================= WRITE =================
with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✅ WakaTime dashboard generated correctly")
