---
name: zju-edge-paper-download
description: Open Science/AAAS, Nature, PNAS, ACS, ScienceDirect, and APS paper pages and download article PDFs or supplementary files in the user's normal Microsoft Edge profile. Use WebVPN for Science/Nature/PNAS/ACS/ScienceDirect requests through ZJU WebVPN; use direct real-Edge access for APS because journals.aps.org is blocked by Cloudflare through WebVPN. Trigger on Science paper, Nature article, PNAS DOI, ACS DOI/article, ScienceDirect/Elsevier article or PII, APS/Physical Review DOI, science.org/nature.com/pnas.org/pubs.acs.org/sciencedirect.com/journals.aps.org URL, article PDF, supplement, supporting information, supplementary material, MMC, or related file.
---

# ZJU Edge Paper Download

## Overview

Use the user's real Microsoft Edge session, not the dedicated ZJU persistent Edge profile. Drive WebVPN directly in the existing browser, prefer stable window/tab identification over front-window assumptions, and reuse publisher WebVPN proxy paths once `www.science.org`, `www.nature.com`, `www.pnas.org`, `pubs.acs.org`, or `www.sciencedirect.com` has been opened through WebVPN. Treat APS as an exception: use direct `journals.aps.org` access in real Edge, not WebVPN.

## Operating Rules

- Use AppleScript against `Microsoft Edge` for the normal user profile.
- Do not invoke legacy dedicated-profile downloader scripts such as `launch_edge.sh` unless the user explicitly asks for that workflow.
- Do not depend on `front window` or `active tab` until you have confirmed the target. Edge may have unrelated pages in front.
- Enumerate Edge windows/tabs first, then bind operations to a specific window id and tab index.
- For WebVPN's search box, keep the left protocol selector on `https` and put only the host/path in the input, for example `www.science.org/doi/10.1126/science.1096205`, `www.nature.com/articles/ncomms14183`, `www.pnas.org/doi/10.1073/pnas.1912154116`, `pubs.acs.org/doi/10.1021/acs.est.6c01242`, or `www.sciencedirect.com/science/article/pii/S0092867420302841`.
- Click `.portal-search__button`; do not assume pressing Enter submits the WebVPN search.
- Prefer simple JavaScript string checks such as `href.includes(...)` inside AppleScript. Avoid complex regex literals that create quoting failures.
- Do not route APS (`journals.aps.org`) through WebVPN. WebVPN currently triggers a Cloudflare page that says the browser does not support the required security verification. Direct real Edge access works.

## Locate The Target Tab

List all Edge tabs:

```bash
osascript <<'APPLESCRIPT'
tell application "Microsoft Edge"
  set out to ""
  repeat with w from 1 to count of windows
    repeat with i from 1 to count of tabs of window w
      set out to out & (id of window w) & tab & i & tab & (title of tab i of window w) & tab & (URL of tab i of window w) & linefeed
    end repeat
  end repeat
  return out
end tell
APPLESCRIPT
```

Pick a WebVPN window id and target tab. Activate it by id:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set active tab index of targetWindow to 3
  set index of targetWindow to 1
  activate
end tell
```

Replace `<edge-window-id>` and `3` with the values discovered in the current session.

## First Publisher Search Through WebVPN

Open `https://webvpn.zju.edu.cn/` in real Edge if no WebVPN tab exists:

```bash
open -a "Microsoft Edge" "https://webvpn.zju.edu.cn/"
```

If WebVPN is logged in and shows the resource page, fill the search input with a publisher host/path and click the go button:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set pagePath to "www.science.org/doi/10.1126/science.1096205"
  set js to "(() => { const input = document.querySelector('input.portal-search__input') || Array.from(document.querySelectorAll('input')).find(el => (el.placeholder || '').includes('输入网址')); const btn = document.querySelector('.portal-search__button'); if (!input || !btn) return 'MISSING:' + !!input + ':' + !!btn; const value = '" & pagePath & "'; input.focus(); const desc = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(input), 'value'); desc.set.call(input, value); input.dispatchEvent(new Event('input', {bubbles:true})); input.dispatchEvent(new Event('change', {bubbles:true})); btn.click(); return 'CLICKED:' + input.value; })()"
  execute active tab of targetWindow javascript js
