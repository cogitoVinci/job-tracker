from pathlib import Path
import sys

src_dir = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(src_dir))

from job_tracker.app import main

main()
