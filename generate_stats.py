import requests
import os
from collections import defaultdict

# ================= CONFIG =================
API_KEY = os.environ.get("WAKATIME_API_KEY")
if not API_KEY:
    raise RuntimeError("WAKATIME_API_KEY not found")

HEADERS = {"Authorization": f"Basic {API_KEY}"}
URL = "https://wakatime.com/api/v1/users/current/stats/last_7_days"

# ================= FETCH =================
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

# ================= SVG BAR =================
def bar(y, label, value, scale=2, delay=0):
    width = min(max(value // scale, 4), 260)
    return f"""
    <text class="label" x="30" y="{y}">{label}</text>

    <rect class="bar-bg" x="150" y="{y-11}" width="260" height="14" rx="7"/>

    <rect class="bar" x="150" y="{y-11}" height="14" rx="7">
      <animate attributeName="width"
               from="0"
               to="{width}"
               dur="0.8s"
               begin="{delay}s"
               fill="freeze"/>
    </rect>

    <text class="value" x="{160 + width}" y="{y+1}">{value}</text>
    """

# ================= SVG BUILD =================
svg = """
<svg width="520" height="360" viewBox="0 0 520 360"
     xmlns="http://www.w3.org/2000/svg">

<defs>
  <filter id="glow">
    <feGaussianBlur stdDeviation="4" result="blur"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>

<style>
  .frame {
    fill: #050607;
    stroke: #00ff9c;
    stroke-width: 1;
    filter: drop-shadow(0 0 16px #00ff9c66);
  }

  .title {
    fill: #00ff9c;
    font-family: monospace;
    font-size: 14px;
    letter-spacing: 1px;
  }

  .label {
    fill: #00ff9c;
    font-family: monospace;
    font-size: 12px;
  }

  .value {
    fill: #0a0a0a;
    font-family: monospace;
    font-size: 11px;
  }

  .bar-bg {
    fill: #0f1a17;
  }

  .bar {
    fill: #00ff9c;
    filter: url(#glow);
  }

  .divider {
    stroke: #00ff9c44;
    stroke-width: 1;
  }
</style>

<rect class="frame" x="6" y="6" rx="20" ry="20" width="508" height="348"/>

<text class="title" x="30" y="36">PHASE OF DAY</text>
"""

y = 62
delay = 0.1
for k in ["Morning", "Daytime", "Evening", "Night"]:
    svg += bar(y, k, time_blocks[k], scale=4, delay=delay)
    y += 28
    delay += 0.08

svg += """
<line class="divider" x1="30" y1="190" x2="490" y2="190"/>
<text class="title" x="30" y="218">DAYS OF WEEK</text>
"""

y = 244
for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
    svg += bar(y, d, weekdays[d], scale=2, delay=delay)
    y += 28
    delay += 0.06

svg += "</svg>"

# ================= WRITE =================
with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("🔥 Animated WakaTime dashboard generated")
