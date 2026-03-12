#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
eval "$(python3 "$SCRIPT_DIR/core/config.py" export-shell)"
EDGE_BIN="$ZJU_EDGE_EDGE_BIN"
PROFILE_DIR="$ZJU_EDGE_PROFILE_DIR"

usage() {
  cat <<'EOF'
Usage:
  login_acs.sh <doi_or_url>

Examples:
  login_acs.sh 10.1021/acs.est.6c01242
  login_acs.sh https://doi.org/10.1021/acs.est.6c01242
EOF
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

normalize_doi() {
  python3 - "$1" <<'PY'
import re
import sys
from urllib.parse import urlparse

raw = sys.argv[1].strip()
doi = raw
if raw.startswith("http://") or raw.startswith("https://"):
    parsed = urlparse(raw)
    path = parsed.path.strip("/")
    if parsed.netloc.endswith("doi.org"):
        doi = path
    elif parsed.netloc.endswith("pubs.acs.org") and path.startswith("doi/"):
        doi = path[len("doi/") :]

if not re.match(r"^10\.\d{4,9}/.+$", doi):
    raise SystemExit("invalid DOI or ACS URL")

print(doi)
PY
}

DOI="$(normalize_doi "$1")"
"$SCRIPT_DIR/launch_edge.sh"

SSO_URL="$(python3 - "$DOI" <<'PY'
import sys
from urllib.parse import quote

doi = sys.argv[1]
redirect = "/doi/" + doi
url = (
    "https://pubs.acs.org/action/ssostart"
    "?idp=https%3A%2F%2Fidp.zju.edu.cn%2Fidp%2Fshibboleth"
    f"&redirectUri={quote(redirect, safe='')}"
    "&federationId=urn%3Amace%3Ashibboleth%3Acarsifed"
)
print(url)
PY
)"

"$EDGE_BIN" --user-data-dir="$PROFILE_DIR" --profile-directory=Default "$SSO_URL" >/dev/null 2>&1 &
osascript -e 'tell application "Microsoft Edge" to activate' >/dev/null 2>&1 || true
echo "ACS_ZJU_LOGIN_OPENED doi=$DOI"
echo "URL=$SSO_URL"
