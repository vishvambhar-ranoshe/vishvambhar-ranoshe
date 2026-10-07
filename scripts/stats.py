import os, json, urllib.request, datetime as dt

LOGIN = "vishvambhar-ranoshe"
QUERY = """query($login:String!){user(login:$login){
 name
 repositories(ownerAffiliation:OWNER,isFork:false,first:100){nodes{stargazerCount}}
 contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
    headers={"Authorization": "bearer " + os.environ["METRICS_TOKEN"],
             "Content-Type": "application/json", "User-Agent": "stats-card"},
)
data = json.load(urllib.request.urlopen(req))
if "errors" in data:
    raise SystemExit(data["errors"])

u = data["data"]["user"]
cal = u["contributionsCollection"]["contributionCalendar"]
weeks = cal["weeks"]
days = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]

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
name = u["name"] or LOGIN
stats = [
    (f'{cal["totalContributions"]:,}', "Contributions, last year", "#7aa2f7"),
    (str(cur), "Current streak, days", "#bb9af7"),
    (str(best), "Longest streak, days", "#9ece6a"),
    (str(stars), "Stars earned", "#e0af68"),
]
tiles = "".join(
    f'<text x="{40 + k * 190}" y="125" font-size="34" font-weight="700" fill="{col}">{v}</text>'
    f'<text x="{40 + k * 190}" y="148" font-size="12" fill="#565f89">{label}</text>'
    for k, (v, label, col) in enumerate(stats)
)

recent = weeks[-40:]
mx = max((d["contributionCount"] for w in recent for d in w["contributionDays"]), default=1) or 1
palette = ["#24283b", "#2f3d6b", "#3d59a1", "#7aa2f7", "#b4c8ff"]
cells = []
for x, w in enumerate(recent):
    for d in w["contributionDays"]:
        c = d["contributionCount"]
        lvl = 0 if c == 0 else 1 + min(3, int(4 * (c - 1) / mx))
        row = dt.date.fromisoformat(d["date"]).isoweekday() % 7
        cells.append(f'<rect x="{50 + x * 18}" y="{178 + row * 18}" width="14" height="14" rx="3" fill="{palette[lvl]}"/>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="820" height="330" viewBox="0 0 820 330" font-family="Segoe UI, Ubuntu, Helvetica, Arial, sans-serif">
<rect width="820" height="330" rx="14" fill="#1a1b26"/>
<text x="40" y="52" font-size="22" font-weight="700" fill="#c0caf5">{name}</text>
<text x="40" y="74" font-size="13" fill="#565f89">GitHub activity, updated {dt.date.today():%d %b %Y}</text>
{tiles}
<line x1="40" y1="164" x2="780" y2="164" stroke="#24283b"/>
{"".join(cells)}
</svg>'''
open("stats-card.svg", "w", encoding="utf-8").write(svg)
print("written", len(days), "days, current streak", cur)
