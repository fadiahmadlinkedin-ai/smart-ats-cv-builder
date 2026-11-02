# No-code mode

Use this when the assistant cannot run Python, for example a chat-only model, a custom GPT or Gem without code execution, or any environment where `scripts/build_cv.py` fails to start. The content rules in `content-guide.md` still apply in full.

## Deliver a PDF

The user expects a PDF. Use the first route that works:

1. **The platform's own file creation.** Some assistants create PDF files directly in the chat (Gemini has done so for all users since April 2026). Write the finished CV, then create the PDF with this structure: one column, the standard section headings, real selectable text, A4, and no tables, columns, text boxes, photos, logos or icons. An Arabic CV runs right to left. Name the file `Firstname_Lastname_CV.pdf` and give the user the copy test below.
2. **Hand-filled HTML** (Option A). The user saves it as a PDF from Chrome or Edge. This is the safest route for Arabic, because the design and its fonts were tested for ATS reading.
3. **Plain text** (Option B), for application forms that only accept pasted text.

**Copy test (tell the user):** open the PDF, select all the text, copy it and paste it into a plain text editor. Every word should appear whole and in order. If Arabic letters come out separated, reversed or out of order, ATS software will misread them too: use the HTML route for that CV.

## Option A: hand-filled HTML (keeps the professional design)

1. Choose the template: `assets/no-code/cv_template_en.html` (English, left to right) or `assets/no-code/cv_template_ar.html` (Arabic, right to left). Each is a complete, finished CV filled with a fictional person, so you can see every block in context.
2. Copy the file unchanged, then edit only the text inside `<body>`. Never touch `<head>`: it holds the fonts, page size, margins, page numbers, divider style and a small page-fit script.
3. Replace every sample value with the candidate's confirmed facts. Remove the instruction comment at the top of `<body>`, and make sure no sample name, company or `example.com` address is left anywhere.
4. Add or remove blocks by copying or deleting whole elements:

| Need | Copy or delete this block |
| :--- | :--- |
| Another job | `<div class="exp-entry"> ... </div>` |
| Another bullet | `<p>• Bullet text</p>` inside `exp-achievements` |
| Another degree | `<div class="edu-entry"> ... </div>` |
| Another skill line | `<li>...</li>` inside `strengths-list` |
| Another certificate / language / award | the matching `cert-`, `lang-item` or `award-` block |
| Remove a section | from its `<hr class="maroon-line">` up to (not including) the next one |

5. Write `&amp;` for `&`, `&lt;` for `<` and `&gt;` for `>` inside text. Do not add emoji or icons, because the fonts do not contain them.
6. In the Arabic template, keep phone numbers, email addresses and links inside `<span class="ltr" dir="ltr">...</span>` so they display left to right.
7. Do not add tables, columns, photos, logos, colours or new CSS. They break ATS parsing and the design.
8. If you cannot create the PDF yourself, give the user the finished file named `Firstname_Lastname_CV.html` (or the full HTML in one code block if you cannot attach files, with a note to save it as a `.html` file) with these steps:

> Open the file in Google Chrome or Microsoft Edge while connected to the internet, press Ctrl+P (Cmd+P on Mac), set Destination to **Save as PDF**, Paper size **A4**, Margins **Default**, and switch **Headers and footers off**. Then click Save.

What happens in the browser:

- The yellow help note at the top of the page is hidden automatically when printing.
- The fonts load from fixed public copies of the bundled font files, so the computer needs internet access when the file is opened. Offline, the browser uses system fonts: the PDF stays readable, but it loses the designed look and may break pages differently. If the name does not appear in a bold serif (English) or bold Naskh (Arabic) typeface, tell the user to reconnect and reopen the file.
- The page-fit script adjusts line spacing so the printed CV does not end with a nearly empty page. It never changes the text. If the CV is still longer than the length table in `content-guide.md`, shorten older roles.
- Recommend only Chrome or Edge "Save as PDF" for Arabic CVs. Other print engines and online HTML-to-PDF converters were not tested and can break the Arabic text layer that ATS software reads.

## Option B: plain text (for online application forms)

Some application portals only accept pasted text. Write it in this order, with section headings in capitals (English) or on their own line (Arabic), one blank line between sections, and a hyphen at the start of each bullet:

```text
FULL NAME
City, Country | Phone | Email | LinkedIn

PROFESSIONAL SUMMARY
...

SKILLS
Area: skill, skill, skill

EXPERIENCE
Job Title | Company, City | MM/YYYY – Present
- Achievement bullet
- Achievement bullet

EDUCATION
Degree | University, City | Year
```

When code execution is available, `build_cv.py --out cv.txt` produces the same layout from the JSON data.

## Self-check before delivering (no tools needed)

Read the final HTML or text once more and confirm each point:

1. The name, phone and email are the candidate's own and correctly spelled.
2. No sample text from the template remains (search for "Okafor", "Northwind", "سارة", "example.com", "555").
3. Every number, date, title and employer comes from the candidate. Nothing was invented.
4. Bullets start with action verbs (Arabic: a verbal noun such as إدارة، مراجعة، الإشراف على, never a past-tense verb) and are 1–2 lines long; the summary has no "I/my".
5. Dates use one format throughout, newest first.
6. The length fits the experience (see the table in `content-guide.md`).
7. Arabic CV: the phone number is written without spaces (`+966555550123`), so it copies in the right order.
