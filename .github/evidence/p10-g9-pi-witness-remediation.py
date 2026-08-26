from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
from urllib.request import urlopen

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

repo = os.environ["GITHUB_REPOSITORY"]
head = os.environ["GITHUB_SHA"]
url = (
    f"https://raw.githubusercontent.com/{repo}/{head}/"
    ".github/evidence/p10-g9-pi-witness-remediation-base.py"
)
base = urlopen(url).read()
base_path = Path("/tmp/pi-witness-remediation-base.py")
base_path.write_bytes(base)
Path("/tmp/pi-witness-base.sha256").write_text(hashlib.sha256(base).hexdigest() + "\n")
code = compile(base, url, "exec")
globals_dict = {
    "__name__": "__main__",
    "__file__": str(base_path),
    "__package__": None,
}
exec(code, globals_dict)
