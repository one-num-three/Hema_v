# Check ppt-master stats
import urllib.request, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

repos = [
    "hugohe3/ppt-master",
]

for repo in repos:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github.v3+json"}
    )
    try:
        data = json.loads(urllib.request.urlopen(req, context=ctx, timeout=10).read())
        print(f"{repo}:")
        print(f"  Stars: {data.get('stargazers_count', 'N/A')}")
        print(f"  Forks: {data.get('forks_count', 'N/A')}")
        print(f"  Open Issues: {data.get('open_issues_count', 'N/A')}")
        print(f"  Last Push: {data.get('pushed_at', 'N/A')[:10]}")
        print(f"  Created: {data.get('created_at', 'N/A')[:10]}")
        print(f"  Description: {data.get('description', 'N/A')}")
    except Exception as e:
        print(f"{repo}: Error - {e}")
