import urllib.request
import socket

print("=== Network Test ===")

# Test DNS
try:
    ip = socket.gethostbyname("github.com")
    print(f"DNS github.com -> {ip}")
except Exception as e:
    print(f"DNS FAIL: {e}")

# Test HTTPS connection
for url in [
    "https://github.com",
    "https://github.com/hugohe3/ppt-master",
    "https://api.github.com/repos/hugohe3/ppt-master/zipball/main",
]:
    try:
        r = urllib.request.urlopen(url, timeout=10)
        print(f"OK [{r.status}] {url[:50]}...")
    except Exception as e:
        print(f"FAIL {url[:50]}... : {e}")
