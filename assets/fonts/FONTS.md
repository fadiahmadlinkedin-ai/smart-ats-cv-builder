# Bundled fonts

All fonts here are unmodified files licensed under the SIL Open Font License 1.1 (full text in `OFL.txt`). They may be bundled, embedded in PDFs and redistributed with this skill. They may not be sold on their own.

| File | Family | Version | Source (pinned commit) |
| :--- | :--- | :--- | :--- |
| OpenSans-Regular/Bold/Italic/BoldItalic.ttf | Open Sans | 3.003 | github.com/googlefonts/opensans @ bd7e376 |
| Merriweather-Black.ttf | Merriweather Black | 2.200 | github.com/SorkinType/Merriweather @ 4481226 |
| NotoNaskhArabic-Regular/Bold.ttf | Noto Naskh Arabic | 2.012 | github.com/notofonts/noto-fonts @ ffebf8c (hinted/ttf) |

The `link` font mode (`build_cv.py --font-mode link` and the no-code templates) loads these same files, byte for byte, from the pinned commits through jsDelivr, with GitHub as a fallback.

Do not replace the Arabic fonts with Google Fonts, Fontsource or WOFF2 copies, or with newer Noto Arabic builds (2.02x). In tests with Chrome's Save as PDF those versions left only 15–26% of Arabic words readable in the PDF text layer, which ATS software relies on. These files give 97–100%.

Arabic name and headings use Noto Naskh Arabic Bold on purpose. Noto Kufi Arabic Bold (2.102 and 2.107) and Noto Sans Arabic Bold map their lam-alef ligature (لا، لأ، لإ) to the wrong character order, so pdftotext and PyMuPDF read "المؤهلات" as "المؤهالت" and names such as "علاء" or "صلاح" as "عالء" and "صالح". Noto Naskh Arabic reads back correctly with pypdf, pdftotext, PyMuPDF and Apache PDFBox (used by Apache Tika).

`coverage.json` lists the characters each font contains. `scripts/cv_core.py` uses it to reject CV text that the fonts cannot display, so no character is ever printed as an empty box. Regenerate it if a font file changes.
