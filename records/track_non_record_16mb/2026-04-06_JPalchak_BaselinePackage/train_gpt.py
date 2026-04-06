from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[3]
ROOT_TRAIN = ROOT / "train_gpt.py"

if not ROOT_TRAIN.exists():
    raise FileNotFoundError(f"Could not find root train_gpt.py at {ROOT_TRAIN}")

sys.path.insert(0, str(ROOT))
runpy.run_path(str(ROOT_TRAIN), run_name="__main__")
