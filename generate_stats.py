import requests
import os
import base64
from collections import defaultdict
from datetime import datetime, timedelta, timezone

# ================= AUTH =================
API_KEY = os.environ.get("WAKATIME_API_KEY")
if not API_KEY:
    raise RuntimeError("WAKATIME_API_KEY missing")

auth = base64.b64encode(f"{API_KEY}:".encode()).decode()
HEADERS = {"Authorization": f"Basic {auth}"}

# ================= TIMEZONE =================
IST = timezone(timedelta(hours=5, minutes=30))

# ================= DATE RANGE =================
end_dt = datetime.utcnow()
start_dt = end_dt - timedelta(days=7)

# 🔑 Durations API REQUIRES UNIX timestamps
start_ts = int(start_dt.timestamp())
end_ts = int(end_dt.timestamp())

URL = (
    "https://wakatime.com/api/v1/users/current/durations"
    f"?start={start_ts}&end={end_ts}"
)

resp = requests.get(URL, headers=HEADERS)
resp.raise_for_status()
durations = resp.json().get("data", [])

# ================= BUCKETS =================
phase_minutes = defaultdict(int)
weekday_minutes = defaultdict(int)

# ================= PARSE REAL DATA =================
for d in durations:
    try:
        start_utc = datetime.fromtimestamp(d["time"], tz=timezone.utc)
        local = start_utc.astimezone(IST)
        minutes = int(d["duration"] / 60)

        h = local.hour

        # ---- Phase of day ----
        if 5 <= h < 12:
            phase_minutes["Morning"] += minutes
        elif 12 <= h < 17:
            phase_minutes["Daytime"] += minutes
        elif 17 <= h < 21:
            phase_minutes["Evening"] += minutes
        else:
            phase_minutes["Night"] += minutes

        # ---- Day of week ----
        weekday_minutes[local.strftime("%A")] += minutes

    except Exception:
        continue

# ================= HELPERS =================
MAX_SCALE_MINUTES = 120  # 2 hours = full bar

def format_time(mins):
    h = mins // 60
    m = mins % 60
    return f"{h}h {m}m" if h else f"{m}m"

def bar(y, label, minutes):
    width = min(int((minutes / MAX_SCALE_MINUTES) * 260), 260)
    return f"""
    <text class="label" x="30" y="{y}">{label}</text>
    <rect class="bar-bg" x="160" y="{y-10}" width="260" height="12" rx="6"/>
    <rect class="bar" x="160" y="{y-10}" width="{width}" height="12" rx="6"/>
    <text class="value" x="460" y="{y+1}">{format_time(minutes)}</text>
    """

# ================= SVG =================
updated = datetime.now(IST).strftime("%d %b %Y • %H:%M IST")
row_h = 26
svg_height = 260 + 7 * row_h

svg = f"""
<svg width="540" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
<style>
.frame {{
  fill:#050607;
  stroke:#00ff9c22;
  stroke-width:1;
}}
.title {{
  fill:#00ff9c;
  font-family:monospace;
  font-size:13px;
  letter-spacing:1px;
}}
.label {{
  fill:#00ff9c;
  font-family:monospace;
  font-size:12px;
}}
.value {{
  fill:#eafff6;
  font-family:monospace;
  font-size:11px;
  font-weight:bold;
  text-anchor:end;
}}
.bar-bg {{ fill:#0f1a17; }}
.bar {{ fill:#00ff9c; }}
.divider {{ stroke:#00ff9c33; }}
.footer {{
  fill:#00ff9c66;
  font-family:monospace;
  font-size:10px;
}}
</style>

<rect class="frame" x="6" y="6" rx="18"
      width="528" height="{svg_height - 12}"/>

<text class="title" x="30" y="36">PHASE OF DAY</text>
"""

y = 62
for k in ["Morning", "Daytime", "Evening", "Night"]:
    svg += bar(y, k, phase_minutes[k])
    y += row_h

svg += f"""
<line class="divider" x1="30" y1="{y-10}" x2="510" y2="{y-10}"/>
<text class="title" x="30" y="{y+16}">DAYS OF WEEK</text>
"""

y += 42
for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
    svg += bar(y, d, weekday_minutes[d])
    y += row_h

svg += f"""
<text class="footer" x="30" y="{svg_height - 20}">
Last updated: {updated}
</text>
</svg>
"""

with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✅ Dashboard generated correctly (durations-based, fixed)")
