"""Run the simplified FULL against four original controls on original settings."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/"src"))
os.environ.setdefault("NUMBA_NUM_THREADS", "1")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "analyze", "plot", "verify"])
    parser.add_argument("--output", type=Path, default=ROOT/"_runs/full-reward-r20")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--check-current", action="store_true")
    args = parser.parse_args()
    from srcbench.full_reward import run, verify
    if args.command == "run":
        run(args.output, args.workers, args.resume, args.pilot, args.dry_run)
        if args.dry_run or args.no_render:
            return
    elif args.command == "verify":
        print(json.dumps(verify(args.output, args.check_current), indent=2))
        return
    from srcbench.full_reward_analysis import analyze
    analyze(args.output)


if __name__ == "__main__":
    main()
