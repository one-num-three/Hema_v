import urllib.request, json, sys

repos = [
    ("python-pptx", "scanny/python-pptx"),
    ("PptxGenJS", "gitbrent/PptxGenJS"),
]

for name, repo in repos:
    try:
        url = f"https://api.github.com/repos/{repo}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        
        print(f"=== {name} ===")
        print(f"Stars: {data['stargazers_count']:,}")
        print(f"Forks: {data['forks_count']:,}")
        print(f"Open Issues: {data['open_issues_count']:,}")
        print(f"Created: {data['created_at'][:10]}")
        print(f"Last Push: {data['pushed_at'][:10]}")
        print(f"Last Updated: {data['updated_at'][:10]}")
        print(f"License: {data['license']['spdx_id'] if data['license'] else 'N/A'}")
        print(f"URL: {data['html_url']}")
        print(f"Description: {data['description'][:100] if data['description'] else 'N/A'}")
        print()
    except Exception as e:
        print(f"ERROR {name}: {e}")
        print()
