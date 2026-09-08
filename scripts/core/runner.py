from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable

from .models import DownloadPlan, DownloadResult


def execute_plan(
    plan: DownloadPlan,
    *,
    open_url: Callable[[str], None],
    wait_for_pdf: Callable[[], Path | None],
    move_to_target: Callable[[Path, Path], None],
    validate_pdf: Callable[[Path], bool],
    target_dir: Path,
    after_login: Callable[[DownloadPlan], bool] | None = None,
    browser_fallback: Callable[[DownloadPlan, Path], bool | Path | None] | None = None,
) -> DownloadResult:
    attempts: list[str] = []
    opened_article_fallback = False
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / plan.filename

    saved_path = _attempt_urls(
        plan.candidate_urls,
        attempts=attempts,
        open_url=open_url,
        wait_for_pdf=wait_for_pdf,
        move_to_target=move_to_target,
        validate_pdf=validate_pdf,
        target=target,
    )
    if saved_path:
        return DownloadResult(True, saved_path, None, attempts, opened_article_fallback)

    if plan.login_url:
        open_url(plan.login_url)
        attempts.append(plan.login_url)
        login_ok = after_login(plan) if after_login else True
        if login_ok:
            saved_path = _attempt_urls(
                plan.candidate_urls,
                attempts=attempts,
                open_url=open_url,
                wait_for_pdf=wait_for_pdf,
                move_to_target=move_to_target,
                validate_pdf=validate_pdf,
                target=target,
            )
            if saved_path:
                return DownloadResult(True, saved_path, None, attempts, opened_article_fallback)

    if plan.article_url:
        open_url(plan.article_url)
        attempts.append(plan.article_url)
        opened_article_fallback = True

    if plan.fallback_mode and browser_fallback:
        fallback_result = browser_fallback(plan, target)
        if fallback_result:
            target_path = fallback_result if isinstance(fallback_result, Path) else target
            return DownloadResult(True, target_path, None, attempts, opened_article_fallback)

    return DownloadResult(
        success=False,
        target_path=None,
        failure_reason="download_not_detected",
        attempts=attempts,
        opened_article_fallback=opened_article_fallback,
    )


def wait_for_manual_login(_: DownloadPlan) -> bool:
    if os.isatty(0):
        input("Complete the publisher or ZJU login in Edge if prompted, then press Enter to retry download...")
    else:
        time.sleep(10)
    return True


def _attempt_urls(
    urls: list[str],
    *,
    attempts: list[str],
    open_url: Callable[[str], None],
    wait_for_pdf: Callable[[], Path | None],
    move_to_target: Callable[[Path, Path], None],
    validate_pdf: Callable[[Path], bool],
    target: Path,
) -> Path | None:
    for url in urls:
        open_url(url)
        attempts.append(url)
        downloaded = wait_for_pdf()
        if downloaded is None:
            continue
        move_to_target(downloaded, target)
        if validate_pdf(target):
            return target
        if target.exists():
            target.unlink()
    return None
