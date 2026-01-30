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
end = datetime.utcnow().date()
start = end - timedelta(days=6)

URL = (
    "https://wakatime.com/api/v1/users/current/summaries"
    f"?start={start}&end={end}"
)

resp = requests.get(URL, headers=HEADERS, timeout=15)
resp.raise_for_status()
days = resp.json().get("data", [])

# ================= BUCKETS =================
phase_minutes = defaultdict(int)
weekday_minutes = defaultdict(int)

# ================= PARSE DATA =================
for day in days:
    date_str = day["range"]["start"][:10]
    local_date = datetime.fromisoformat(date_str).replace(tzinfo=IST)

    total_minutes = int(day["grand_total"]["total_seconds"] / 60)

    # --- Daytime vs Nighttime split ---
    # Assume Daytime = 08:00–20:00 (12h)
    # Nighttime = remaining hours
    daytime_minutes = int(total_minutes * 0.6)
    nighttime_minutes = total_minutes - daytime_minutes

    phase_minutes["Daytime"] += daytime_minutes
    phase_minutes["Nighttime"] += nighttime_minutes

    # --- Weekday ---
    weekday_minutes[local_date.strftime("%A")] += total_minutes

# ================= HELPERS =================
MAX_SCALE_MINUTES = 240  # 4h full bar

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
svg_height = 220 + 7 * row_h

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

<text class="title" x="30" y="36">DAYTIME vs NIGHTTIME</text>
"""

y = 62
for k in ["Daytime", "Nighttime"]:
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

print("✅ Dashboard generated (Daytime vs Nighttime)")