end tell
```

If the page asks for ZJU unified authentication, stop and ask the user to complete login in the real Edge window.

## Reuse Publisher Proxy URLs

After a publisher domain has been opened once through WebVPN, later pages on the same domain usually do not need another WebVPN search. Use the current proxied URL as a template.

For Science/AAAS:

```text
https://webvpn.zju.edu.cn/https/<science-proxy-id>/doi/10.1126/science.1096205
```

For a new Science DOI, replace only the DOI path segment after `/doi/`:

```text
https://webvpn.zju.edu.cn/https/<science-proxy-id>/doi/10.1126/science.aab1680
```

For direct PDF download, use:

```text
https://webvpn.zju.edu.cn/https/<science-proxy-id>/doi/pdf/10.1126/science.aab1680?download=true
```

For Nature:

```text
https://webvpn.zju.edu.cn/https/<nature-proxy-id>/articles/ncomms14183
https://webvpn.zju.edu.cn/https/<nature-proxy-id>/articles/ncomms14183.pdf
```

For PNAS:

```text
https://webvpn.zju.edu.cn/https/<pnas-proxy-id>/doi/10.1073/pnas.1912154116
https://webvpn.zju.edu.cn/https/<pnas-proxy-id>/doi/pdf/10.1073/pnas.1912154116?download=true
```

For ACS:

```text
https://webvpn.zju.edu.cn/https/<acs-proxy-id>/doi/10.1021/acs.est.6c01242
https://webvpn.zju.edu.cn/https/<acs-proxy-id>/doi/pdf/10.1021/acs.est.6c01242?ref=article_openPDF
```

For ScienceDirect:

```text
https://webvpn.zju.edu.cn/https/<sciencedirect-proxy-id>/science/article/pii/S0092867420302841
```

Do not assume a guessed PII exists. If a ScienceDirect PII page returns `Page not found`, the WebVPN path may still be correct; the PII itself is likely wrong.

Open constructed URLs with:

```bash
open -a "Microsoft Edge" "<constructed-webvpn-url>"
```

## Download Science Or PNAS PDF

Science and PNAS both expose the main article PDF as `/doi/pdf/<DOI>?download=true`. PNAS may also show `/doi/epdf/<DOI>` as a viewer/reader link; use `/doi/pdf/... ?download=true` for download.

On a Science or PNAS article page, inspect PDF/download links before clicking:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set js to "JSON.stringify(Array.from(document.querySelectorAll('a,button,[role=button]')).map((el,i)=>({i,tag:el.tagName,text:(el.innerText||el.textContent||'').trim().replace(/\\s+/g,' ').slice(0,160),aria:el.getAttribute('aria-label')||'',title:el.getAttribute('title')||'',href:el.href||'',cls:typeof el.className === 'string' ? el.className : ''})).filter(x=>/pdf|download|下载|full text/i.test([x.text,x.aria,x.title,x.href,x.cls].join(' '))).slice(0,100))"
  execute active tab of targetWindow javascript js
end tell
```

Click the main PDF download link:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set doi to "10.1073/pnas.1912154116"
  set js to "(() => { const links = Array.from(document.querySelectorAll('a')); const target = links.find(a => a.href.includes('/doi/pdf/" & doi & "') && a.href.includes('download=true')) || links.find(a => (a.innerText || '').trim() === 'Download PDF' && a.href.includes('/doi/pdf/')) || links.find(a => (a.getAttribute('aria-label') || '').toLowerCase() === 'pdf'); if (!target) return 'NO_DOWNLOAD_LINK'; target.scrollIntoView({block:'center'}); target.click(); return 'CLICKED:' + ((target.innerText || target.getAttribute('aria-label') || target.href).trim()); })()"
  execute active tab of targetWindow javascript js
