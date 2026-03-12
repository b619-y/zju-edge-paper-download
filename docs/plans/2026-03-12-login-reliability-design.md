# ZJU Edge Login Reliability Design

## Goal

Reduce false `DOWNLOAD_FAILED` results when the dedicated ACS/ZJU Edge session has expired and the downloader needs a manual institutional re-login.

## Root Cause

The existing fallback opens the ACS ZJU SSO page but does not reliably bring Edge to the foreground, and in non-interactive runs it waits only 10 seconds before retrying the PDF URL. That is often shorter than the real manual login time, so the retry happens before the session is restored.

## Design

1. Keep the current download flow unchanged for already-authenticated sessions.
2. When login fallback is triggered:
   - open the ACS ZJU SSO URL in the dedicated profile
   - force Microsoft Edge to the foreground
   - wait for a concrete completion signal instead of sleeping blindly
3. Reuse the existing remote debugging port `62777` from the dedicated Edge instance:
   - poll `http://127.0.0.1:62777/json/list`
   - treat login as complete only when a tab URL returns to the target DOI under `pubs.acs.org/doi/...` and is no longer on the IdP or `action/ssostart`
4. Expose a configurable `--login-wait-sec` timeout so long institutional redirects do not fail prematurely.

## Verification

- Syntax-check the Python and shell scripts.
- Run a focused regression snippet against the DOI URL classifier to confirm that:
  - IdP URLs are rejected
  - ACS SSO starter URLs are rejected
  - ACS DOI/article/PDF URLs for the target DOI are accepted
