import urllib.request
import zipfile
import os
import io

url = "https://api.github.com/repos/hugohe3/ppt-master/zipball/main"
target_dir = r"F:\hema-fix\ppt-master"

print(f"Downloading from {url}...")
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/vnd.github.v3+json"
})
data = urllib.request.urlopen(req, timeout=120).read()
print(f"Downloaded {len(data):,} bytes")

# Extract
print(f"Extracting to {target_dir}...")
os.makedirs(target_dir, exist_ok=True)
with zipfile.ZipFile(io.BytesIO(data)) as zf:
    # The zip has a root dir like hugohe3-ppt-master-xxx/
    members = zf.namelist()
    # Find the common prefix
    prefix = members[0].split("/")[0] + "/"
    for m in members:
        rel_path = m[len(prefix):] if m.startswith(prefix) else m
        if rel_path == "":
            continue
        dest = os.path.join(target_dir, rel_path)
        if m.endswith("/"):
            os.makedirs(dest, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with zf.open(m) as src, open(dest, "wb") as dst:
                dst.write(src.read())

print(f"Extracted {len(members)} entries to {target_dir}")
