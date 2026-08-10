"""Make ``tests/`` importable and the working directory the repository root.

Only pytest reads this file; the standalone ``__main__`` runners in each test
module do the same job by importing ``_support`` directly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _support  # noqa: E402,F401  (imported for its path/cwd side effects)
