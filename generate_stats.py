import requests
import os
from collections import defaultdict

# --- CONFIG ---
API_KEY = os.environ.get("WAKATIME_API_KEY")
if not API_KEY:
    raise RuntimeError("WAKATIME_API_KEY not found in environment variables")

headers = {
    "Authorization": f"Basic {API_KEY}"
}

URL = "https://wakatime.com/api/v1/users/current/stats/last_7_days"

# --- FETCH DATA ---
response = requests.get(URL, headers=headers)
response.raise_for_status()
data = response.json().get("data", {})

# --- STORAGE ---
time_blocks = defaultdict(int)
weekdays = defaultdict(int)

# --- TIME OF DAY (Morning / Day / Evening / Night) ---
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

# --- WEEKDAYS ---
for d in data.get("days", []):
    try:
        weekdays[d["name"]] = int(d["total_seconds"] / 60)
    except Exception:
        continue


# --- SVG BAR FUNCTION ---
def bar(y, label, value, scale=2):
    width = min(max(value // scale, 2), 240)
    return f"""
    <text x="24" y="{y}">{label}</text>
    <rect x="120" y="{y-9}" width="{width}" height="10" rx="5"/>
    <text x="{130 + width}" y="{y}">{value}</text>
    """


# --- SVG BUILD ---
svg = """
<svg width="420" height="260" xmlns="http://www.w3.org/2000/svg">
<style>
text { fill:#00ff9c; font-family:monospace; font-size:12px }
rect { fill:#00ff9c }
</style>
<rect width="100%" height="100%" rx="16" fill="#050505"/>
"""

y = 36
for k in ["Morning", "Daytime", "Evening", "Night"]:
    svg += bar(y, k, time_blocks[k], scale=4)
    y += 22

y += 10
for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
    svg += bar(y, d, weekdays[d], scale=2)
    y += 22

svg += "</svg>"

# --- WRITE FILE ---
with open("stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("stats.svg generated successfully")
