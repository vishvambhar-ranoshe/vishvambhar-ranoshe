import os, json, urllib.request, urllib.error, datetime as dt

LOGIN = "vishvambhar-ranoshe"
QUERY = """query($login:String!){user(login:$login){
 repositories(ownerAffiliations:OWNER,isFork:false,first:100){nodes{stargazerCount}}
 contributionsCollection{
  totalCommitContributions
  contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""

tok = os.environ.get("METRICS_TOKEN", "")
if not tok.strip():
    raise SystemExit("METRICS_TOKEN is empty or missing")

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
    headers={"Authorization": "bearer " + tok,
             "Content-Type": "application/json", "User-Agent": "stats-card"},
)
try:
    data = json.load(urllib.request.urlopen(req))
except urllib.error.HTTPError as e:
    raise SystemExit(f"GitHub API returned {e.code}: {e.read().decode()[:200]}")
if "errors" in data:
    raise SystemExit(data["errors"])

u = data["data"]["user"]
cc = u["contributionsCollection"]
cal = cc["contributionCalendar"]
days = [d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]]

cur, i = 0, len(days) - 1
if days[i] == 0:
    i -= 1
while i >= 0 and days[i] > 0:
    cur += 1
    i -= 1
best = run = 0
for c in days:
    run = run + 1 if c > 0 else 0
    best = max(best, run)

stars = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])

stats = [
    (f'{cal["totalContributions"]:,}', "Contributions", "#7aa2f7"),
    (str(cur), "Current streak", "#bb9af7"),
    (str(best), "Longest streak", "#9ece6a"),
    (f'{cc["totalCommitContributions"]:,}', "Commits", "#2ac3de"),
    (str(stars), "Stars", "#e0af68"),
]

W, H, N = 820, 120, len(stats)
colw = W / N
parts = []
for k, (val, label, col) in enumerate(stats):
    cx = colw * k + colw / 2
    parts.append(f'<text x="{cx:.0f}" y="62" text-anchor="middle" font-size="32" font-weight="700" fill="{col}">{val}</text>')
    parts.append(f'<text x="{cx:.0f}" y="87" text-anchor="middle" font-size="12" letter-spacing="1" fill="#565f89">{label.upper()}</text>')
    if k:
        parts.append(f'<line x1="{colw * k:.0f}" y1="32" x2="{colw * k:.0f}" y2="88" stroke="#292e42"/>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Ubuntu, Helvetica, Arial, sans-serif">
<rect width="{W}" height="{H}" rx="14" fill="#1a1b26"/>
{"".join(parts)}
<text x="{W - 16}" y="{H - 10}" text-anchor="end" font-size="9" fill="#414868">last 12 months, updated {dt.date.today():%d %b %Y}</text>
</svg>'''
open("stats-card.svg", "w", encoding="utf-8").write(svg)
print("written", len(days), "days, current streak", cur)
