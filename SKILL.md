---
name: zju-edge-paper-download
description: Use when downloading publisher PDFs through Zhejiang University institutional access in a dedicated persistent Microsoft Edge profile, especially when the user wants ACS fast-path downloads or wants stable Nature, Science, or ScienceDirect downloads with the same saved login state and fixed output directory.
---

# ZJU Edge Paper Download

Use this skill for the `ZJU + persistent Edge + publisher adapter` workflow.

## When To Use

- User wants to reuse the saved ZJU institutional login state instead of logging in every run.
- User wants publisher PDFs downloaded into a fixed folder.
- User wants a dedicated Edge profile, not the main browser profile.
- User mentions `ZJU`, `浙江大学`, `ACS`, `Nature`, `Science`, `ScienceDirect`, `机构登录`, `持久登录态`, or batch DOI download.

## Scope

- Verified fast path for ACS DOI/article pages.
- First-class adapter for Nature DOI/article pages, including `_reference.pdf` fallback used by newer pages.
- Exploratory adapters for Science and ScienceDirect.
- Uses a dedicated Edge profile at:
  `/Users/b/Downloads/browser-use-local/persistent-edge/zju-edge-profile`
- Saves PDFs to:
  `/Users/b/Downloads/browser-use-local/output/downloads/zju-edge-persistent/final-pdfs`
- Defaults institution choice to `Zhejiang University` when publisher flows require institution selection.

## Quick Start

Launch or reuse the dedicated Edge session:

```bash
/Users/b/.codex/skills/zju-edge-paper-download/scripts/launch_edge.sh
```

If the ACS/ZJU session has expired, open a fresh institutional login entry point:

```bash
/Users/b/.codex/skills/zju-edge-paper-download/scripts/login_acs.sh "10.1021/acs.est.6c01242"
```

Download one or more papers with publisher auto-detection:

```bash
python3 /Users/b/.codex/skills/zju-edge-paper-download/scripts/download.py \
  10.1021/acs.est.6c01242 \
  10.1038/ncomms14183
```

Force a specific publisher adapter when needed:

```bash
python3 /Users/b/.codex/skills/zju-edge-paper-download/scripts/download.py \
  --publisher science \
  10.1126/science.ada1091
```

Batch from file:

```bash
python3 /Users/b/.codex/skills/zju-edge-paper-download/scripts/download.py \
  --from-file /path/to/dois.txt
```

The old ACS entrypoint still works and now forwards into the new CLI:

```bash
python3 /Users/b/.codex/skills/zju-edge-paper-download/scripts/download_dois.py \
  10.1021/acs.est.6c01242
```

## Behavior

1. Reuse a dedicated Edge instance on port `62777`.
2. Keep login cookies in the dedicated profile.
3. Force PDFs to download instead of opening in-browser.
4. Route each DOI/URL through a publisher adapter.
5. Keep ACS on the direct `Open PDF` fast path with ZJU SSO retry.
6. For Nature, Science, and ScienceDirect, try adapter-specific PDF URL heuristics first and then fall back to opening the article page.
7. For ScienceDirect DOI inputs, first try to resolve the DOI into a concrete article URL before falling back to `doi.org`.

## Limits

- This skill does not store campus credentials.
- Science and ScienceDirect support are still less stable than ACS; do not present them as equivalent to the ACS fast path.
- If the institutional session fully expires, the user may still need to complete the ZJU login in Edge once before retrying.
