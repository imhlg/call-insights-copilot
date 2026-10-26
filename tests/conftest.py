import sys
from pathlib import Path

COMMON_PATH = Path(__file__).resolve().parents[1] / "src" / "common"
sys.path.insert(0, str(COMMON_PATH))
