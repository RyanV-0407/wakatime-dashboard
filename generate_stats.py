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

SUMMARIES_URL = (
    "https://wakatime.com/api/v1/users/current/summaries"
    f"?start={start}&end={end}"
)

resp = requests.get(SUMMARIES_URL, headers=HEADERS)
resp.raise_for_status()
summaries = resp.json().get("data", [])

# ================= BUCKETS =================
phase_minutes = defaultdict(int)
weekday_minutes = defaultdict(int)

# ================= PARSE DATA =================
for entry in summaries:
    try:
        utc_time = datetime.fromisoformat(
            entry["range"]["start"].replace("Z", "+00:00")
        )
        local_time = utc_time.astimezone(IST)

        minutes = int(entry["grand_total"]["total_seconds"] / 60)

        # ---- Phase of day ----
        hour = local_time.hour
        if 5 <= hour < 12:
            phase_minutes["Morning"] += minutes
        elif 12 <= hour < 17:
            phase_minutes["Daytime"] += minutes
        elif 17 <= hour < 21:
            phase_minutes["Evening"] += minutes
        else:
            phase_minutes["Night"] += minutes

        # ---- Day of week ----
        weekday_minutes[local_time.strftime("%A")] += minutes

    except Exception:
        continue

# ================= HELPERS =================
def format_time(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"

def bar(y, label, minutes, max_minutes):
    width = int((minutes / max_minutes) * 260) if max_minutes > 0 else 0
    return f"""
    <text class="label" x="30" y="{y}">{label}</text>
    <rect class="bar-bg" x="160" y="{y-10}" width="260" height="12" rx="6"/>
    <rect class="bar" x="160" y="{y-10}" width="{width}" height="12" rx="6"/>
    <text class="value" x="450" y="{y+1}">{format_time(minutes)}</text>
    """

# ================= NORMALIZATION =================
max_phase = max(phase_minutes.values(), default=0)
max_weekday = max(weekday_minutes.values(), default=0)

updated = datetime.now(IST).strftime("%d %b %Y • %H:%M IST")

row_h = 26
svg_height = 260 + 7 * row_h

# ================= SVG =================
svg = f"""
<svg width="520" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
<style>
.frame {{ fill:#050607; stroke:#00ff9c22; stroke-width:1; }}
.title {{ fill:#00ff9c; font-family:monospace; font-size:13px; letter-spacing:1px; }}
.label {{ fill:#00ff9c; font-family:monospace; font-size:12px; }}
.value {{ fill:#9fffe0; font-family:monospace; font-size:11px; text-anchor:end; }}
.bar-bg {{ fill:#0f1a17; }}
.bar {{ fill:#00ff9c; }}
.divider {{ stroke:#00ff9c33; stroke-width:1; }}
.footer {{ fill:#00ff9c66; font-family:monospace; font-size:10px; }}
</style>

<rect class="frame" x="6" y="6" rx="18" width="508" height="{svg_height - 12}"/>

<text class="title" x="30" y="36">PHASE OF DAY</text>
"""

y = 62
for k in ["Morning", "Daytime", "Evening", "Night"]:
    svg += bar(y, k, phase_minutes[k], max_phase)
    y += row_h

svg += f"""
<line class="divider" x1="30" y1="{y-10}" x2="490" y2="{y-10}"/>
<text class="title" x="30" y="{y+16}">DAYS OF WEEK</text>
"""

y += 42
for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
    svg += bar(y, d, weekday_minutes[d], max_weekday)
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

print("✅ WakaTime dashboard generated (HOURS ONLY, no percentages)")
