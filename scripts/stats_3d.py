import os, sys, json, urllib.request
from datetime import datetime, timedelta, timezone

user = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GH_USER", "YOUR_GITHUB_USERNAME")
token = os.environ.get("METRICS_TOKEN")
from zoneinfo import ZoneInfo
TZ = os.environ.get("TZ_NAME", "Asia/Kolkata")
today = datetime.now(ZoneInfo(TZ)).date()
start = today - timedelta(days=9)

def fetch():
    q = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){
    contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    body = json.dumps({"query": q, "variables": {
        "u": user, "f": f"{start - timedelta(days=1)}T00:00:00Z", "t": f"{today + timedelta(days=1)}T23:59:59Z"}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", body,
        {"Authorization": f"bearer {token}", "Content-Type": "application/json"})
    data = json.load(urllib.request.urlopen(req))
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = {d["date"]: d["contributionCount"] for w in weeks for d in w["contributionDays"]}
    print('API days:', dict(sorted(days.items())[-12:]))
    return [days.get(str(start + timedelta(days=i)), 0) for i in range(10)]

if token:
    counts = fetch()          # fail loudly in CI instead of committing fake data
else:
    print("No METRICS_TOKEN set, using sample data (local preview only)")
    counts = [0, 1, 0, 2, 0, 3, 4, 5, 0, 2]

Wd, DX, DY = 36, 14, 7        # bar width, 3D depth x, 3D depth y
BASE, STEP, X0, MAXH = 170, 70, 70, 100
mx = max(counts) or 1
f = 'font-family="Segoe UI, Ubuntu, Helvetica, Arial, sans-serif"'

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="820" height="220" viewBox="0 0 820 220" {f}>',
       '<rect width="820" height="220" rx="14" fill="#1a1b26"/>',
       '<text x="24" y="30" font-size="12" letter-spacing="1" fill="#565f89">LAST 10 DAYS · CONTRIBUTIONS</text>']

for i, c in enumerate(counts):
    h = 4 + (c / mx) * MAXH if c else 4
    x, y = X0 + i * STEP, BASE
    if c:
        top, left, right = "#b4e07f", "#9ece6a", "#6b9a45"
    else:
        top, left, right = "#3b4261", "#292e42", "#1f2335"
    svg.append(f'<polygon points="{x},{y-h} {x+DX},{y-h-DY} {x+Wd+DX},{y-h-DY} {x+Wd},{y-h}" fill="{top}"/>')
    svg.append(f'<rect x="{x}" y="{y-h}" width="{Wd}" height="{h}" fill="{left}"/>')
    svg.append(f'<polygon points="{x+Wd},{y-h} {x+Wd+DX},{y-h-DY} {x+Wd+DX},{y-DY} {x+Wd},{y}" fill="{right}"/>')
    svg.append(f'<text x="{x+(Wd+DX)/2}" y="{y-h-DY-6}" text-anchor="middle" font-size="12" font-weight="700" fill="#7aa2f7">{c}</text>')
    label = (start + timedelta(days=i)).strftime("%d %b")
    svg.append(f'<text x="{x+(Wd+DX)/2}" y="{y+20}" text-anchor="middle" font-size="10" fill="#565f89">{label}</text>')

svg.append(f'<text x="804" y="210" text-anchor="end" font-size="9" fill="#414868">updated {today.strftime("%d %b %Y")}</text>')
svg.append('</svg>')
open("activity-3d.svg", "w").write("\n".join(svg))
print("Generated activity-3d.svg with", counts)