end tell
```

Verify the download in `$HOME/Downloads`:

```bash
find "$HOME/Downloads" -maxdepth 2 \( -name '*.pdf' -o -name '*.crdownload' -o -name '*.download' \) -mmin -5 -print | sort
```

## Download ACS PDF

ACS pages use DOI paths like:

```text
https://pubs.acs.org/doi/10.1021/acs.est.6c01242
```

Through WebVPN:

```text
https://webvpn.zju.edu.cn/https/<acs-proxy-id>/doi/10.1021/acs.est.6c01242
```

The main article PDF link is the `Open PDF` button:

```text
/doi/pdf/10.1021/acs.est.6c01242?ref=article_openPDF
```

Important: do not click Supporting Information PDFs unless the user asks for supplements. ACS pages often contain many `/doi/suppl/.../suppl_file/...pdf` links such as `es6c01242_si_001.pdf`; those are not the main article.

Inspect PDF-related links:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set js to "JSON.stringify(Array.from(document.querySelectorAll('a,button,[role=button]')).map((el,i)=>({i,tag:el.tagName,text:(el.innerText||el.textContent||'').trim().replace(/\\s+/g,' ').slice(0,200),aria:el.getAttribute('aria-label')||'',title:el.getAttribute('title')||'',href:el.href||'',cls:typeof el.className === 'string' ? el.className : ''})).filter(x=>/pdf|download|下载|suppl|open pdf/i.test([x.text,x.aria,x.title,x.href,x.cls].join(' '))).slice(0,140))"
  execute active tab of targetWindow javascript js
end tell
```

Click only the main article `Open PDF` link:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set doi to "10.1021/acs.est.6c01242"
  set js to "(() => { const links = Array.from(document.querySelectorAll('a')); const target = links.find(a => a.href.includes('/doi/pdf/" & doi & "') && a.href.includes('ref=article_openPDF')) || links.find(a => (a.innerText || '').trim() === 'Open PDF' && a.href.includes('/doi/pdf/" & doi & "')); if (!target) return 'NO_ACS_OPEN_PDF_LINK'; target.scrollIntoView({block:'center'}); target.click(); return 'CLICKED:' + target.href; })()"
  execute active tab of targetWindow javascript js
end tell
```

Verify the download in `$HOME/Downloads`; ACS often saves with a title-based filename:

```bash
find "$HOME/Downloads" -maxdepth 2 \( -name '*.pdf' -o -name '*.crdownload' -o -name '*.download' \) -mmin -5 -print | sort
```

## Download Nature PDF

Nature article pages use article ids under `/articles/`:

```text
https://www.nature.com/articles/ncomms14183
https://www.nature.com/articles/s41467-024-54358-z
```

Through WebVPN:

```text
https://webvpn.zju.edu.cn/https/<nature-proxy-id>/articles/ncomms14183
```

The main PDF is usually the same article path with `.pdf` appended:

```text
/articles/ncomms14183.pdf
```

Newer pages may still expose the same destination through a visible `Download PDF` link. Prefer matching the current article id plus `.pdf`; do not rely only on link text if recommendation cards also contain PDF links.

Inspect PDF-related links:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set js to "JSON.stringify(Array.from(document.querySelectorAll('a,button,[role=button]')).map((el,i)=>({i,tag:el.tagName,text:(el.innerText||el.textContent||'').trim().replace(/\\s+/g,' ').slice(0,200),aria:el.getAttribute('aria-label')||'',title:el.getAttribute('title')||'',href:el.href||'',cls:typeof el.className === 'string' ? el.className : ''})).filter(x=>/pdf|download|下载|article/i.test([x.text,x.aria,x.title,x.href,x.cls].join(' '))).slice(0,140))"
  execute active tab of targetWindow javascript js
end tell
```

