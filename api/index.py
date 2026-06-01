from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from webapp import app  # noqa: E402

