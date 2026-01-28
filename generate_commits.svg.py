import requests
from collections import defaultdict
from datetime import datetime, timezone, timedelta

# ===== CONFIG =====
USERNAME = "RyanV-0407"   # ← your GitHub username
MAX_SCALE_COMMITS = 20    # full bar = 20 commits
IST = timezone(timedelta(hours=5, minutes=30))

# ===== FETCH EVENTS =====
url = f"https://api.github.com/users/{USERNAME}/events/public"
headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "commit-dashboard"
}

resp = requests.get(url, headers=headers)
resp.raise_for_status()
events = resp.json()

# ===== BUCKET COMMITS =====
weekday_commits = defaultdict(int)

for e in events:
    if e.get("type") != "PushEvent":
        continue

    created = datetime.fromisoformat(
        e["created_at"].replace("Z", "+00:00")
    ).astimezone(IST)

    weekday = created.strftime("%A")
    commits = len(e["payload"].get("commits", []))
    weekday_commits[weekday] += commits

# ===== SVG HELPERS =====
def bar(y, label, value):
    width = min(int((value / MAX_SCALE_COMMITS) * 260), 260)
    return f"""
    <text class="label" x="30" y="{y}">{label}</text>
    <rect class="bar-bg" x="160" y="{y-10}" width="260" height="12" rx="6"/>
    <rect class="bar" x="160" y="{y-10}" width="{width}" height="12" rx="6"/>
    <text class="value" x="460" y="{y+1}">{value}</text>
    """

updated = datetime.now(IST).strftime("%d %b %Y • %H:%M IST")
row_h = 26
svg_height = 160 + 7 * row_h

# ===== SVG =====
svg = f"""
<svg width="540" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">
<style>
.frame {{ fill:#050607; stroke:#00ff9c22; }}
.title {{ fill:#00ff9c; font-family:monospace; font-size:13px; }}
.label {{ fill:#00ff9c; font-family:monospace; font-size:12px; }}
.value {{ fill:#eafff6; font-family:monospace; font-size:11px; text-anchor:end; }}
.bar-bg {{ fill:#0f1a17; }}
.bar {{ fill:#00ff9c; }}
.footer {{ fill:#00ff9c66; font-family:monospace; font-size:10px; }}
</style>

<rect class="frame" x="6" y="6" rx="18"
      width="528" height="{svg_height - 12}"/>

<text class="title" x="30" y="36">COMMITS BY WEEKDAY</text>
"""

y = 62
for d in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]:
    svg += bar(y, d, weekday_commits[d])
    y += row_h

svg += f"""
<text class="footer" x="30" y="{svg_height - 20}">
Last updated: {updated}
</text>
</svg>
"""

with open("commits.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✅ Commits weekday dashboard generated")
