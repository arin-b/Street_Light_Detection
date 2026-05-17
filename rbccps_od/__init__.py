from __future__ import annotations

import sys
from pathlib import Path
from pkgutil import extend_path

_SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

__path__ = extend_path(__path__, __name__)
