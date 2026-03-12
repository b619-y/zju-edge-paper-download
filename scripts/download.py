#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from scripts.adapters import get_adapter
from scripts.core.browser import (
    DEFAULT_OUT_DIR,
    EdgeDownloadSession,
    activate_edge,
    launch_edge,
    sciencedirect_edge_fallback,
    wait_for_publisher_page,
)
from scripts.core.downloads import is_pdf, move_to_target
from scripts.core.inputs import load_inputs
from scripts.core.runner import execute_plan, wait_for_manual_login


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download PDFs through the persistent ZJU Edge session with publisher adapters."
    )
    parser.add_argument("inputs", nargs="*", help="DOI(s) or supported publisher article URL(s)")
    parser.add_argument("--from-file", type=Path, help="Text file with one DOI/URL per line")
    parser.add_argument(
        "--publisher",
        choices=["auto", "acs", "nature", "science", "sciencedirect"],
        default="auto",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout-sec", type=int, default=45)
    parser.add_argument("--login-wait-sec", type=int, default=180)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--no-login-retry",
        action="store_true",
        help="Do not open a login page when the first download attempt fails",
    )
    parser.add_argument(
        "--restart-edge",
        action="store_true",
        help="Restart only the dedicated Edge profile before downloading",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    forced_publisher = None if args.publisher == "auto" else args.publisher
    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    launch_edge(restart=args.restart_edge)
    items = load_inputs(
        args.inputs,
        args.from_file.expanduser().resolve() if args.from_file else None,
        forced_publisher=forced_publisher,
    )
    session = EdgeDownloadSession(download_dir=DEFAULT_OUT_DIR, timeout_sec=args.timeout_sec)

    failures = 0
    for item in items:
        adapter = get_adapter(item.publisher)
        plan = adapter.build_plan(item)
        if args.no_login_retry:
            plan = replace(plan, login_url=None)
        target = out_dir / plan.filename

        if target.exists() and not args.force:
            print(f"SKIP exists {target}")
            continue
        if target.exists():
            target.unlink()

        print(
            f"DOWNLOAD_START publisher={plan.publisher} label={plan.label} "
            f"mode={plan.primary_mode} support={plan.support_level}"
        )
        result = execute_plan(
            plan,
            open_url=session.open_url,
            wait_for_pdf=session.wait_for_pdf,
            move_to_target=move_to_target,
            validate_pdf=is_pdf,
            target_dir=out_dir,
            after_login=lambda current_plan: _after_login(current_plan, args.login_wait_sec),
            browser_fallback=lambda current_plan, target: _browser_fallback(
                current_plan,
                target,
                session=session,
                login_wait_sec=args.login_wait_sec,
            ),
        )

        if result.success and result.target_path:
            print(f"SAVED publisher={plan.publisher} path={result.target_path}")
            continue

        failures += 1
        attempts = ",".join(result.attempts) if result.attempts else "none"
        print(
            f"DOWNLOAD_FAILED publisher={plan.publisher} label={plan.label} "
            f"reason={result.failure_reason} attempts={attempts}",
            file=sys.stderr,
        )

    return 1 if failures else 0


def _after_login(plan, timeout_sec: int) -> bool:
    activate_edge()
    wait_for_manual_login(plan)
    if plan.publisher != "acs":
        return True

    label = plan.label
    if not label:
        return True

    return wait_for_publisher_page(
        [
            f"pubs.acs.org/doi/{label}",
            f"pubs.acs.org/doi/abs/{label}",
            f"pubs.acs.org/doi/full/{label}",
            f"pubs.acs.org/doi/pdf/{label}",
        ],
        timeout_sec,
    )


def _browser_fallback(plan, target, *, session, login_wait_sec: int):
    if plan.publisher != "sciencedirect" or plan.fallback_mode != "edge_cdp":
        return None
    return sciencedirect_edge_fallback(
        plan,
        target,
        session=session,
        move_to_target=move_to_target,
        validate_pdf=is_pdf,
        timeout_sec=login_wait_sec,
    )


if __name__ == "__main__":
    raise SystemExit(main())
