# Multi-Publisher Download Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Preserve the existing ACS fast path while refactoring the skill into a shared downloader core with publisher adapters for ACS, Nature, Science, and ScienceDirect.

**Architecture:** Keep `download_dois.py` as the compatibility entrypoint, but move logic into `scripts/core` and `scripts/adapters`. ACS remains a direct-PDF adapter with ZJU SSO retry; the other publishers use bounded direct-link heuristics plus exploratory article-page fallback so the skill can report concrete failure modes instead of a generic timeout.

**Tech Stack:** Python 3, pytest, Microsoft Edge persistent profile, existing shell launch/login scripts.

---

### Task 1: Create the failing tests

**Files:**
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/tests/test_inputs.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/tests/test_adapters.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/tests/test_runner.py`

**Dependencies:** None
**Execution:** Sequential, establishes the target behavior before refactor.

**Step 1: Write publisher-detection tests**

Cover DOI and URL inputs for `acs`, `nature`, `science`, and `sciencedirect`.

**Step 2: Write adapter-plan tests**

Assert the generated article/PDF/login URLs and support-level metadata for each adapter.

**Step 3: Write retry-orchestration tests**

Use a fake browser/download layer to prove the runner retries login or fallback URLs in the expected order.

**Step 4: Run tests to verify RED**

Run: `pytest /Users/b/.codex/skills/zju-edge-paper-download/tests -q`

Expected: import or symbol failures because the refactor has not been implemented yet.

### Task 2: Implement the shared core

**Files:**
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/__init__.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/core/__init__.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/core/models.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/core/inputs.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/core/downloads.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/core/browser.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/core/runner.py`

**Dependencies:** Task 1
**Execution:** Sequential, shared contract used by all adapters.

**Step 1: Define dataclasses for normalized input and download plans**

Keep the schema small and explicit.

**Step 2: Implement input normalization and publisher detection**

Support DOI, `doi.org`, and publisher article URLs.

**Step 3: Move PDF validation, file watching, and move logic into the shared layer**

This preserves the existing Edge download-folder behavior.

**Step 4: Implement runner orchestration**

Support candidate URL attempts, optional login retry, article-page fallback, and structured result reporting.

### Task 3: Add publisher adapters

**Files:**
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/adapters/__init__.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/adapters/base.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/adapters/acs.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/adapters/nature.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/adapters/science.py`
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/adapters/sciencedirect.py`

**Dependencies:** Task 2
**Execution:** Nature/Science/ScienceDirect adapter logic can be developed in parallel after the base API exists.

**Step 1: Port ACS behavior into `acs.py`**

Keep direct PDF + ZJU SSO retry intact.

**Step 2: Implement Nature URL strategy**

Prefer article URL plus predictable `.pdf` candidate; keep article fallback for manual/auth-assisted retries.

**Step 3: Implement Science URL strategy**

Prefer `science.org/doi/pdf/<doi>` candidates; keep article fallback.

**Step 4: Implement ScienceDirect exploratory strategy**

Accept DOI and article/PII URLs, preserve article-page fallback, and report that support is exploratory.

### Task 4: Rebuild the CLI and compatibility wrapper

**Files:**
- Create: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/download.py`
- Modify: `/Users/b/.codex/skills/zju-edge-paper-download/scripts/download_dois.py`

**Dependencies:** Tasks 2-3
**Execution:** Sequential, because the wrapper depends on the new core.

**Step 1: Build the new CLI**

Add `--publisher auto|acs|nature|science|sciencedirect` and preserve the existing flags.

**Step 2: Keep `download_dois.py` as a wrapper**

Delegate to the new CLI so existing commands still work.

**Step 3: Run tests to verify GREEN**

Run: `pytest /Users/b/.codex/skills/zju-edge-paper-download/tests -q`

Expected: all unit tests pass.

### Task 5: Update docs and support claims

**Files:**
- Modify: `/Users/b/.codex/skills/zju-edge-paper-download/SKILL.md`
- Modify: `/Users/b/.codex/skills/zju-edge-paper-download/README.md`

**Dependencies:** Task 4
**Execution:** Sequential, must reflect the implemented behavior.

**Step 1: Update scope wording**

State that ACS is the verified fast path, Nature has first-class adapter support, and Science/ScienceDirect are exploratory adapters with explicit caveats.

**Step 2: Document new CLI examples**

Include auto-detect and explicit publisher usage.

### Task 6: Run live verification

**Files:**
- No code changes

**Dependencies:** Task 5
**Execution:** Sequential per publisher; avoid concurrent downloads in the same Edge profile.

**Step 1: Verify ACS regression**

Run one known ACS DOI through the wrapper.

**Step 2: Verify Nature adapter**

Run one known Nature DOI and confirm either a saved PDF or a classified exploratory failure.

**Step 3: Explore Science and ScienceDirect**

Run one known DOI each and capture whether the adapter downloads successfully or fails with a specific reason.

**Step 4: Record results**

Update README/SKILL only if observed behavior differs from the documented support level.
