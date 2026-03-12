from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

from .models import DownloadPlan
from .downloads import scan_pdfs, wait_for_pdf


EDGE_BIN = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
PROFILE_DIR = Path("/Users/b/Downloads/browser-use-local/persistent-edge/zju-edge-profile")
SKILL_DIR = Path(__file__).resolve().parents[2]
LAUNCH_SCRIPT = SKILL_DIR / "scripts" / "launch_edge.sh"
DEFAULT_OUT_DIR = Path("/Users/b/Downloads/browser-use-local/output/downloads/zju-edge-persistent/final-pdfs")
REMOTE_DEBUG_LIST_URL = "http://127.0.0.1:62777/json/list"
CDP_SCRIPT = SKILL_DIR / "scripts" / "core" / "cdp_command.js"


def launch_edge(*, restart: bool = False) -> None:
    cmd = [str(LAUNCH_SCRIPT)]
    if restart:
        cmd.append("--restart")
    subprocess.run(cmd, check=True)


def activate_edge() -> None:
    subprocess.run(
        ["osascript", "-e", 'tell application "Microsoft Edge" to activate'],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class EdgeDownloadSession:
    def __init__(self, *, download_dir: Path, timeout_sec: int) -> None:
        self.download_dir = download_dir
        self.timeout_sec = timeout_sec
        self._before = {}
        self._start_ts = time.time()
        self.arm_download_watch()

    def open_url(self, url: str) -> None:
        self.arm_download_watch()
        encoded_url = quote(url, safe=":/?&=%+#")
        req = Request(f"http://127.0.0.1:62777/json/new?{encoded_url}", method="PUT")
        with urlopen(req, timeout=5) as response:
            response.read()

    def wait_for_pdf(self) -> Path | None:
        return wait_for_pdf(self.download_dir, self._before, self._start_ts, self.timeout_sec)

    def arm_download_watch(self) -> None:
        self._before = scan_pdfs(self.download_dir)
        self._start_ts = time.time()


def fetch_debug_targets() -> list[dict]:
    try:
        with urlopen(REMOTE_DEBUG_LIST_URL, timeout=2) as response:
            return json.load(response)
    except Exception:
        return []


def wait_for_publisher_page(url_patterns: list[str], timeout_sec: int) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        targets = fetch_debug_targets()
        for target in targets:
            url = str(target.get("url", ""))
            title = str(target.get("title", ""))
            if _matches_any_pattern(url, url_patterns):
                if "error (acs publications)" in title.lower():
                    print(f"PUBLISHER_PAGE_ERROR title={title} url={url}", file=sys.stderr)
                    return False
                return True
        time.sleep(1)
    return False


def _matches_any_pattern(url: str, patterns: list[str]) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    candidate = f"{host}{parsed.path}"
    return any(pattern in candidate for pattern in patterns)


def run_cdp_command(target: dict, method: str, params: dict) -> dict:
    result = subprocess.run(
        ["node", str(CDP_SCRIPT), str(target["webSocketDebuggerUrl"]), method, json.dumps(params)],
        check=True,
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip() or "{}"
    return json.loads(output)


def find_sciencedirect_target(plan: DownloadPlan) -> dict | None:
    pii = extract_sciencedirect_pii(plan.article_url or "") or extract_sciencedirect_pii(plan.label)
    matches = []
    for target in fetch_debug_targets():
        url = str(target.get("url", ""))
        if "sciencedirect.com" not in url and "doi.org/10.1016/" not in url:
            continue
        score = 0
        if pii and pii in url:
            score += 10
        if "?via=ihub" in url:
            score += 5
        if "/abs/pii/" in url:
            score += 3
        if str(plan.article_url or "") == url:
            score += 2
        matches.append((score, target))
    if not matches:
        return None
    matches.sort(key=lambda item: item[0], reverse=True)
    return matches[0][1]


def extract_sciencedirect_pii(value: str) -> str | None:
    match = re.search(r"/pii/([^/?#]+)", value)
    if match:
        return match.group(1)
    return None


def sciencedirect_page_state(target: dict) -> dict:
    expression = """
(() => {
  const body = document.body ? document.body.innerText : "";
  const text = body || "";
  const hasAccessLink = text.includes("Access through Zhejiang University");
  const hasInstitutionAccess = text.includes("institutional Access via Zhejiang University Library")
    || text.includes("You have institutional Access via Zhejiang University Library");
  const hasPageNotFound = document.title.includes("Page not found") || text.includes("Page not found");
  const elements = [...document.querySelectorAll('a,button')].map((el) => ({
    text: (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' '),
    href: el.href || el.getAttribute('href') || '',
    disabled: Boolean(el.disabled) || el.getAttribute('aria-disabled') === 'true'
  }));
  return { hasAccessLink, hasInstitutionAccess, hasPageNotFound, elements };
})()
"""
    result = run_cdp_command(
        target,
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
    )
    return result["result"]["value"]


def cdp_click_first_matching_text(target: dict, texts: list[str]) -> bool:
    expression = f"""
(() => {{
  const patterns = {json.dumps(texts)};
  const nodes = [...document.querySelectorAll('a,button')];
  for (const node of nodes) {{
    const text = (node.innerText || node.textContent || '').trim().replace(/\\s+/g, ' ');
    const disabled = Boolean(node.disabled) || node.getAttribute('aria-disabled') === 'true';
    if (!disabled && patterns.some((pattern) => text.includes(pattern))) {{
      node.click();
      return true;
    }}
  }}
  return false;
}})()
"""
    result = run_cdp_command(
        target,
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
    )
    return bool(result["result"]["value"])


def cdp_collect_pdf_urls(target: dict) -> list[str]:
    state = sciencedirect_page_state(target)
    urls: list[str] = []
    for item in state["elements"]:
        href = str(item.get("href", "")).strip()
        text = str(item.get("text", "")).strip().lower()
        if not href:
            continue
        if any(token in href.lower() for token in ("pdf", "pdfft", "download")) or "pdf" in text:
            urls.append(href)
    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        absolute = urljoin(str(target.get("url", "")), url)
        if absolute not in seen:
            seen.add(absolute)
            deduped.append(absolute)
    return deduped


def sciencedirect_edge_fallback(
    plan: DownloadPlan,
    target_path: Path,
    *,
    session: EdgeDownloadSession,
    move_to_target: Callable[[Path, Path], None],
    validate_pdf: Callable[[Path], bool],
    timeout_sec: int,
) -> Path | None:
    target = wait_for_sciencedirect_target(plan, timeout_sec=timeout_sec)
    if not target:
        return None

    state = sciencedirect_page_state(target)
    if state["hasPageNotFound"]:
        print(f"SCIENCEDIRECT_PAGE_NOT_FOUND label={plan.label}", file=sys.stderr)
        return None

    pii = extract_sciencedirect_pii(str(target.get("url", ""))) or extract_sciencedirect_pii(str(plan.article_url or ""))
    if state["hasAccessLink"] and not state["hasInstitutionAccess"]:
        clicked = cdp_click_first_matching_text(target, ["Access through Zhejiang University"])
        if not clicked and pii:
            session.open_url(f"https://www.sciencedirect.com/science/article/abs/pii/{pii}?via=ihub")
        if not wait_for_sciencedirect_access(plan, timeout_sec=timeout_sec):
            print(f"SCIENCEDIRECT_ACCESS_NOT_ESTABLISHED label={plan.label}", file=sys.stderr)
            return None
        target = wait_for_sciencedirect_target(plan, timeout_sec=timeout_sec) or target
        state = sciencedirect_page_state(target)

    for url in _sciencedirect_candidate_urls(target, plan, pii):
        session.open_url(url)
        downloaded = session.wait_for_pdf()
        if downloaded is None:
            continue
        move_to_target(downloaded, target_path)
        if validate_pdf(target_path):
            return target_path
        if target_path.exists():
            target_path.unlink()

    for text in ["Download PDF", "View PDF", "PDF", "Download full issue", "View full text"]:
        target = wait_for_sciencedirect_target(plan, timeout_sec=timeout_sec) or target
        session.arm_download_watch()
        if not cdp_click_first_matching_text(target, [text]):
            continue
        downloaded = session.wait_for_pdf()
        if downloaded is None:
            continue
        move_to_target(downloaded, target_path)
        if validate_pdf(target_path):
            return target_path
        if target_path.exists():
            target_path.unlink()

    return None


def wait_for_sciencedirect_target(plan: DownloadPlan, *, timeout_sec: int) -> dict | None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        target = find_sciencedirect_target(plan)
        if target:
            return target
        time.sleep(1)
    return None


def wait_for_sciencedirect_access(plan: DownloadPlan, *, timeout_sec: int) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        target = find_sciencedirect_target(plan)
        if target:
            state = sciencedirect_page_state(target)
            url = str(target.get("url", ""))
            if state["hasInstitutionAccess"] or "?via=ihub" in url:
                return True
        time.sleep(1)
    return False


def _sciencedirect_candidate_urls(target: dict, plan: DownloadPlan, pii: str | None) -> list[str]:
    urls: list[str] = []
    urls.extend(cdp_collect_pdf_urls(target))
    current_url = str(target.get("url", ""))
    if current_url:
        base = current_url.split("?", 1)[0].rstrip("/")
        if "/science/article/abs/pii/" in base:
            article_base = base.replace("/science/article/abs/pii/", "/science/article/pii/")
            urls.append(f"{article_base}/pdfft?isDTMRedir=true&download=true")
            urls.append(f"{article_base}/pdf")
    if pii:
        urls.append(f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isDTMRedir=true&download=true")
        urls.append(f"https://www.sciencedirect.com/science/article/pii/{pii}/pdf")
        urls.append(f"https://www.sciencedirect.com/science/article/abs/pii/{pii}?via=ihub")

    deduped: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped
