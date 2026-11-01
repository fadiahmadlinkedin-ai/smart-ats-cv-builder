---
name: smart-ats-cv-builder
description: Create, rewrite, translate or tailor professional ATS-friendly CVs and resumes in English or Arabic, delivered as a print-ready PDF with a clean single-column design, embedded fonts and built-in quality checks. Use when someone asks to write, improve, update or reformat a CV or resume, adapt it to a job advert, turn notes or an old CV into a new one, or build an Arabic CV (سيرة ذاتية، سي في، تحديث السيرة الذاتية). Works with or without code execution.
license: Free for personal use; do not sell or re-attribute (LICENSE.md). Bundled fonts are SIL Open Font License 1.1 (assets/fonts/OFL.txt).
metadata:
  version: "7.3.0"
  author: "Fadi Ahmad"
  homepage: "https://www.fadiahmad.com"
  languages: "en, ar"
  requires: "Python 3.8+ for PDF; WeasyPrint or Chrome/Chromium/Edge; no-code mode needs nothing"
---

# Smart ATS CV Builder

Build a one- to three-page, single-column CV that applicant tracking systems (ATS) read cleanly and recruiters find easy to scan. The design is fixed and tested: black serif name, Open Sans body (Noto Naskh Arabic in Arabic, bold for the name and headings), thin maroon dividers, A4, page numbers. Your job is the content. The script handles layout, fonts, page fitting and checks.

All paths below are relative to this skill's folder.

## Workflow

### 1. Gather facts

Collect what the candidate provides: an old CV, notes, LinkedIn text, a job advert. Then read `references/content-guide.md`. Its first rule overrides everything else: **never invent companies, titles, dates, numbers or percentages**. If key facts are missing, ask once, using the question list in section 2 of that guide. If the candidate cannot answer, continue without numbers.

Match the CV language to the request: English, or Arabic (right-to-left). If the candidate needs both, build two separate files.

### 2. Write the content

Follow `references/content-guide.md` for the summary, achievement bullets, skills, tailoring to an advert, section order, length and regional norms. Use `references/action-verbs-and-keywords.md` for strong verbs (English and Arabic) and industry keywords. Only use a keyword that is true for the candidate.

### 3. Choose the mode

Check whether you can run commands. If you can, run:

```bash
python3 scripts/build_cv.py --env
```

| You can... | Mode | Read |
| :--- | :--- | :--- |
| run Python | **Script mode** (steps 4–6 below). Gives a checked PDF, or a print-ready HTML when no PDF engine exists | this file |
| not run code | **No-code mode**: write the CV by hand, then deliver a PDF with the platform's own file creation, or a hand-filled HTML or plain text | `references/no-code-mode.md` |

The user expects a PDF in every mode. Installation per platform (Manus, Claude, ChatGPT, Gemini, Codex, Gemini CLI, Gems, custom GPTs) is in `references/platform-setup.md`.

### 4. Write the data file (script mode)

Write the content to a UTF-8 JSON file. Use the schema in `references/data-schema.md`, and start from the closest example:

| Example | Use for |
| :--- | :--- |
| `assets/examples/en_senior.json` | experienced professional, 2 pages |
| `assets/examples/en_graduate.json` | graduate or career changer: education and projects first, renamed headings |
| `assets/examples/ar_mid.json` | Arabic CV, mid-level, 1 page |

`bullets`, `strengths` and every other list must be JSON lists, never one long string.

### 5. Build

```bash
python3 scripts/build_cv.py --data cv.json --out Firstname_Lastname_CV.pdf --preview
```

Options: `--lang en|ar` (default: auto-detect), `--style bullet|indent` (bullet points, or indented paragraphs without bullet marks), `--max-pages N` (override the length rule), `--check-only` (validate the data only), `--strict` (warnings become errors), `--out file.html` or `--out file.txt` (HTML for browser printing, or plain text for online forms), `--font-mode link` (HTML only: about 20 KB instead of 1 MB, but needs internet when opened).

The script validates the data, renders with WeasyPrint or headless Chrome/Chromium/Edge, adjusts spacing to avoid a nearly empty last page, and then checks the PDF. It confirms the page count, that the bundled fonts were embedded, and that the name, the section headings and at least 85% of the words read back correctly with every PDF text reader on the machine (pypdf, pdftotext, PyMuPDF), because ATS products use different readers. Arabic diacritics (harakat, shadda) and stretched letters (tatweel inside a word) are removed automatically: CVs are written without them, ATS keyword search may not match them, and Chrome splits words at them in the PDF text.

### 6. Read the result and act on it

| Last line / exit code | Meaning | What to do |
| :--- | :--- | :--- |
| `RESULT: OK` / 0 | PDF passed every check | Review the warnings, look at the preview PNGs, then deliver the PDF |
| `RESULT: FAILED` / 1 | Data problem, nothing was written | Fix each `[ERROR]` in the JSON and run again |
| `RESULT: HTML FALLBACK` / 2 | No PDF engine on this computer | Deliver the `.html` with the print steps below |
| `RESULT: FAILED` / 3 | PDF built but failed a check; renamed `*.FAILED.pdf` | Never deliver it. Read the `[ERROR]`, fix, rebuild |

Treat warnings seriously: weak phrases, first-person summary, long bullets, missing dates or contacts. Fix them unless the candidate decided otherwise.

If the run produced preview images, look at every page before delivering. Check alignment, that no section heading is stranded at the bottom of a page, and that the text is the candidate's own.

### 7. Deliver

Send the PDF named `Firstname_Lastname_CV.pdf`. Never send preview images, `*.FAILED.pdf` files or the JSON unless asked. Add two or three lines saying what was improved and which facts the candidate should double-check. If no numbers were available, name the bullets that would get stronger with real figures.

For an HTML deliverable, include these steps for the user:

> Open the file in Google Chrome or Microsoft Edge > Ctrl+P (Cmd+P on Mac) > Destination **Save as PDF** > Paper **A4** > Margins **Default** > **Headers and footers off** > Save.

HTML files fit their own line spacing in the browser to avoid a nearly empty last page, but only a PDF built here has a checked page count and text layer. Prefer the PDF whenever an engine exists.

## Fixed design rules (do not override)

1. Single column only: no tables, text boxes, columns, icons, skill bars, photos or logos.
2. No emoji or decorative symbols. The build rejects characters the fonts cannot print.
3. Contacts sit in the body, not in a page header. The footer shows only the page number.
4. Do not edit the templates in `assets/` to change fonts, sizes or colours. Change the content instead: shorten older roles before considering anything else.
5. Use one date format throughout, newest first.

## Files

| Path | Purpose |
| :--- | :--- |
| `scripts/build_cv.py` | The single command: validate, render, fit, check |
| `scripts/cv_core.py` | Data loading, validation and HTML building (imported by `build_cv.py`) |
| `assets/template_en.html`, `assets/template_ar.html` | Design used by the script |
| `assets/no-code/` | Ready-to-edit HTML CVs for no-code mode |
| `assets/fonts/` | Bundled OFL fonts, licence and glyph coverage table |
| `assets/examples/` | Fictional example data files |
| `assets/samples/` | Images of the examples as built by the script, for showing the design |
| `references/` | Content guide, data schema, verbs and keywords, no-code mode, platform setup |