Click the current article PDF:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set articleId to "ncomms14183"
  set js to "(() => { const links = Array.from(document.querySelectorAll('a')); const target = links.find(a => a.href.includes('/articles/' + '" & articleId & "' + '.pdf')) || links.find(a => (a.innerText || '').trim() === 'Download PDF' && a.href.includes('.pdf')); if (!target) return 'NO_NATURE_PDF_LINK'; target.scrollIntoView({block:'center'}); target.click(); return 'CLICKED:' + target.href; })()"
  execute active tab of targetWindow javascript js
end tell
```

Verify the download in `$HOME/Downloads`; Nature often saves as `<article-id>.pdf`:

```bash
find "$HOME/Downloads" -maxdepth 2 \( -name '*ncomms14183*.pdf' -o -name '*.crdownload' -o -name '*.download' \) -mmin -5 -print | sort
```

## Download Supplementary Files

Prefer extracting the supplementary file `href` from the article page, then opening that href directly with real Edge. For Science, PNAS, and Nature, DOM `click()` can sometimes not produce a saved file, while `open -a "Microsoft Edge" "<supplement-url>"` reliably downloads.

Common patterns:

- Science: `/doi/suppl/<DOI>/suppl_file/<filename>`, for example `yoon.sm.pdf`.
- PNAS: `/doi/suppl/<DOI>/suppl_file/<filename>`, often `pnas.<id>.sapp.pdf`; other supplements can be media files such as `.mp4`.
- ACS: `/doi/suppl/<DOI>/suppl_file/<filename>`, often `<article>_si_001.pdf`. These are Supporting Information files, not the main article.
- Nature: `/esm/art%3A<DOI>/MediaObjects/<...>_ESM.<ext>`, for example `41467_2017_BFncomms14183_MOESM1187_ESM.pdf`.
- ScienceDirect: `/content/image/1-s2.0-<PII>-mmcN.<ext>`, for example `1-s2.0-S0012821X20302363-mmc1.pdf`.

Find candidates on the current page:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set js to "(() => { const keys = ['suppl','supplement','supplementary','supporting','materials','appendix','mediaobjects','mmc','sapp','si_','.pdf','.docx','.xlsx','.zip','.csv','.mp4']; return JSON.stringify(Array.from(document.querySelectorAll('a')).map((a,i)=>({i,text:(a.innerText||a.textContent||'').trim().replace(/\\s+/g,' ').slice(0,220),href:a.href,title:a.getAttribute('title')||'',aria:a.getAttribute('aria-label')||''})).filter(x => keys.some(k => [x.text,x.href,x.title,x.aria].join(' ').toLowerCase().includes(k))).slice(0,160)); })()"
  execute active tab of targetWindow javascript js
end tell
```

Open the selected supplement href directly:

```bash
open -a "Microsoft Edge" "https://webvpn.zju.edu.cn/https/<publisher-proxy-id>/doi/suppl/10.1126/science.aab1680/suppl_file/yoon.sm.pdf"
```

For ScienceDirect, verify that the `mmc` filename contains the current PII. Not every ScienceDirect article has supplementary files; if no `mmc` or supplementary links appear, try another article known to have an Appendix/Supplementary data section instead of assuming the extraction failed.

Verify supplement downloads:

```bash
find "$HOME/Downloads" -maxdepth 2 \( -name '*sm.pdf' -o -name '*sapp*' -o -name '*_si_*' -o -name '*MOESM*' -o -name '*-mmc*' -o -name '*.crdownload' -o -name '*.download' \) -mmin -10 -print | sort
```

## Download APS PDF Or Supplemental Material

APS/Physical Review is an exception to the WebVPN pattern. Do not use WebVPN for `journals.aps.org`; it is intercepted by Cloudflare security verification through WebVPN. Use the user's normal Edge directly:

