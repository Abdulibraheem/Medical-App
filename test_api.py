import urllib.request
import urllib.error

URL = "http://127.0.0.1:8000/patients"

try:
    with urllib.request.urlopen(URL, timeout=5) as response:
        status = response.status
        body = response.read().decode("utf-8")
        print("Status:", status)
        print("Body:")
        print(body[:1000])  # print first 1000 chars
except urllib.error.HTTPError as e:
    print("HTTP error:", e.code, e.reason)
except urllib.error.URLError as e:
    print("URL error:", e.reason)
except Exception as e:
    print("Other error:", repr(e))
