import re, os

os.chdir("F:\\hema-fix\\hema-fix")

with open("gh_pptx.html", "r", encoding="utf-8") as f:
    html = f.read()

print("=== python-pptx (scanny/python-pptx) ===")

s = re.search(r'(\d[\d,]*)\s*stars', html, re.I)
print(f"Stars: {s.group(1) if s else 'N/A'}")

f = re.search(r'(\d[\d,]*)\s*forks', html, re.I)
print(f"Forks: {f.group(1) if f else 'N/A'}")

c = re.findall(r'relative-time[^>]*>([^<]+)<', html)
print(f"Recent commit timestamps: {c[:3]}")

a = re.search(r'archived', html, re.I)
print(f"Archived: {'YES' if a else 'No'}")

con = re.search(r'(\d[\d,]*)\s*contributors', html, re.I)
print(f"Contributors: {con.group(1) if con else 'N/A'}")

desc = re.search(r'<p[^>]*itemprop=\"description\"[^>]*>([^<]+)', html)
print(f"Description: {desc.group(1).strip() if desc else 'N/A'}")