```bash
open -a "Microsoft Edge" "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.061102"
```

APS article pages use journal slugs such as `prl`, `pra`, `prb`, `prd`, `pre`, and DOI paths:

```text
https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.061102
```

The main article PDF path is:

```text
https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.116.061102
```

Supplemental material, when present, is linked from the abstract page and commonly uses:

```text
https://journals.aps.org/prl/supplemental/10.1103/PhysRevLett.132.076401/SI.pdf
```

Inspect APS PDF/supplement links on the direct page:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set js to "(() => { const keys = ['pdf','supplement','supplemental','supp','ancillary','media','.pdf','.zip']; return JSON.stringify(Array.from(document.querySelectorAll('a')).map((a,i)=>({i,text:(a.innerText||a.textContent||'').trim().replace(/\\s+/g,' ').slice(0,220),href:a.href,title:a.getAttribute('title')||'',aria:a.getAttribute('aria-label')||''})).filter(x => keys.some(k => [x.text,x.href,x.title,x.aria].join(' ').toLowerCase().includes(k))).slice(0,140)); })()"
  execute active tab of targetWindow javascript js
end tell
```

Open APS PDF or supplemental href directly:

```bash
open -a "Microsoft Edge" "https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.116.061102"
open -a "Microsoft Edge" "https://journals.aps.org/prl/supplemental/10.1103/PhysRevLett.132.076401/SI.pdf"
```

Verify APS downloads:

```bash
find "$HOME/Downloads" -maxdepth 2 \( -name 'PhysRev*.pdf' -o -name 'SI.pdf' -o -name '*.crdownload' -o -name '*.download' \) -mmin -10 -print | sort
```

## Download ScienceDirect PDF

ScienceDirect article pages use PII-based URLs:

```text
https://www.sciencedirect.com/science/article/pii/<PII>
```

Through WebVPN, the article becomes:

```text
https://webvpn.zju.edu.cn/https/<sciencedirect-proxy-id>/science/article/pii/<PII>
```

The PDF link is not a stable `/pdf` path. It appears on the article page as a `View PDF` link whose `href` contains:

```text
/science/article/pii/<PII>/pdfft?...
pid=1-s2.0-<PII>-main.pdf
```

Important: do not click the first link whose text is `View PDF`. ScienceDirect pages can contain recommended or related articles with their own `View PDF` links, which can download the wrong paper. Always match the current PII in both the `/pdfft` path and the `pid` filename.

List candidate links for the current PII:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set pii to "S0092867420302841"
  set js to "JSON.stringify(Array.from(document.querySelectorAll('a')).map((a,i)=>({i,text:(a.innerText||a.textContent||'').trim().replace(/\\s+/g,' ').slice(0,160),aria:a.getAttribute('aria-label')||'',href:a.href})).filter(x=>x.href.includes('" & pii & "') || x.text.includes('PDF') || x.aria.includes('PDF')).slice(0,80))"
  execute active tab of targetWindow javascript js
end tell
```

Click only the exact PDF link for the current PII:

```applescript
tell application "Microsoft Edge"
  set targetWindow to first window whose id is <edge-window-id>
  set pii to "S0092867420302841"
  set js to "(() => { const links = Array.from(document.querySelectorAll('a')); const target = links.find(a => a.href.includes('/science/article/pii/" & pii & "/pdfft?') && a.href.includes('pid=1-s2.0-" & pii & "-main.pdf')); if (!target) return 'NO_TARGET_PDF_LINK'; target.scrollIntoView({block:'center'}); target.click(); return 'CLICKED:' + target.href; })()"
  execute active tab of targetWindow javascript js
end tell
```

Verify the target filename in `$HOME/Downloads`, for example:

```bash
find "$HOME/Downloads" -maxdepth 2 \( -name '1-s2.0-S0092867420302841-main.pdf' -o -name '*.crdownload' -o -name '*.download' \) -mmin -5 -print | sort
```
