#!/usr/bin/env python3
"""Build an ATS-friendly CV from a JSON data file.

    python3 scripts/build_cv.py --data cv.json --out Name_CV.pdf
    python3 scripts/build_cv.py --data cv.json --out Name_CV.pdf --preview  # + page PNGs
    python3 scripts/build_cv.py --data cv.json --out Name_CV.html   # no PDF engine needed
    python3 scripts/build_cv.py --data cv.json --out Name_CV.txt    # plain text for web forms
    python3 scripts/build_cv.py --data cv.json --check-only         # validate data only
    python3 scripts/build_cv.py --env                               # what this computer can do

Exit codes: 0 success | 1 data errors (nothing written) | 2 no PDF engine
(a print-ready HTML was written instead) | 3 the PDF failed the output checks
(file kept as *.FAILED.pdf for inspection; do not give it to the user).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv_core as C  # noqa: E402

FOOTER_RE = re.compile(r"^\s*(Page|صفحة)\s*\d+\s*$")
BUNDLED_FONT_RE = re.compile(r"CV-?(Sans|Serif|Naskh)|OpenSans|Open-Sans|Merriweather|NotoNaskhArabic", re.I)
CHROME_CANDIDATES = [
    "chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome",
    "microsoft-edge", "microsoft-edge-stable", "msedge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


# ------------------------------------------------------------- engines

def find_weasyprint():
    try:
        import weasyprint  # noqa: F401
        return weasyprint
    except Exception:  # missing package or missing system libraries (pango)
        return None


def find_chrome():
    env = os.environ.get("CV_CHROME")
    if env and Path(env).exists():
        return env
    for c in CHROME_CANDIDATES:
        p = shutil.which(c) or (c if os.path.isabs(c) and Path(c).exists() else None)
        if p:
            return p
    return None


def render_weasyprint(html: str, out: Path):
    wp = find_weasyprint()
    wp.HTML(string=html, base_url=str(C.ASSETS)).write_pdf(str(out))


def render_chrome(html: str, out: Path, chrome: str):
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "cv.html"
        src.write_text(html, encoding="utf-8")
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run",
               "--no-default-browser-check", f"--user-data-dir={Path(td) / 'profile'}",
               "--no-pdf-header-footer", "--virtual-time-budget=15000",
               f"--print-to-pdf={out}", src.resolve().as_uri()]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd.insert(1, "--no-sandbox")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if not out.exists() or out.stat().st_size == 0:
            raise RuntimeError("Chrome did not produce a PDF: " + (r.stderr or r.stdout)[-600:])


# --------------------------------------------------------- PDF reading

def _pypdf():
    try:
        import pypdf
        return pypdf
    except Exception:
        return None


def pdf_pages_text(path: Path):
    """List of page texts, or None when no extraction tool exists."""
    pp = _pypdf()
    if pp:
        try:
            r = pp.PdfReader(str(path))
            return [(p.extract_text() or "") for p in r.pages]
        except Exception:
            pass
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-enc", "UTF-8", str(path), "-"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            pages = r.stdout.split("\f")
            if pages and not pages[-1].strip():
                pages = pages[:-1]
            return pages
    return None


def pdf_text_readings(path: Path):
    """{tool: [page texts]} from every text reader available (pypdf, pdftotext, PyMuPDF).
    ATS products use different PDF readers, so the checks below judge the worst one."""
    out = {}
    pp = _pypdf()
    if pp:
        try:
            out["pypdf"] = [(p.extract_text() or "") for p in pp.PdfReader(str(path)).pages]
        except Exception:
            pass
    if shutil.which("pdftotext"):
        try:
            r = subprocess.run(["pdftotext", "-enc", "UTF-8", str(path), "-"],
                               capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                pages = r.stdout.split("\f")
                if pages and not pages[-1].strip():
                    pages = pages[:-1]
                out["pdftotext"] = pages
        except Exception:
            pass
    try:
        import fitz  # PyMuPDF
        with fitz.open(str(path)) as doc:
            out["pymupdf"] = [pg.get_text() for pg in doc]
    except Exception:
        pass
    return out


def pdf_page_count(path: Path):
    pp = _pypdf()
    if pp:
        try:
            return len(pp.PdfReader(str(path)).pages)
        except Exception:
            pass
    pages = pdf_pages_text(path)
    if pages is not None:
        return len(pages)
    raw = path.read_bytes()
    n = len(re.findall(rb"/Type\s*/Page[^s]", raw))
    return n or None


def last_page_lines(path: Path):
    pages = pdf_pages_text(path)
    if not pages:
        return None
    lines = [ln for ln in pages[-1].splitlines() if ln.strip() and not FOOTER_RE.match(ln)]
    return len(lines)


def pdf_fonts(path: Path):
    """[(name, embedded)] using pypdf, else pdffonts, else None."""
    pp = _pypdf()
    if pp:
        try:
            seen = {}
            for page in pp.PdfReader(str(path)).pages:
                res = page.get("/Resources") or {}
                fonts = res.get("/Font") or {}
                for ref in fonts.values():
                    f = ref.get_object()
                    name = str(f.get("/BaseFont", "?")).lstrip("/")
                    desc = f.get("/FontDescriptor")
                    if desc is None and f.get("/DescendantFonts"):
                        desc = f["/DescendantFonts"][0].get_object().get("/FontDescriptor")
                    desc = desc.get_object() if desc is not None else {}
                    emb = any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3"))
                    seen[name] = seen.get(name, False) or emb
            return list(seen.items())
        except Exception:
            pass
    if shutil.which("pdffonts"):
        r = subprocess.run(["pdffonts", str(path)], capture_output=True, text=True, timeout=60)
        out = []
        for ln in r.stdout.splitlines()[2:]:
            parts = ln.split()
            if len(parts) >= 5:
                emb = "yes" in parts[-5:-2]
                out.append((parts[0], emb))
        return out
    return None


# ---------------------------------------------------------- verification

SCRIPT_BOUNDARY_RE = re.compile(r"(?<=[\u0600-\u06FF])(?=[A-Za-z0-9])|(?<=[A-Za-z0-9])(?=[\u0600-\u06FF])")
TOKEN_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)


def _norm_ar(t: str) -> str:
    t = re.sub(r"[\u064B-\u0652\u0670\u0640]", "", t)  # harakat, tatweel
    return (t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه"))


def _tokens(text: str):
    import unicodedata
    # Remove harakat/tatweel before splitting: Python does not count them as word
    # characters, so "خفّض" would otherwise be split into "خف" + "ض".
    text = _norm_ar(unicodedata.normalize("NFKC", text))
    # PDF readers often glue an Arabic word to an adjacent Latin word or number.
    text = SCRIPT_BOUNDARY_RE.sub(" ", text)
    return [w.lower() for w in TOKEN_RE.findall(text)]


def word_integrity(data: dict, pages):
    src = [w for w in _tokens(" ".join(C.iter_strings(data))) if len(w) >= 3 and not w.isdigit()]
    if not src:
        return 1.0, 0, 0
    got = set(_tokens(" ".join(pages)))
    uniq = sorted(set(src))
    found = sum(1 for w in uniq if w in got)
    return found / len(uniq), found, len(uniq)


def _section_present(d: dict, key: str) -> bool:
    v = d.get(key)
    return bool(v.strip()) if isinstance(v, str) else bool(v)


def verify_pdf(path: Path, data: dict, lang: str, budget: int, rep: C.Report):
    size_kb = path.stat().st_size / 1024
    rep.note(f"File size: {size_kb:.0f} KB")
    if size_kb < 5:
        rep.error("The PDF is suspiciously small; rendering probably failed.")
    if size_kb > 2048:
        rep.warn("The PDF is larger than 2 MB; some application portals reject large files.")
    n = pdf_page_count(path)
    if n:
        rep.note(f"Pages: {n} (recommended maximum for this profile: {budget})")
        if n > budget:
            rep.warn(f"The CV has {n} pages; {budget} is recommended for this experience level. "
                     f"Shorten older roles or merge similar bullets.")
    readings = pdf_text_readings(path)
    if not readings:
        rep.note("No PDF text tool (pypdf or pdftotext) is installed, so the text layer was not "
                 "verified. Install pypdf for full checks: pip install pypdf")
    else:
        expected = len(re.sub(r"\s+", "", plain_text(data, lang)))
        labels = dict(C.LABELS[lang]); labels.update(data.get("labels", {}))
        heads = [labels[k] for k in data.get("section_order", []) if k in labels and _section_present(data, k)]
        name_tokens = [w for w in _tokens(data.get("name", "")) if len(w) >= 2]
        head_tokens = sorted({w for h in heads for w in _tokens(h) if len(w) >= 2})
        worst = None
        for tool, pages in readings.items():
            text = "\n".join(pages)
            got = len(re.sub(r"\s+", "", text))
            if expected and got < 0.6 * expected:
                rep.error(f"[{tool}] Only {got} of about {expected} characters could be read back from the PDF. "
                          f"ATS software would miss part of this CV.")
            ratio, found, total = word_integrity(data, pages)
            if worst is None or ratio < worst[1]:
                worst = (tool, ratio, found, total)
            toks = set(_tokens(text))
            miss_name = [w for w in name_tokens if w not in toks]
            if miss_name:
                rep.error(f"[{tool}] The candidate name cannot be read back from the PDF text "
                          f"(misread: {' '.join(miss_name)}).")
            miss_head = [w for w in head_tokens if w not in toks]
            if miss_head:
                rep.error(f"[{tool}] Section headings are misread in the PDF text ({' '.join(miss_head[:6])}). "
                          f"ATS software would not find these sections.")
        tool, ratio, found, total = worst
        rep.note(f"Text layer: {found}/{total} distinct words read back intact ({ratio:.0%}); "
                 f"weakest of {len(readings)} reader(s): {', '.join(readings)}.")
        limit = 0.85
        if ratio < limit:
            rep.error(f"Only {ratio:.0%} of the words can be read back from the PDF by {tool} (minimum {limit:.0%}). "
                      f"Words are being split or replaced; ATS software would misread this CV.")
    fonts = pdf_fonts(path)
    if fonts is None:
        rep.note("Font check skipped (needs pypdf or pdffonts).")
    else:
        not_emb = [f for f, emb in fonts if not emb]
        foreign = sorted({re.sub(r"^[A-Z]{6}\+", "", f) for f, _ in fonts
                          if not BUNDLED_FONT_RE.search(f)})
        if not_emb:
            rep.error("Fonts not embedded: " + ", ".join(not_emb[:6]))
        if foreign:
            rep.warn("Fonts other than the bundled ones were used (" + ", ".join(foreign[:6]) +
                     "). A character may be missing from the bundled fonts; check the PDF visually.")
        rep.note(f"Fonts: {len(fonts)} embedded subsets, all from the bundled set" if not foreign and not not_emb
                 else f"Fonts: {len(fonts)} found")


# ------------------------------------------------------------- outputs

def plain_text(d: dict, lang: str) -> str:
    L = dict(C.LABELS[lang])
    L.update(d.get("labels", {}))
    out = [d.get("name", "")]
    loc = ("، " if lang == "ar" else ", ").join(x for x in (d.get("city"), d.get("country")) if x) or d.get("location", "")
    out += [" | ".join(x for x in (loc, d.get("phone")) if x),
            " | ".join(x for x in (d.get("email"), d.get("linkedin"), d.get("website")) if x)]
    if d.get("personal_details"):
        out.append(" | ".join(d["personal_details"]))
    out = [x for x in out if x]
    for key in d["section_order"]:
        block = []
        if key == "summary" and d.get("summary"):
            block = [d["summary"]]
        elif key == "strengths" and d.get("strengths"):
            block = [f"- {s}" for s in d["strengths"]]
        elif key == "experience":
            for j in d.get("experience", []):
                block.append(" - ".join(x for x in (j.get("company"), j.get("location")) if x))
                block.append(" | ".join(x for x in (j.get("title"), j.get("dates")) if x))
                if j.get("project"):
                    block.append(j["project"])
                block += [f"- {b}" for b in j.get("bullets", [])]
                block.append("")
        elif key == "education":
            for ed in d.get("education", []):
                block.append(" | ".join(x for x in (ed.get("degree"), ed.get("date")) if x))
                block += [x for x in (ed.get("university"), ed.get("location"), ed.get("details")) if x]
        elif key == "projects":
            for p in d.get("projects", []):
                block.append(" | ".join(x for x in (p.get("name"), p.get("date")) if x))
                block += [x for x in (p.get("description"),) if x]
                if p.get("technologies"):
                    block.append(f"{L['technologies']}: {p['technologies']}")
        elif key == "certifications":
            for c in d.get("certifications", []):
                block.append(" | ".join(x for x in (" – ".join(y for y in (c.get("name"), c.get("issuer")) if y),
                                                    c.get("date")) if x))
        elif key == "volunteer":
            for v in d.get("volunteer", []):
                block.append(" | ".join(x for x in (v.get("role"), v.get("organization"), v.get("date")) if x))
                block += [x for x in (v.get("description"),) if x]
        elif key == "awards":
            for a in d.get("awards", []):
                block.append(" | ".join(x for x in (a.get("name"), a.get("issuer"), a.get("date")) if x))
        elif key == "publications":
            for p in d.get("publications", []):
                block.append(" | ".join(x for x in (p.get("title"), p.get("journal"), p.get("date")) if x))
        elif key == "languages":
            for lg in d.get("languages", []):
                block.append(f"{lg['name']}: {lg['level']}" if lg.get("level") else lg["name"])
        while block and not block[-1]:
            block.pop()
        if block:
            out += ["", L[key].rstrip(":").upper() if lang == "en" else L[key].rstrip(":"), *block]
    return "\n".join(out).strip() + "\n"


def fit_and_render(d, lang, style, out: Path, engine, chrome, budget, fit=True):
    """Render, then adjust spacing so the CV respects the page budget and has no near-empty last page."""
    def render(level):
        html = C.full_html(d, lang, style, font_mode="file", level=level)
        if engine == "weasyprint":
            render_weasyprint(html, out)
        else:
            render_chrome(html, out, chrome)
        return pdf_page_count(out), last_page_lines(out)

    pages, lines = render(0)
    if not fit or pages is None or lines is None:
        return 0, pages, lines

    def ok(p, ln):
        return p <= budget and (p == 1 or ln >= 10)

    tried = {0: (pages, lines)}
    # A last page that is less than about a third full looks unfinished: first try
    # to pull it back with slightly tighter spacing.
    if pages > 1 and lines < 18:
        for level in (-1, -2):
            p, ln = render(level)
            tried[level] = (p, ln)
            if p < pages and ok(p, ln):
                print(f"[FIT]   Spacing level {level:+d}: {p} page(s) instead of {pages}.")
                return level, p, ln
        p, ln = render(0)
    if ok(pages, lines):
        return 0, pages, lines
    order = [lv for lv in (-1, -2) if lv not in tried] if (pages > budget or lines < 10) else []
    order += [1, 2, 3] if pages <= budget else []
    for level in order:
        p, ln = render(level)
        tried[level] = (p, ln)
        if ok(p, ln):
            print(f"[FIT]   Spacing level {level:+d}: {p} page(s), last page {ln} line(s).")
            return level, p, ln
    # best effort: fewest pages, then fullest last page, then smallest change
    best = sorted(tried.items(), key=lambda kv: (kv[1][0] > budget, kv[1][0], -(kv[1][1] or 0), abs(kv[0])))[0]
    level = best[0]
    p, ln = render(level)
    print(f"[FIT]   Best effort spacing level {level:+d}: {p} page(s), last page {ln} line(s).")
    return level, p, ln


def save_previews(pdf: Path, dpi: int = 80) -> list:
    """Save each PDF page as <name>_page-N.png (PyMuPDF, else pdftoppm). Returns the files."""
    files = []
    try:
        try:
            import pymupdf as fitz  # PyMuPDF >= 1.24
        except ImportError:
            import fitz  # older PyMuPDF
        doc = fitz.open(str(pdf))
        for i, page in enumerate(doc, 1):
            f = pdf.with_name(f"{pdf.stem}_page-{i}.png")
            page.get_pixmap(dpi=dpi).save(str(f))
            files.append(f)
        return files
    except Exception:
        pass
    exe = shutil.which("pdftoppm")
    if exe:
        prefix = pdf.with_name(f"{pdf.stem}_page")
        subprocess.run([exe, "-r", str(dpi), "-png", str(pdf), str(prefix)], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        files = sorted(pdf.parent.glob(f"{pdf.stem}_page-*.png"))
    return files


def env_report():
    print(f"smart-ats-cv-builder {C.VERSION}")
    print(f"Python {sys.version.split()[0]} ({sys.executable})")
    wp = find_weasyprint()
    print("WeasyPrint:", f"yes ({wp.__version__})" if wp else "no  (pip install weasyprint)")
    ch = find_chrome()
    print("Chrome/Chromium/Edge:", ch or "no")
    print("pypdf:", "yes" if _pypdf() else "no  (pip install pypdf  -> enables full PDF checks)")
    print("pdftotext:", shutil.which("pdftotext") or "no")
    missing = [f for fam in C.FONTS.values() for f, _, _ in fam if not (C.FONT_DIR / f).exists()]
    print("Bundled fonts:", "all present" if not missing else "MISSING " + ", ".join(missing))
    if wp:
        mode = "PDF with WeasyPrint"
    elif ch:
        mode = "PDF with headless Chrome"
    else:
        mode = "print-ready HTML (user saves it as PDF from the browser)"
    print("Best output on this computer:", mode)
    return 0 if not missing else 1


def main():
    ap = argparse.ArgumentParser(description="Build an ATS-friendly CV (PDF, HTML or TXT) from JSON data.")
    ap.add_argument("--data", help="CV data file (JSON, UTF-8)")
    ap.add_argument("--out", help="Output file: .pdf, .html or .txt")
    ap.add_argument("--lang", choices=["auto", "en", "ar"], default="auto")
    ap.add_argument("--style", choices=["bullet", "indent"], default="bullet")
    ap.add_argument("--engine", choices=["auto", "weasyprint", "chrome"], default="auto",
                    help="PDF engine (default: WeasyPrint, then Chrome/Chromium/Edge)")
    ap.add_argument("--font-mode", choices=["embed", "link"], default="embed",
                    help="HTML output only: embed the bundled fonts (default, about 1 MB, works offline) "
                         "or link the same font files online (about 20 KB, needs internet when opened)")
    ap.add_argument("--preview", action="store_true",
                    help="After a successful PDF build, also save each page as PNG for visual review")
    ap.add_argument("--max-pages", type=int, help="Override the recommended page budget")
    ap.add_argument("--no-fit", action="store_true", help="Do not adjust spacing")
    ap.add_argument("--check-only", action="store_true", help="Only validate the data file")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    ap.add_argument("--env", action="store_true", help="Show what this computer can produce")
    a = ap.parse_args()

    if a.env:
        sys.exit(env_report())
    if not a.data or (not a.out and not a.check_only):
        ap.error("--data and --out are required (or use --check-only / --env)")

    rep = C.Report()
    try:
        raw = C.load_json(a.data)
    except FileNotFoundError:
        print(f"[ERROR] Data file not found: {a.data}")
        sys.exit(1)
    except json.JSONDecodeError as ex:
        print(f"[ERROR] The data file is not valid JSON (line {ex.lineno}, column {ex.colno}): {ex.msg}.")
        sys.exit(1)
    d = C.normalise(raw, rep)
    lang = a.lang if a.lang != "auto" else (raw.get("lang") if raw.get("lang") in ("en", "ar") else C.detect_lang(d))
    rep.note(f"Language: {lang}" + (" (detected)" if a.lang == "auto" else ""))
    C.check_data(d, lang, rep)
    rep.print("Data checks")
    if rep.errors or (a.strict and rep.warnings):
        print(f"\nRESULT: FAILED - fix the {len(rep.errors) or len(rep.warnings)} problem(s) above. Nothing was written.")
        sys.exit(1)
    if a.check_only:
        print("\nRESULT: DATA OK")
        sys.exit(0)

    out = Path(a.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    years = C.estimate_years(d)
    budget = a.max_pages or C.page_budget(years)
    ext = out.suffix.lower()

    if ext == ".txt":
        out.write_text(plain_text(d, lang), encoding="utf-8")
        print(f"\nRESULT: OK - plain text written: {out}")
        sys.exit(0)
    if ext in (".html", ".htm"):
        out.write_text(C.full_html(d, lang, a.style, font_mode=a.font_mode, print_help=True), encoding="utf-8")
        print(f"\nRESULT: OK - print-ready HTML written: {out}\n"
              f"Open it in Chrome or Edge > Ctrl+P > Save as PDF, A4, margins Default, headers and footers OFF.\n"
              f"[NOTE] Page fitting for HTML runs in the browser when the file is opened; "
              f"build a .pdf here to get a checked page count.")
        sys.exit(0)
    if ext != ".pdf":
        print("[ERROR] --out must end with .pdf, .html or .txt")
        sys.exit(1)

    chrome = find_chrome()
    engine = a.engine
    if engine == "auto":
        engine = "weasyprint" if find_weasyprint() else ("chrome" if chrome else None)
    elif engine == "weasyprint" and not find_weasyprint():
        engine = None
    elif engine == "chrome" and not chrome:
        engine = None
    if engine is None:
        html_out = out.with_suffix(".html")
        html_out.write_text(C.full_html(d, lang, a.style, font_mode="embed", print_help=True), encoding="utf-8")
        print(f"\n[INFO] No PDF engine here (WeasyPrint or Chrome). Wrote a print-ready HTML instead:\n  {html_out}\n"
              f"Give this file to the user: open in Chrome or Edge > Ctrl+P > Save as PDF, A4, "
              f"margins Default, headers and footers OFF.\nRESULT: HTML FALLBACK")
        sys.exit(2)

    try:
        level, pages, lines = fit_and_render(d, lang, a.style, out, engine, chrome, budget, fit=not a.no_fit)
    except Exception as ex:  # rendering crashed
        print(f"[ERROR] {engine} could not render the PDF: {ex}")
        html_out = out.with_suffix(".html")
        html_out.write_text(C.full_html(d, lang, a.style, font_mode="embed", print_help=True), encoding="utf-8")
        print(f"Wrote a print-ready HTML instead: {html_out}\nRESULT: HTML FALLBACK")
        sys.exit(2)

    vrep = C.Report()
    vrep.note(f"Engine: {engine}; spacing level {level:+d}")
    verify_pdf(out, d, lang, budget, vrep)
    vrep.print("PDF checks")
    if vrep.errors:
        failed = out.with_name(out.stem + ".FAILED.pdf")
        out.replace(failed)
        print(f"\nRESULT: FAILED - the PDF did not pass the checks and was renamed to {failed.name}. "
              f"Do not send it to the user.")
        sys.exit(3)
    if a.preview:
        shots = save_previews(out)
        if shots:
            print("Preview images (for checking only, do not send):")
            for f in shots:
                print(f"  {f}")
        else:
            print("[NOTE] No preview: install PyMuPDF (pip install pymupdf) or poppler (pdftoppm).")
    sha = hashlib.sha256(out.read_bytes()).hexdigest()[:12]
    print(f"\nRESULT: OK - {out} ({pages} page(s), sha256 {sha})")
    sys.exit(0)


if __name__ == "__main__":
    main()
