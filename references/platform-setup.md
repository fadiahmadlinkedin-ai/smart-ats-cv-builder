# Platform setup

This skill follows the open Agent Skills format (a folder with `SKILL.md`, `scripts/`, `references/`, `assets/`). The folder must stay named `cv-2026-top`, the same as the `name` field. Facts below were checked against each vendor's help pages in October 2026. Menus change, so follow the vendor page if a label differs.

## Which mode each platform gets

| Platform | How the skill is loaded | Best output |
| :--- | :--- | :--- |
| Manus | Skill folder in the skills directory | PDF (WeasyPrint) |
| Claude apps (Free, Pro, Max, Team, Enterprise) | Customize > Skills > "+" > Create skill > Upload a skill (ZIP of the folder). Needs **Code execution and file creation** on in Settings > Capabilities | PDF, or HTML if no PDF engine |
| Claude Code | Folder in `~/.claude/skills/` or the project's `.claude/skills/` | PDF |
| ChatGPT Business, Enterprise, Edu, Healthcare | Skills > Create > Upload from your computer (uploaded skills are scanned first) | PDF or HTML, depending on the sandbox |
| OpenAI Codex, Cursor and other Agent Skills clients | Copy the folder into the client's skills directory | PDF |
| Gemini app | Upload works only in the web app at gemini.google.com: Customize > Skills > Create > Upload > select `cv-2026-top.zip` > Create (needs a personal Google account, age 18+ and Keep Activity on). Then type `/` or `@` in a chat, on any device, and pick the skill. Google lists plain-text files, `.py`, `.html`, `.json` and `.png` as supported, but not `.ttf` fonts. If the upload is refused, on a computer use Add files > More uploads > Import code > `https://github.com/fadiahmadlinkedin-ai/cv-2026-top`. Do not attach the ZIP in a chat: a chat ZIP may hold only 10 files | Script PDF if code runs with the fonts present; otherwise a PDF through Gemini's own file creation (copy test in `no-code-mode.md`) |
| Gemini CLI | `gemini skills install <path-or-git-url>`, or copy into `~/.gemini/skills/` | PDF |
| Gemini Gems, custom GPTs, any chat without code | Paste `SKILL.md` into the instructions and add `references/*.md` and `assets/no-code/*.html` as knowledge files | Hand-filled HTML or plain text (`references/no-code-mode.md`) |

Google's Gemini CLI page notes that for unpaid-tier and Google One users, Gemini CLI was replaced by Antigravity CLI on 18 June 2026. Follow Google's current instructions there; the skill folder itself does not change.

No-code HTML loads its fonts from fixed public copies of the bundled files, so the user needs internet access when opening it. The HTML that `build_cv.py` writes embeds the fonts and works offline.

If a platform drops the `.ttf` files, `--env` reports them as missing. English PDFs then build with substitute fonts and a warning, and Arabic PDFs fail the text check on purpose, so switch to the no-code route for Arabic.

## Check what the computer can do

Run this once at the start:

```bash
python3 scripts/build_cv.py --env
```

It reports Python, WeasyPrint, Chrome/Chromium/Edge, pypdf and whether all bundled fonts are present, and names the best output for that machine.

| Situation | What `build_cv.py --out cv.pdf` does |
| :--- | :--- |
| WeasyPrint installed | Builds the PDF with WeasyPrint and checks it |
| No WeasyPrint, but Chrome, Chromium or Edge found | Builds the PDF in headless Chrome and checks it |
| Neither | Writes `cv.html` with the fonts embedded and a page-fit script, prints `RESULT: HTML FALLBACK`, exit code 2. Give the HTML to the user with the print steps. The page count is only known once the user prints it |
| No Python at all | Use `references/no-code-mode.md` |

Optional installs that make the result stronger (only if the environment allows it):

```bash
pip install weasyprint pypdf pymupdf
```

`pypdf` enables the full text-layer check (it confirms that ATS software can read every word back). When `pdftotext` (poppler) or `pymupdf` are also installed, the check runs with each of them and judges the weakest result. `pymupdf` enables `--preview` page images. Nothing else is required: the fonts are bundled, nothing is downloaded, and no admin rights are needed.

## Packaging the skill for upload

Zip the folder itself so that the archive contains `cv-2026-top/SKILL.md` at its top level:

```bash
cd <folder that contains cv-2026-top>
zip -r cv-2026-top.zip cv-2026-top -x "*/__pycache__/*" "*.pyc"
```

The archive is about 1.5 MB, mostly the bundled fonts. Do not remove the fonts: without them Arabic text and digits can render incorrectly.
