import sys, json

data = json.load(sys.stdin)
print(f"Stars: {data['stargazers_count']:,}")
print(f"Forks: {data['forks_count']:,}")
print(f"Open Issues: {data['open_issues_count']:,}")
print(f"Last Push: {data['pushed_at'][:10]}")
print(f"Last Updated: {data['updated_at'][:10]}")
print(f"License: {data['license']['spdx_id'] if data['license'] else 'N/A'}")
