#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT))
prior = os.environ.get("PYTHONPATH")
os.environ["PYTHONPATH"] = str(ROOT) if not prior else str(ROOT) + os.pathsep + prior

runpy.run_path("/tmp/p10-g9-evidence-r4.py", run_name="__main__")
