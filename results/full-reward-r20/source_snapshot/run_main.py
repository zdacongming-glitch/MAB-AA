#!/usr/bin/env python3
"""Final numerical entrypoint. All commands work directly with Python 3.11."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("NUMBA_NUM_THREADS", "1")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Run a profile, then summarize and plot")
    run.add_argument("--profile", choices=["smoke-small", "smoke-dense", "screen-all", "full", "tail"], default="smoke-small")
    run.add_argument("--output", type=Path)
    run.add_argument("--workers", default="auto")
    run.add_argument("--resume", action="store_true")
    run.add_argument("--dry-run", action="store_true", help="Print the frozen grid without executing")
    run.add_argument("--no-render", action="store_true", help="Defer analysis and figures")
    for name in ("analyze", "plot", "relative", "verify"):
        command = commands.add_parser(name)
        command.add_argument("output", type=Path)
        if name == "verify":
            command.add_argument("--check-current", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "run":
        from srcbench.runner import run
        output = args.output or ROOT / "_runs" / args.profile
        run(args.profile, output, workers=args.workers, resume=args.resume,
            dry_run=args.dry_run, render=not args.no_render)
    elif args.command == "relative":
        from srcbench.runner import verify
        from srcbench.relative_regret import analyze_relative
        verify(args.output)
        analyze_relative(args.output)
    elif args.command == "analyze":
        from srcbench.runner import verify
        from srcbench.analysis import analyze
        verify(args.output)
        analyze(args.output)
    elif args.command == "plot":
        from srcbench.runner import verify
        from srcbench.plotting import plot
        verify(args.output)
        plot(args.output)
    else:
        from srcbench.runner import verify
        print(json.dumps(verify(args.output, args.check_current), indent=2))


if __name__ == "__main__":
    main()
