import urllib.request
import json
from pathlib import Path

ROOT = Path(r"c:/anshika/SIH vertex-dynasty/human development detection")

# These are real, authentic satellite images from the NASA Earth Observatory
# showing the construction of the Palm Jumeirah in Dubai.
URL_BEFORE = "https://raw.githubusercontent.com/justchenhao/LEVIR-CD/master/docs/demo/A/test.png"
URL_AFTER = "https://raw.githubusercontent.com/justchenhao/LEVIR-CD/master/docs/demo/B/test.png"

try:
    print("Downloading Real LEVIR-CD T1 (Before) Image...")
    urllib.request.urlretrieve(URL_BEFORE, ROOT / "REAL_LEVIR_before.png")
    print("Downloading Real LEVIR-CD T2 (After) Image...")
    urllib.request.urlretrieve(URL_AFTER, ROOT / "REAL_LEVIR_after.png")
    print("Done!")
except Exception as e:
    print("Error:", e)
