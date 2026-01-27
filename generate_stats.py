import requests
import os
from collections import defaultdict

# ========== CONFIG ==========
API_KEY = os.environ.get("WAKATIME_API_KEY")
if not API_KEY:
    raise RuntimeError("WAKATIME_API_KEY not found")

HEADERS = {
    "Authorization": f"Basic {API_KEY}"
}

URL = "https://wakatime.com/api/v1/users/current/stats/last_7_days"

# ========== FETCH DATA ==========
response = requests.get(URL, headers=HEADERS)
response.raise_for_status()
data = response.json().get("data", {})

time_blocks = defaultdict(int)
weekdays = defaultdict(int)

# ========== TIME OF DAY ==========
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

# ========== WEEKDAYS ==========
for d in data.get("days", []):
    try:
        weekdays[d["name"]] = int(d["total_seconds"] / 60)
    except Exception:
        continue

# ========== SVG BAR ==========
def bar(y, label, value, scale=2):
    width = min(max(value // scale, 4), 240)
    return f"""
    <text class="label" x="28" y="{y}">{label}</text>
    <rect class="bar-bg" x="120" y="{y-10}" width="240" height="14" rx="7"/>
    <rect class="bar" x="120" y="{y-10}" width="{width}" height="14" rx="7"/>
    <text class="value" x="{130 + width}" y="{y+1}">{value}</text>
    """

# ========== SVG BUILD ==========
svg = """
<svg width="460" height="300" viewBox="0 0 460 300"
     xmlns="http://www.w3.org/2000/svg">

<defs>
  <filter id="glow">
    <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
    <feMerge>
      <feMergeNode in="coloredBlur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
</defs>

<style>
  .bg {
    fill: #050607;
    stroke: #00ff9c;
    stroke-width: 1;
    filter: drop-shadow(0 0 12px #00ff9c55);
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
</style>

<rect class="bg" x="5" y="5" rx="18" ry="18" width="450" height="290"/>
"""

y = 42
for k in ["Morning", "Daytime", "Evening", "Night"]:
    svg += bar(y, k, time_blocks[k], scale=4)
    y += 26

y += 12
for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
    svg += bar(y, d, weekdays[d], scale=2)
    y += 26

svg += "</svg>"

# ========== WRITE FILE ==========
with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✨ Neon WakaTime dashboard generated (stats.svg)")
