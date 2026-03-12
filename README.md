# zju-edge-paper-download

Persistent `Microsoft Edge + Zhejiang University institutional access + publisher PDF download` workflow.

## What It Solves

- Keeps a dedicated Edge profile for institutional access.
- Reuses the saved ZJU login state across runs.
- Treats `Zhejiang University` as the default institution when publisher flows ask for institutional access.
- Preserves the verified ACS fast path.
- Adds adapter-driven downloads for Nature and exploratory flows for Science and ScienceDirect.
- Favors stable publisher-specific PDF paths, including modern Nature `_reference.pdf` links and ScienceDirect article-URL-first handling.
- Avoids contaminating the user's main Edge profile.

## Verified Paths

- Skill root:
  `/Users/b/.codex/skills/zju-edge-paper-download`
- Persistent Edge profile:
  `/Users/b/Downloads/browser-use-local/persistent-edge/zju-edge-profile`
- Download output:
  `/Users/b/Downloads/browser-use-local/output/downloads/zju-edge-persistent/final-pdfs`
- Remote debugging port:
  `62777`

## Files

- `SKILL.md`
- `scripts/launch_edge.sh`
- `scripts/login_acs.sh`
- `scripts/download.py`
- `scripts/download_dois.py`
- `scripts/core/`
- `scripts/adapters/`
- `tests/`

## Requirements

- macOS
- Microsoft Edge installed at `/Applications/Microsoft Edge.app`
- Existing ZJU institutional access flow that works in Edge
- Python 3

## Usage

### 1. Start the dedicated Edge instance

```bash
/Users/b/.codex/skills/zju-edge-paper-download/scripts/launch_edge.sh
```

Use `--restart` when you want to restart only the dedicated profile instance and reapply profile preferences:

```bash
/Users/b/.codex/skills/zju-edge-paper-download/scripts/launch_edge.sh --restart
```

### 2. Refresh the ACS institutional session when needed

```bash
/Users/b/.codex/skills/zju-edge-paper-download/scripts/login_acs.sh "10.1021/acs.est.6c01242"
```

This opens the ACS ZJU SSO entry URL for the DOI. If the session is already valid, it should land on the article page. If not, complete the ZJU login in Edge.

### 3. Download PDFs

Auto-detect publisher from DOI:

```bash
python3 /Users/b/.codex/skills/zju-edge-paper-download/scripts/download.py \
  10.1021/acs.est.6c01242 \
  10.1038/ncomms14183
```

Recommended ScienceDirect usage:

```bash
python3 /Users/b/.codex/skills/zju-edge-paper-download/scripts/download.py \
  "https://www.sciencedirect.com/science/article/pii/S0013935126005669?via=ihub"
```

ScienceDirect DOI input is also supported. The adapter now tries to resolve the DOI to a concrete ScienceDirect article URL before falling back to `doi.org`, but article URLs are still the most stable input for live runs.

Force a publisher adapter:

```bash
python3 /Users/b/.codex/skills/zju-edge-paper-download/scripts/download.py \
  --publisher science \
  10.1126/science.ada1091
```

From a file:

```bash
python3 /Users/b/.codex/skills/zju-edge-paper-download/scripts/download.py \
  --from-file ./dois.txt
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
python3 /Users/b/.codex/skills/zju-edge-paper-download/scripts/download_dois.py \
  10.1021/acs.est.6c01242
```

## Output

Downloaded PDFs are written to:

`/Users/b/Downloads/browser-use-local/output/downloads/zju-edge-persistent/final-pdfs`

The script renames each successful download to a stable file name derived from the DOI or article URL, for example:

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
- The dedicated profile is configured to:
  - always download PDFs instead of previewing them
  - write downloads into the fixed output folder
- If a download does not start, the downloader opens the login or article page defined by the adapter and retries when applicable.

## Publishing Notes

If this is published to GitHub, do not commit the actual browser profile or downloaded PDFs. Publish only the skill files and document the local paths as machine-specific defaults that can be overridden later.
