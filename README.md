# zju-edge-paper-download

OpenClaw-oriented academic paper download skill for `Zhejiang University WebVPN access + configurable output directory + publisher-specific PDF handling`.

[中文说明 / README.zh-CN.md](./README.zh-CN.md)

## What It Solves

- Packages the workflow as an OpenClaw-consumable skill repository instead of a Codex-only local skill.
- Reuses the saved ZJU login state across runs.
- Uses the WebVPN-backed institutional route; normal use does not require opening `aTrust`.
- Treats `Zhejiang University` as the default institution when publisher flows ask for institutional access.
- Preserves the verified ACS fast path.
- Adds adapter-driven downloads for Nature and exploratory flows for Science and ScienceDirect.
- Keeps the live download implementation isolated from the user's main browser profile.

## OpenClaw Positioning

This repository is published as an OpenClaw-ready skill:

- `SKILL.md` is written for OpenClaw skill discovery and invocation.
- The repository can be installed into an OpenClaw skill collection as-is.
- The bundled scripts still execute the proven dedicated-browser workflow used during live verification.

The skill surface is OpenClaw-first, while the runtime implementation remains the dedicated `Edge + persistent profile + configurable download directory` stack.

## Configuration

Copy `.env.example` to `.env` and adjust the values for your machine:

```bash
cp .env.example .env
```

Supported variables:

- `ZJU_EDGE_EDGE_BIN`
  Default: `/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge`
- `ZJU_EDGE_PROFILE_DIR`
  Default: `./.local/edge-profile`
- `ZJU_EDGE_DOWNLOAD_DIR`
  Default: `./output/final-pdfs`
- `ZJU_EDGE_REMOTE_DEBUG_PORT`
  Default: `62777`

## Files

- `SKILL.md`
- `.env.example`
- `scripts/launch_edge.sh`
- `scripts/login_acs.sh`
- `scripts/download.py`
- `scripts/download_dois.py`
- `scripts/core/`
- `scripts/adapters/`
- `tests/`

## Requirements

- macOS
- OpenClaw environment or any compatible skill runner that can call local shell and Python scripts
- Microsoft Edge installed at `/Applications/Microsoft Edge.app`
- Existing ZJU WebVPN institutional access flow that works in Edge
- Python 3

## Access Model

- This project is intended to run through Zhejiang University WebVPN-backed access.
- Normal usage does not require opening `aTrust`.
- On a fresh profile or after session expiry, the first download may still require one manual WebVPN refresh, publisher login handoff, or CAPTCHA / human verification inside Edge.

## Usage

### 1. Install into your OpenClaw skill collection

Clone or copy this repository into the directory where OpenClaw loads local skills.

### 2. Configure local paths

```bash
cp .env.example .env
```

Edit `.env` if you want a custom Edge profile location, PDF staging directory, or remote debugging port.

### 3. Start the dedicated browser instance

```bash
./scripts/launch_edge.sh
```

Use `--restart` when you want to restart only the dedicated profile instance and reapply profile preferences:

```bash
./scripts/launch_edge.sh --restart
```

### 4. Refresh the ACS institutional session when needed

```bash
./scripts/login_acs.sh "10.1021/acs.est.6c01242"
```

This opens the ACS ZJU SSO entry URL for the DOI. If the session is already valid, it should land on the article page. If not, complete the ZJU login in Edge.

### 5. Download PDFs

Auto-detect publisher from DOI:

```bash
python3 ./scripts/download.py \
  10.1021/acs.est.6c01242 \
  10.1038/ncomms14183
```

Recommended ScienceDirect usage:

```bash
python3 ./scripts/download.py \
  "https://www.sciencedirect.com/science/article/pii/S0013935126005669?via=ihub"
```

ScienceDirect DOI input is also supported. The adapter first tries to resolve the DOI to a concrete ScienceDirect article URL before falling back to `doi.org`, but article URLs are still the most stable input for live runs.

Force a publisher adapter:

```bash
python3 ./scripts/download.py \
  --publisher science \
  10.1126/science.ada1091
```

From a file:

```bash
python3 ./scripts/download.py \
  --from-file ./dois.txt
```

Override the final saved PDF directory for one run:

```bash
python3 ./scripts/download.py \
  --out-dir ./papers \
  10.1021/acs.est.6c01242
```

Example `dois.txt`:

```text
10.1021/acs.est.6c01242
10.1038/ncomms14183
10.1126/science.ada1091
https://www.sciencedirect.com/science/article/pii/S1876610217346770
```

Compatibility wrapper:

```bash
python3 ./scripts/download_dois.py \
  10.1021/acs.est.6c01242
```

## Output

By default, downloaded PDFs are written to the path configured by `ZJU_EDGE_DOWNLOAD_DIR` in `.env`.

If `--out-dir` is provided, files are moved into that final directory after download verification.

Successful downloads are renamed to stable file names derived from the DOI or article URL, for example:

- `10.1021_acs.est.6c01242.pdf`
- `10.1038_ncomms14183.pdf`
- `www.sciencedirect.com_science_article_pii_S1876610217346770.pdf`

## Security Notes

- No password is stored in this skill.
- Cookies and institutional session state live only inside the dedicated Edge profile.
- If credential storage is later needed, integrate a password manager such as `gopass` instead of plaintext files.

## Operational Notes

- ACS remains the verified fast path.
- Nature is a first-class adapter with article-page fallback and modern `_reference.pdf` support.
- Science remains exploratory but has repeated live-download success in the dedicated Edge profile.
- ScienceDirect is still the least stable publisher. The fixed workflow is:
  - keep the dedicated Edge profile warm
  - default institution choice to Zhejiang University
  - prefer direct ScienceDirect article URLs when available
  - allow the challenge/download page to complete in the existing Edge session
- The first download on a new profile may pause for login confirmation or publisher-side human verification before retries succeed.
- The dedicated profile is configured to:
  - always download PDFs instead of previewing them
  - write downloads into the configured output folder
- If a download does not start, the downloader opens the login or article page defined by the adapter and retries when applicable.
- If you expose this repository through OpenClaw, keep the skill description aligned with the bundled scripts rather than claiming a different browser stack.

## Publishing Notes

Do not commit `.env`, the actual browser profile, or downloaded PDFs.
