---
name: zju-edge-paper-download
description: Use when OpenClaw needs to download publisher PDFs through Zhejiang University institutional access with a fixed output directory, especially for ACS fast-path downloads or Nature, Science, and ScienceDirect article flows that reuse an existing logged-in browser session.
---

# ZJU OpenClaw Paper Download

Use this skill when OpenClaw should drive a `Zhejiang University institutional access + fixed download directory + publisher adapter` paper-download workflow.

## When To Use

- OpenClaw already has a logged-in institutional browser context and should reuse it instead of redoing login each run.
- The task is to download ACS, Nature, Science, or ScienceDirect PDFs into a fixed local directory.
- The user wants Zhejiang University to be the default institution when publisher login pickers appear.
- The user mentions `OpenClaw`, `ZJU`, `浙江大学`, `ACS`, `Nature`, `Science`, `ScienceDirect`, `机构登录`, `批量下载`, or a fixed PDF output path.

## Scope

- Verified fast path for ACS DOI/article pages.
- First-class adapter for Nature DOI/article pages, including `_reference.pdf` fallback used by newer pages.
- Exploratory adapters for Science and ScienceDirect.
- Bundled live-download implementation currently uses a dedicated Edge profile at:
  `/Users/b/Downloads/browser-use-local/persistent-edge/zju-edge-profile`
- Saves PDFs to:
  `/Users/b/Downloads/browser-use-local/output/downloads/zju-edge-persistent/final-pdfs`
- Defaults institution choice to `Zhejiang University` when publisher flows require institution selection.

## Quick Start

From OpenClaw, first ensure the logged-in browser session is valid. Then invoke the bundled scripts from the installed skill root.

Launch or reuse the dedicated browser session:

```bash
./scripts/launch_edge.sh
```

If the ACS/ZJU session has expired, open a fresh institutional login entry point:

```bash
./scripts/login_acs.sh "10.1021/acs.est.6c01242"
```

Download one or more papers with publisher auto-detection:

```bash
python3 ./scripts/download.py \
  10.1021/acs.est.6c01242 \
  10.1038/ncomms14183
```

Force a specific publisher adapter when needed:

```bash
python3 ./scripts/download.py \
  --publisher science \
  10.1126/science.ada1091
```

Batch from file:

```bash
python3 ./scripts/download.py \
  --from-file ./dois.txt
```

The old ACS entrypoint still works and now forwards into the new CLI:

```bash
python3 ./scripts/download_dois.py \
  10.1021/acs.est.6c01242
```

## Behavior

1. Reuse a dedicated logged-in browser session on port `62777`.
2. Keep institutional cookies inside the dedicated browser profile.
3. Force PDFs to download instead of opening in-browser.
4. Route each DOI or article URL through a publisher adapter.
5. Keep ACS on the direct `Open PDF` fast path with ZJU SSO retry.
6. For Nature, Science, and ScienceDirect, try adapter-specific PDF URL heuristics first and then fall back to opening the article page.
7. For ScienceDirect DOI inputs, first try to resolve the DOI into a concrete article URL before falling back to `doi.org`.
8. When publisher institution selection appears, prefer `Zhejiang University`.

## Limits

- This skill does not store campus credentials.
- Science and ScienceDirect support are still less stable than ACS; do not present them as equivalent to the ACS fast path.
- If the institutional session fully expires, OpenClaw may still need one manual login refresh before retries succeed.
- This repository is OpenClaw-oriented at the skill/documentation layer, but the bundled downloader implementation still uses the dedicated Edge workflow described above.
