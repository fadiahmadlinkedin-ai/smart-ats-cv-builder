#!/usr/bin/env python3
"""smart-ats-cv-builder core library.

Loads, normalises and validates CV data, then builds the HTML that every
rendering engine turns into the final document. Standard library only
(Python 3.8+), so it runs in any sandbox, laptop or code interpreter.
"""
from __future__ import annotations

import base64
import datetime as _dt
import html as _html
import json
import re
import unicodedata
from pathlib import Path

VERSION = "7.4.0"
SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS = SKILL_DIR / "assets"
FONT_DIR = ASSETS / "fonts"

# CSS family -> [(file, weight, style)]. Unique family names make sure the
# bundled files are used even if the computer has other versions installed.
FONTS = {
    "CV Sans": [("OpenSans-Regular.ttf", 400, "normal"), ("OpenSans-Bold.ttf", 700, "normal"),
                ("OpenSans-Italic.ttf", 400, "italic"), ("OpenSans-BoldItalic.ttf", 700, "italic")],
    "CV Serif": [("Merriweather-Black.ttf", 900, "normal")],
    "CV Naskh": [("NotoNaskhArabic-Regular.ttf", 400, "normal"), ("NotoNaskhArabic-Bold.ttf", 700, "normal")],
}
# "link" font mode (small HTML files such as the no-code templates) loads the
# same files as assets/fonts from pinned commits, so they are byte-identical and
# cannot change. Do not switch to Google Fonts, Fontsource/WOFF2 subsets or newer
# Noto Arabic builds: tested in Chrome, they leave only 15-26% of Arabic words
# readable in the PDF text layer (97% with these files).
FONT_REPOS = {
    "OpenSans": ("googlefonts/opensans", "bd7e37632246368c60fdcbd374dbf9bad11969b6", "fonts/ttf/"),
    "Merriweather": ("SorkinType/Merriweather", "4481226b336843648b5b2ee64f75737f262ded15", "fonts/ttf/"),
    "NotoNaskhArabic": ("notofonts/noto-fonts", "ffebf8c1ee449e544955a7e813c54f9b73848eac",
                        "hinted/ttf/NotoNaskhArabic/"),
}


def remote_font_urls(fname: str) -> list:
    """Public copies of a bundled font file: jsDelivr first, GitHub raw as fallback."""
    repo, sha, sub = FONT_REPOS[fname.split("-")[0]]
    return [f"https://cdn.jsdelivr.net/gh/{repo}@{sha}/{sub}{fname}",
            f"https://raw.githubusercontent.com/{repo}/{sha}/{sub}{fname}"]

LABELS = {
    "en": {"summary": "Professional Summary", "strengths": "Professional strengths include:",
           "experience": "Experience", "education": "Education", "projects": "Projects",
           "certifications": "Certifications", "volunteer": "Volunteer Experience",
           "awards": "Awards", "publications": "Publications", "languages": "Languages",
           "technologies": "Technologies"},
    "ar": {"summary": "الملخص المهني", "strengths": "نقاط القوة المهنية:",
           "experience": "الخبرات المهنية", "education": "المؤهلات العلمية", "projects": "المشاريع",
           "certifications": "الشهادات والدورات", "volunteer": "الأعمال التطوعية",
           "awards": "الجوائز", "publications": "المنشورات", "languages": "اللغات",
           "technologies": "التقنيات"},
}
DEFAULT_ORDER = ["summary", "strengths", "experience", "education", "projects",
                 "certifications", "volunteer", "awards", "publications", "languages"]

CONTACT_KEYS = ["email", "phone", "city", "country", "location", "linkedin", "website"]
TEXT_KEYS = ["name", "summary"] + CONTACT_KEYS
LIST_STR_KEYS = ["strengths", "personal_details"]
OBJ_SECTIONS = {
    "experience": ["company", "location", "title", "dates", "project", "bullets"],
    "education": ["degree", "university", "location", "date", "details"],
    "projects": ["name", "date", "description", "technologies"],
    "certifications": ["name", "issuer", "date"],
    "volunteer": ["role", "organization", "date", "description"],
    "awards": ["name", "issuer", "date"],
    "publications": ["title", "journal", "date"],
    "languages": ["name", "level"],
}
META_KEYS = ["section_order", "labels", "target_role", "lang", "$schema", "_comment", "notes"]
KNOWN_TOP = set(TEXT_KEYS) | set(LIST_STR_KEYS) | set(OBJ_SECTIONS) | set(META_KEYS) | {"contact"}

TOP_ALIASES = {
    "full_name": "name", "fullname": "name", "skills": "strengths", "core_skills": "strengths",
    "key_skills": "strengths", "competencies": "strengths", "work_experience": "experience",
    "employment": "experience", "jobs": "experience", "work": "experience",
    "certificates": "certifications", "courses": "certifications", "training": "certifications",
    "profile": "summary", "objective": "summary", "about": "summary",
    "mobile": "phone", "telephone": "phone", "linkedin_url": "linkedin",
    "portfolio": "website", "url": "website", "personal_info": "personal_details",
    "volunteering": "volunteer", "honors": "awards",
}
ITEM_ALIASES = {
    "experience": {"employer": "company", "organization": "company", "organisation": "company",
                   "position": "title", "role": "title", "job_title": "title", "date": "dates",
                   "period": "dates", "duration": "dates", "achievements": "bullets",
                   "responsibilities": "bullets", "highlights": "bullets", "scope": "project"},
    "education": {"institution": "university", "school": "university", "college": "university",
                  "year": "date", "dates": "date", "graduation": "date", "gpa": "details",
                  "honors": "details"},
    "projects": {"title": "name", "tech": "technologies", "stack": "technologies",
                 "tools": "technologies", "year": "date", "dates": "date", "summary": "description"},
    "certifications": {"title": "name", "certificate": "name", "organization": "issuer",
                       "provider": "issuer", "authority": "issuer", "year": "date", "dates": "date"},
    "volunteer": {"title": "role", "position": "role", "org": "organization",
                  "company": "organization", "year": "date", "dates": "date"},
    "awards": {"title": "name", "award": "name", "organization": "issuer", "year": "date", "dates": "date"},
    "publications": {"name": "title", "publisher": "journal", "venue": "journal",
                     "conference": "journal", "year": "date", "dates": "date"},
    "languages": {"language": "name", "lang": "name", "proficiency": "level"},
}

PRESENT_WORDS = re.compile(r"present|current|now|today|ongoing|الحاضر|حتى الآن|الآن|حاليا|حاليًا|مستمر", re.I)
PLACEHOLDER_RES = [
    (re.compile(r"lorem ipsum", re.I), "Lorem ipsum filler text"),
    (re.compile(r"\{\{[^}]*\}\}"), "an unfilled {{placeholder}}"),
    (re.compile(r"\b(TODO|TBD|FIXME)\b"), "a TODO/TBD marker"),
    (re.compile(r"\[(?:your|company|name|date|role|title|city|country|insert|add)[^\]]*\]", re.I),
     "a [bracket placeholder]"),
    (re.compile(r"\bX{3,}\b"), "an XXX placeholder"),
    (re.compile(r"your name|company name|job title here", re.I), "template wording"),
    (re.compile(r"اسم الشركة|اسمك هنا|المسمى الوظيفي هنا|ضع هنا"), "template wording"),
]
ARABIC_MARKS_RE = re.compile(r"[\u064B-\u065F\u0670]|(?<=[\u0620-\u064A])\u0640+(?=[\u0620-\u064A])")
# Tatweel is removed only inside a word (stretched letters); "لـ 350" and "بـ SAP" keep it.
ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
FORBIDDEN = {
    "en": ["responsible for", "duties included", "tasked with", "helped with", "worked on", "assisted in"],
    "ar": ["مسؤول عن", "مسؤولة عن", "المهام تشمل", "كلف ب", "كلفت ب", "تضمنت مهامي", "ساعدت في"],
}
FIRST_PERSON = {
    "en": re.compile(r"\b(i|my|me|myself|i'm|i've)\b", re.I),
    "ar": re.compile(r"(^|\s)(أنا|لدي|لديّ|خبرتي|مهاراتي|أسعى|أطمح)(\s|$)"),
}


class Report:
    """Collects ERROR / WARN / NOTE messages."""

    def __init__(self):
        self.errors, self.warnings, self.notes = [], [], []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def note(self, msg):
        self.notes.append(msg)

    def extend(self, other):
        self.errors += other.errors
        self.warnings += other.warnings
        self.notes += other.notes

    def print(self, title="Checks"):
        print(f"--- {title} ---")
        for m in self.errors:
            print(f"[ERROR] {m}")
        for m in self.warnings:
            print(f"[WARN]  {m}")
        for m in self.notes:
            print(f"[NOTE]  {m}")
        if not (self.errors or self.warnings or self.notes):
            print("[OK]    nothing to report")


# ----------------------------------------------------------------- loading

def _clean_text(v) -> str:
    """Return a trimmed string; numbers become strings; control chars removed."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return ""
    if isinstance(v, (int, float)):
        v = str(v)
    if not isinstance(v, str):
        return v  # caller reports the wrong type
    v = unicodedata.normalize("NFC", v)
    v = "".join(ch for ch in v if ch in "\n\t" or unicodedata.category(ch) != "Cc")
    # Arabic harakat (incl. shadda) and in-word tatweel: CVs are written without them,
    # ATS keyword search may not match them, and Chrome PDFs split words at them.
    v = ARABIC_MARKS_RE.sub("", v)
    return re.sub(r"[ \t]+", " ", v).strip()


def _str_list(value, where, rep):
    """Coerce to a list of non-empty strings, reporting problems clearly."""
    if value in (None, "", []):
        return []
    if isinstance(value, str):
        rep.error(f"{where} is one text value but must be a JSON list, e.g. [\"First point\", "
                  f"\"Second point\"], so each point prints on its own line.")
        return []
    if not isinstance(value, list):
        rep.error(f"{where} must be a list of text items, got {type(value).__name__}.")
        return []
    out = []
    for i, item in enumerate(value):
        if isinstance(item, dict):
            # {"category": "Tools", "items": ["Git", "Docker"]} -> "Tools: Git, Docker"
            cat = _clean_text(item.get("category") or item.get("name") or item.get("title") or "")
            items = item.get("items") or item.get("skills") or item.get("values") or []
            if isinstance(items, str):
                items = [items]
            if isinstance(items, list) and all(isinstance(x, (str, int, float)) for x in items):
                joined = ", ".join(_clean_text(x) for x in items if _clean_text(x))
                text = f"{cat}: {joined}" if cat and joined else (cat or joined)
                if text:
                    out.append(text)
                continue
            rep.error(f"{where}[{i}] is an object that cannot be read as text.")
            continue
        t = _clean_text(item)
        if not isinstance(t, str):
            rep.error(f"{where}[{i}] must be text, got {type(item).__name__}.")
            continue
        if t:
            out.append(t)
    return out


def load_json(path) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def normalise(raw, rep: Report) -> dict:
    """Map aliases, coerce types and return clean data. Problems go to rep."""
    if not isinstance(raw, dict):
        rep.error("The data file must contain one JSON object { ... } at the top level.")
        return {}
    data = dict(raw)

    # contact block -> flat fields
    contact = data.pop("contact", None)
    if isinstance(contact, dict):
        for k, v in contact.items():
            k2 = TOP_ALIASES.get(k, k)
            if k2 in CONTACT_KEYS and not data.get(k2):
                data[k2] = v
            elif k2 not in CONTACT_KEYS:
                rep.warn(f"contact.{k} is not a supported contact field and was ignored.")
    elif isinstance(contact, str) and contact.strip():
        rep.warn("'contact' was free text; put email, phone, city, country, linkedin in their own fields.")
        data.setdefault("location", contact)

    for alias, canon in TOP_ALIASES.items():
        if alias in data:
            if data.get(canon) in (None, "", []):
                data[canon] = data[alias]
                rep.note(f"Field '{alias}' was read as '{canon}'.")
            else:
                rep.warn(f"Both '{alias}' and '{canon}' exist; '{alias}' was ignored.")
            del data[alias]

    for k in list(data):
        if k not in KNOWN_TOP:
            rep.warn(f"Top-level field '{k}' is not supported and will not appear in the CV.")

    out = {}
    for k in TEXT_KEYS:
        v = _clean_text(data.get(k, ""))
        if not isinstance(v, str):
            rep.error(f"'{k}' must be text, got {type(data.get(k)).__name__}.")
            v = ""
        out[k] = v
    for k in LIST_STR_KEYS:
        out[k] = _str_list(data.get(k), k, rep)

    for sec, fields in OBJ_SECTIONS.items():
        val = data.get(sec)
        items = []
        if val in (None, "", []):
            out[sec] = []
            continue
        if isinstance(val, dict):
            val = [val]
            rep.warn(f"'{sec}' was a single object; it was treated as a list with one item.")
        if not isinstance(val, list):
            rep.error(f"'{sec}' must be a list of entries, got {type(val).__name__}.")
            out[sec] = []
            continue
        for i, item in enumerate(val):
            where = f"{sec}[{i}]"
            if sec == "languages" and isinstance(item, str):
                t = _clean_text(item)
                if t:
                    items.append({"name": t, "level": ""})
                continue
            if not isinstance(item, dict):
                rep.error(f"{where} must be an object {{...}}, got {type(item).__name__}.")
                continue
            item = dict(item)
            if sec == "experience" and "description" in item:
                desc = item.pop("description")
                if isinstance(desc, list) and not item.get("bullets") and not item.get("achievements"):
                    item["bullets"] = desc
                elif isinstance(desc, str) and not item.get("project") and not item.get("scope"):
                    item["project"] = desc
            for alias, canon in ITEM_ALIASES.get(sec, {}).items():
                if alias in item:
                    if item.get(canon) in (None, "", []):
                        item[canon] = item[alias]
                    del item[alias]
            clean = {}
            for f in fields:
                if sec == "experience" and f == "bullets":
                    clean[f] = _str_list(item.get(f), f"{where}.bullets", rep)
                    continue
                v = item.get(f, "")
                if isinstance(v, list) and f in ("technologies", "details", "description"):
                    v = ", ".join(_clean_text(x) for x in v if isinstance(x, (str, int, float)))
                v = _clean_text(v)
                if not isinstance(v, str):
                    rep.error(f"{where}.{f} must be text, got {type(item.get(f)).__name__}.")
                    v = ""
                if f in ("dates", "date") and v:
                    # one range style everywhere: "09/2020 - 12/2021" -> "09/2020 – 12/2021"
                    # (ISO dates such as 2020-01 are left alone)
                    v = re.sub(r"\s+(?:-{1,2}|\u2014|\u2012|\u2212)\s+", " \u2013 ", v)
                    v = re.sub(r"(?<=\d{4})(?:-{1,2}|\u2014|\u2012|\u2212)(?=(?:\d{1,2}/)?\d{4}\b|[^\W\d_])",
                               " \u2013 ", v)
                    v = re.sub(r"\s*\u2013\s*", " \u2013 ", v)
                clean[f] = v
            for k in item:
                if k not in fields:
                    rep.warn(f"{where}.{k} is not a supported field and will not appear.")
            if any(clean.values()):
                items.append(clean)
        out[sec] = items

    order = data.get("section_order")
    if order is not None:
        if not isinstance(order, list) or any(s not in DEFAULT_ORDER for s in order):
            rep.error(f"'section_order' must be a list using only: {', '.join(DEFAULT_ORDER)}.")
            order = None
        else:
            order = list(dict.fromkeys(order)) + [s for s in DEFAULT_ORDER if s not in order]
    out["section_order"] = order or list(DEFAULT_ORDER)

    labels = data.get("labels") or {}
    if not isinstance(labels, dict):
        rep.error("'labels' must be an object, e.g. {\"strengths\": \"Technical Skills\"}.")
        labels = {}
    out["labels"] = {k: _clean_text(v) for k, v in labels.items()
                     if k in LABELS["en"] and isinstance(_clean_text(v), str) and _clean_text(v)}
    for k in labels:
        if k not in LABELS["en"]:
            rep.warn(f"labels.{k} is not a known section label and was ignored.")
    out["target_role"] = _clean_text(data.get("target_role", "")) if isinstance(data.get("target_role", ""), str) else ""
    return out


# ------------------------------------------------------------- inspection

def iter_strings(d):
    if isinstance(d, str):
        yield d
    elif isinstance(d, dict):
        for k, v in d.items():
            if k in ("section_order",):
                continue
            yield from iter_strings(v)
    elif isinstance(d, list):
        for v in d:
            yield from iter_strings(v)


def detect_lang(data) -> str:
    text = " ".join(iter_strings({k: v for k, v in data.items() if k != "labels"}))
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "en"
    ar = sum(1 for c in letters if ARABIC_RE.match(c))
    return "ar" if ar / len(letters) >= 0.3 else "en"


_COVERAGE = None


def coverage() -> dict:
    """{font file: [[start, end], ...]} computed from the bundled fonts."""
    global _COVERAGE
    if _COVERAGE is None:
        _COVERAGE = json.loads((FONT_DIR / "coverage.json").read_text(encoding="utf-8"))
    return _COVERAGE


def _covered(cp: int) -> bool:
    for ranges in coverage().values():
        for a, b in ranges:
            if a <= cp <= b:
                return True
    return False


def unsupported_chars(text: str) -> list:
    bad = []
    for ch in sorted(set(text)):
        if ch.isspace() or unicodedata.category(ch) in ("Cf", "Cc", "Mn") and ord(ch) < 0x0600:
            continue
        if unicodedata.category(ch) == "Cf":
            continue
        if not _covered(ord(ch)):
            bad.append(ch)
    return bad


def estimate_years(data) -> int:
    """Approximate total years of experience from the dates of each role."""
    now = _dt.date.today().year
    spans = []
    for job in data.get("experience", []):
        d = job.get("dates", "")
        years = [int(y) for y in re.findall(r"(?<!\d)(19[5-9]\d|20\d\d)(?!\d)", d)]
        if not years:
            continue
        start = min(years)
        end = now if PRESENT_WORDS.search(d) else max(years)
        if end >= start:
            spans.append((start, end))
    if not spans:
        return 0
    spans.sort()
    total, (cs, ce) = 0, spans[0]
    for s, e in spans[1:]:
        if s <= ce:
            ce = max(ce, e)
        else:
            total += ce - cs
            cs, ce = s, e
    total += ce - cs
    return max(total, 0)


def page_budget(years: int) -> int:
    """Maximum recommended pages."""
    if years < 5:
        return 1
    if years <= 15:
        return 2
    return 3


# Arabic bullets start with a verbal noun (masdar): إدارة، مراجعة، الإشراف على. It reads the same for
# men and women. Common past-tense openings are flagged so they can be rewritten (words that are
# also verbal nouns, such as خفض، رفع، وضع، عمل, are left out).
AR_PAST_OPENERS = set("""
قاد قادت أدار أدارت طور طورت خفضت أعد أعدت نفذ نفذت أشرف أشرفت نظم نظمت حقق حققت راجع راجعت
طبق طبقت نسق نسقت أنشأ أنشأت صمم صممت حسن حسنت سجل سجلت طابق طابقت شارك شاركت تولى تولت أعاد أعادت
قدم قدمت حلل حللت درب دربت رفعت زاد زادت وفر وفرت تابع تابعت بنى بنت أطلق أطلقت أسس أسست جهز جهزت
عملت ساهم ساهمت أنجز أنجزت اعتمد اعتمدت أجرى أجرت كتب كتبت ترأس ترأست وضعت حدث حدثت
""".split())
def _ar_key(word: str) -> str:
    w = ARABIC_MARKS_RE.sub("", word).strip("،,.:;")
    return re.sub("[\u0622\u0623\u0625]", "\u0627", w)
_AR_PAST_KEYS = {_ar_key(w) for w in AR_PAST_OPENERS}
def apply_lang_rules(data: dict, lang: str, rep: Report) -> None:
    """Language-specific clean-up, run once the language is known."""
    if lang != "ar" or not data:
        return
    phone = data.get("phone", "")
    if phone:
        # In a right-to-left line, a phone number with spaces is copied in reverse order by
        # Chrome's PDF reader ("0000 000 79 +962"). Written as one block it stays intact.
        packed = re.sub(r"[\s\-\u2010-\u2014.()]+", "", phone)
        if packed != phone:
            data["phone"] = packed
            rep.note(f"Phone written without spaces for the Arabic CV: {packed}")
def check_data(data: dict, lang: str, rep: Report) -> None:
    """Content and safety checks on normalised data (errors block rendering)."""
    if not data:
        return
    if not data.get("name"):
        rep.error("'name' is missing. The CV must start with the candidate's full name.")
    has_exp = any(j.get("company") or j.get("title") for j in data.get("experience", []))
    has_edu = any(e.get("degree") or e.get("university") for e in data.get("education", []))
    if not has_exp and not has_edu:
        rep.error("Add at least one 'experience' or 'education' entry; a CV cannot be built from a name only.")
    if not (data.get("email") or data.get("phone")):
        rep.warn("No email and no phone number: employers will have no way to reach the candidate.")
    email = data.get("email", "")
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        rep.warn(f"Email '{email}' does not look like a valid address.")
    if re.search(r"@example\.(com|org|net)$", email or "", re.I):
        rep.warn("The email uses example.com, which is a placeholder. Replace it with the real address.")

    all_text = "\n".join(iter_strings(data))
    for rx, what in PLACEHOLDER_RES:
        m = rx.search(all_text)
        if m:
            rep.error(f"Found {what}: '{m.group(0)}'. Replace it with real content before building.")
    bad = unsupported_chars(all_text)
    if bad:
        shown = " ".join(f"'{c}' (U+{ord(c):04X})" for c in bad[:12])
        rep.error("These characters are not in the bundled fonts and would print as empty boxes: "
                  f"{shown}. Remove them (emoji, icons, decorative symbols) or replace them with plain text.")

    letters = [c for c in all_text if c.isalpha()]
    if letters:
        ar_ratio = sum(1 for c in letters if ARABIC_RE.match(c)) / len(letters)
        if lang == "ar" and ar_ratio < 0.3:
            rep.warn(f"Language is 'ar' but only {ar_ratio:.0%} of the letters are Arabic. Check --lang.")
        if lang == "en" and ar_ratio > 0.3:
            rep.warn(f"Language is 'en' but {ar_ratio:.0%} of the letters are Arabic. Check --lang.")

    # content quality (advice, never blocking)
    for i, job in enumerate(data.get("experience", [])):
        where = f"experience[{i}]"
        if not job.get("company"):
            rep.warn(f"{where} has no company name.")
        if not job.get("title"):
            rep.warn(f"{where} has no job title.")
        if not job.get("dates"):
            rep.warn(f"{where} has no dates; recruiters and ATS expect a period such as 03/2021 – Present.")
        if not job.get("bullets"):
            rep.warn(f"{where} has no achievement bullets.")
        for b in job.get("bullets", []):
            low = b.lower()
            for p in FORBIDDEN["en" if lang == "en" else "ar"]:
                if p in low:
                    rep.warn(f"Weak phrase '{p}' in {where}: '{b[:60]}...'. Start with an action verb instead.")
            if len(b.split()) > 45:
                rep.warn(f"Long bullet in {where} ({len(b.split())} words). Keep bullets to 1–2 lines.")
    summary = data.get("summary", "")
    if summary:
        if FIRST_PERSON[lang].search(summary):
            rep.warn("The summary uses first person (I / my / أنا / خبرتي). Write it without pronouns.")
        n = len(summary.split())
        if n > 90:
            rep.warn(f"The summary has {n} words. Aim for 3–4 lines (about 40–80 words).")
    else:
        rep.warn("No professional summary. A 3–4 line summary helps both recruiters and ATS.")
    if not data.get("strengths"):
        rep.warn("No skills listed in 'strengths'. ATS keyword matching relies on this section.")

    starts = {}
    for job in data.get("experience", []):
        for b in job.get("bullets", []):
            w = (b.split() or [""])[0].lower().strip(",.:;")
            if w:
                starts[w] = starts.get(w, 0) + 1
    if lang == "ar":
        past = []
        for sec in ("experience", "projects", "volunteer"):
            for job in data.get(sec, []):
                for b in job.get("bullets", []):
                    first = (b.split() or [""])[0]
                    if _ar_key(first) in _AR_PAST_KEYS or _ar_key(first)[1:] in _AR_PAST_KEYS and first[:1] in "و":
                        past.append(first)
        if past:
            rep.warn("Arabic bullets start with a past-tense verb (" + "، ".join(dict.fromkeys(past)) +
                     "). Start each bullet with a verbal noun instead: إدارة، مراجعة، إعداد، الإشراف على.")
    rep_verbs = [f"'{w}' x{c}" for w, c in starts.items() if c > 2]
    if rep_verbs:
        rep.note("Repeated opening words: " + ", ".join(rep_verbs) + ". Vary the opening words.")
    bullets = [b for j in data.get("experience", []) for b in j.get("bullets", [])]
    if bullets:
        with_num = sum(1 for b in bullets if re.search(r"\d", b))
        rep.note(f"{with_num}/{len(bullets)} bullets contain a number. Use only numbers the candidate "
                 f"confirmed; never invent metrics.")
    years = estimate_years(data)
    rep.note(f"Estimated experience: {years} year(s); recommended length: up to {page_budget(years)} page(s).")


# ------------------------------------------------------------ HTML build

def e(text) -> str:
    return _html.escape(text or "", quote=True)


def _href(url: str) -> str:
    u = url.strip()
    if re.match(r"^[a-z][a-z0-9+.-]*:", u, re.I):
        return u
    return "https://" + u.lstrip("/")


def font_face_css(lang: str, mode: str, text: str = "") -> str:
    """@font-face rules. mode: file (local file URLs), embed (base64), link (pinned public copies)."""
    has_ar = lang == "ar" or bool(ARABIC_RE.search(text))
    rules = []
    for fam, files in FONTS.items():
        # Link mode (hand-filled templates) keeps Naskh so later Arabic text still
        # prints; unicode-range means the browser only downloads it when needed.
        if fam == "CV Naskh" and not has_ar and mode != "link":
            continue
        if lang == "ar" and fam == "CV Serif":
            continue
        for fname, weight, style in files:
            if lang == "ar" and style == "italic":
                continue
            path = FONT_DIR / fname
            extra = ""
            if mode == "embed":
                src = "url(data:font/ttf;base64," + base64.b64encode(path.read_bytes()).decode("ascii") + ") format('truetype')"
            elif mode == "link":
                src = ", ".join(f"url('{u}') format('truetype')" for u in remote_font_urls(fname))
                if lang == "en" and fam == "CV Naskh":
                    extra = " unicode-range: U+0600-06FF, U+0750-077F, U+08A0-08FF, U+FB50-FDFF, U+FE70-FEFF;"
            else:
                src = f"url('{path.resolve().as_uri()}') format('truetype')"
            rules.append("@font-face { font-family: '%s'; src: %s; font-weight: %d; font-style: %s; font-display: block;%s }"
                         % (fam, src, weight, style, extra))
    return "\n".join(rules)


def _contact_lines(d: dict, rtl: bool) -> list:
    ltr = (lambda s: f'<span class="ltr" dir="ltr">{s}</span>') if rtl else (lambda s: s)
    comma = "، " if rtl else ", "
    lines = []
    first = []
    loc = comma.join(x for x in (d.get("city"), d.get("country")) if x) or d.get("location", "")
    if loc:
        first.append(e(loc))
    if d.get("phone"):
        first.append(ltr(e(d["phone"])))
    if first:
        lines.append(" | ".join(first))
    second = []
    if d.get("email"):
        second.append(ltr(f'<a href="mailto:{e(d["email"])}">{e(d["email"])}</a>'))
    for k in ("linkedin", "website"):
        if d.get(k):
            second.append(ltr(f'<a href="{e(_href(d[k]))}">{e(d[k])}</a>'))
    if second:
        lines.append(" | ".join(second))
    if d.get("personal_details"):
        lines.append(" | ".join(e(x) for x in d["personal_details"]))
    return lines


HR = '<hr class="maroon-line">'


def _title(t, cls="section-title"):
    return f'<div class="{cls}">{e(t)}</div>'


def _row(left_cls, left_html, right_cls, right_text, row_cls="row"):
    right = f'<span class="{right_cls}">{e(right_text)}</span>' if right_text else ""
    return f'<div class="{row_cls}"><span class="{left_cls}">{left_html}</span>{right}</div>'


def _sections(d: dict, lang: str, style: str) -> dict:
    L = dict(LABELS[lang])
    L.update(d.get("labels", {}))
    S = {}
    if d.get("summary"):
        S["summary"] = [HR, _title(L["summary"]), f'<div class="summary-text">{e(d["summary"])}</div>']
    if d.get("strengths"):
        S["strengths"] = [HR, _title(L["strengths"], "strengths-title"), HR,
                          '<ul class="strengths-list">' + "".join(f"<li>{e(s)}</li>" for s in d["strengths"]) + "</ul>"]
    if d.get("experience"):
        p = [HR, _title(L["experience"]), HR]
        for j in d["experience"]:
            p.append('<div class="exp-entry">')
            company = f'<span class="exp-company-name">{e(j["company"])}</span>'
            if j.get("location"):
                company += f' - <span class="exp-location">{e(j["location"])}</span>'
            p.append(f'<div class="exp-company-line">{company}</div>')
            p.append(_row("exp-job-title", e(j.get("title")), "exp-date", j.get("dates"), "exp-title-row"))
            if j.get("project"):
                p.append(f'<div class="exp-project">{e(j["project"])}</div>')
            if j.get("bullets"):
                if style == "indent":
                    p.append('<div class="exp-achievements indent-style">' +
                             "".join(f"<p>{e(b)}</p>" for b in j["bullets"]) + "</div>")
                else:
                    p.append('<div class="exp-achievements">' +
                             "".join(f"<p>\u2022 {e(b)}</p>" for b in j["bullets"]) + "</div>")
            p.append("</div>")
        S["experience"] = p
    if d.get("education"):
        p = [HR, _title(L["education"])]
        for ed in d["education"]:
            p.append('<div class="edu-entry">')
            p.append(_row("edu-degree", e(ed.get("degree") or ed.get("university")), "edu-date", ed.get("date")))
            if ed.get("university") and ed.get("degree"):
                p.append(f'<div class="edu-university">{e(ed["university"])}</div>')
            if ed.get("location"):
                p.append(f'<div class="edu-location">{e(ed["location"])}</div>')
            if ed.get("details"):
                p.append(f'<div class="edu-details">{e(ed["details"])}</div>')
            p.append("</div>")
        S["education"] = p
    if d.get("projects"):
        p = [HR, _title(L["projects"])]
        for pr in d["projects"]:
            p.append('<div class="project-entry">')
            p.append(_row("project-name", e(pr.get("name")), "project-date", pr.get("date")))
            if pr.get("description"):
                p.append(f'<div class="project-desc">{e(pr["description"])}</div>')
            if pr.get("technologies"):
                p.append(f'<div class="project-tech">{e(L["technologies"])}: {e(pr["technologies"])}</div>')
            p.append("</div>")
        S["projects"] = p
    if d.get("certifications"):
        p = [HR, _title(L["certifications"])]
        for c in d["certifications"]:
            name = c.get("name", "")
            if c.get("issuer") and c["issuer"] not in name:
                name = f"{name} \u2013 {c['issuer']}" if name else c["issuer"]
            p.append(_row("cert-name", e(name), "cert-date", c.get("date"), "row cert-row"))
        S["certifications"] = p
    if d.get("volunteer"):
        p = [HR, _title(L["volunteer"])]
        for v in d["volunteer"]:
            p.append('<div class="volunteer-entry">')
            if v.get("role"):
                p.append(f'<div class="volunteer-role">{e(v["role"])}</div>')
            org = v.get("organization", "")
            if org or v.get("date"):
                line = e(org) + (f" ({e(v['date'])})" if v.get("date") else "") if org else e(v["date"])
                p.append(f'<div class="volunteer-org">{line}</div>')
            if v.get("description"):
                p.append(f'<div class="volunteer-desc">{e(v["description"])}</div>')
            p.append("</div>")
        S["volunteer"] = p
    if d.get("awards"):
        p = [HR, _title(L["awards"])]
        for a in d["awards"]:
            p.append('<div class="award-entry">')
            p.append(_row("award-name", e(a.get("name")), "award-date", a.get("date")))
            if a.get("issuer"):
                p.append(f'<div class="award-issuer">{e(a["issuer"])}</div>')
            p.append("</div>")
        S["awards"] = p
    if d.get("publications"):
        p = [HR, _title(L["publications"])]
        for pb in d["publications"]:
            p.append('<div class="pub-entry">')
            p.append(f'<div class="pub-title">{e(pb.get("title"))}</div>')
            det = " | ".join(e(x) for x in (pb.get("journal"), pb.get("date")) if x)
            if det:
                p.append(f'<div class="pub-details">{det}</div>')
            p.append("</div>")
        S["publications"] = p
    if d.get("languages"):
        p = [HR, _title(L["languages"])]
        for lg in d["languages"]:
            if lg.get("level"):
                p.append(f'<div class="lang-item"><strong>{e(lg["name"])}:</strong> {e(lg["level"])}</div>')
            else:
                p.append(f'<div class="lang-item">{e(lg["name"])}</div>')
        S["languages"] = p
    return S


PRINT_HELP = {
    "en": ("<div class=\"print-help\"><strong>To save this CV as PDF:</strong> open this file in Google Chrome "
           "or Microsoft Edge, press Ctrl+P (Cmd+P on Mac), choose <em>Save as PDF</em>, paper size "
           "<em>A4</em>, margins <em>Default</em>, and turn <em>Headers and footers</em> off. "
           "This yellow note does not appear in the PDF.</div>"),
    "ar": ("<div class=\"print-help\"><strong>لحفظ السيرة الذاتية بصيغة PDF:</strong> افتح هذا الملف في متصفح "
           "Google Chrome أو Microsoft Edge، واضغط Ctrl+P (أو Cmd+P في ماك)، واختر «حفظ بتنسيق PDF»، "
           "وحجم الورق A4، والهوامش «افتراضي»، وألغِ خيار «الرؤوس والتذييلات». "
           "هذه الملاحظة الصفراء لا تظهر في ملف PDF.</div>"),
}


def body_html(d: dict, lang: str, style: str = "bullet") -> str:
    rtl = lang == "ar"
    parts = [f'<div class="name">{e(d.get("name"))}</div>']
    parts += [f'<div class="contact-line">{ln}</div>' for ln in _contact_lines(d, rtl)]
    parts.append(HR)
    secs = _sections(d, lang, style)
    for key in d.get("section_order", DEFAULT_ORDER):
        for piece in secs.get(key, []):
            if piece == HR and parts and parts[-1] == HR:
                continue
            parts.append(piece)
    if parts and parts[-1] == HR:
        parts.pop()
    return "\n".join(parts)


SPACING_CSS = {
    # negative levels tighten (to pull a few orphan lines back), positive expand
    -2: "body{line-height:1.25 !important}.summary-text{line-height:1.22 !important;margin:2px 0 !important}"
        ".exp-entry{margin-bottom:4px !important}.exp-achievements p{margin-bottom:0 !important}"
        ".maroon-line{margin:3px 25% !important}.strengths-list{margin:2px 0 !important}"
        ".project-entry,.volunteer-entry{margin-bottom:3px !important}",
    -1: "body{line-height:1.3 !important}.summary-text{line-height:1.27 !important;margin:3px 0 !important}"
        ".exp-entry{margin-bottom:6px !important}.exp-achievements p{margin-bottom:1px !important}"
        ".maroon-line{margin:4px 25% !important}",
    1: "body{line-height:1.45 !important}.exp-entry{margin-bottom:12px !important}"
       ".exp-achievements p{margin-bottom:4px !important}.section-title{padding:3px 0 !important}"
       ".maroon-line{margin:8px 25% !important}",
    2: "body{line-height:1.55 !important}.exp-entry{margin-bottom:16px !important}"
       ".exp-achievements p{margin-bottom:6px !important}.section-title{padding:5px 0 !important}"
       ".maroon-line{margin:9px 25% !important}",
    3: "body{line-height:1.65 !important}.exp-entry{margin-bottom:20px !important}"
       ".exp-achievements p{margin-bottom:8px !important}.section-title{padding:7px 0 !important}"
       ".maroon-line{margin:10px 25% !important}",
}
AR_LINE_BONUS = {-2: "1.32", -1: "1.36", 1: "1.5", 2: "1.6", 3: "1.7"}


def _level_rules(level: int, lang: str) -> str:
    css = SPACING_CSS[level]
    if lang == "ar":  # Arabic needs a little more line height than Latin text
        css = re.sub(r"body\{line-height:[0-9.]+", "body{line-height:" + AR_LINE_BONUS[level], css)
        css = re.sub(r"\.summary-text\{line-height:[0-9.]+", ".summary-text{line-height:" + AR_LINE_BONUS[level], css)
    return css


def spacing_css(level: int, lang: str) -> str:
    if not level:
        return ""
    return f"/* spacing level {level} */\n" + _level_rules(level, lang)


def _fit_class(level: int) -> str:
    return ("fit-m%d" if level < 0 else "fit-p%d") % abs(level)


def fit_classes_css(lang: str) -> str:
    """The spacing levels as classes on <html>, chosen in the browser by FIT_SCRIPT."""
    out = ["/* page fit for browser printing (classes set by the script in <head>) */"]
    for level in sorted(SPACING_CSS):
        prefix = "html." + _fit_class(level) + " "
        for rule in _level_rules(level, lang).split("}"):
            if "{" in rule:
                sel, body = rule.split("{", 1)
                out.append(",".join(prefix + s.strip() for s in sel.split(",")) + "{" + body + "}")
    return "\n".join(out)


# Runs only when the HTML is opened in a browser (the script-mode PDF engines get
# the spacing level directly). It never changes text: it measures the CV at the
# A4 content height (297 mm minus 28 mm of page margin, frame padding and footer) and picks the spacing
# level that avoids a nearly empty last page, like build_cv.py does for PDFs.
FIT_SCRIPT = """<script>
/* Page fit: picks line spacing so the printed CV has no nearly empty last page. Do not edit. */
(function () {
  var PAGE = 269 * 96 / 25.4, NAMES = ["fit-m2", "fit-m1", "fit-p1", "fit-p2", "fit-p3"];
  function set(level) {
    var c = document.documentElement.classList;
    NAMES.forEach(function (n) { c.remove(n); });
    if (level) c.add((level < 0 ? "fit-m" : "fit-p") + Math.abs(level));
  }
  function measure() {
    var first = document.querySelector(".name"), last = document.body.lastElementChild;
    while (last && last.tagName === "SCRIPT") last = last.previousElementSibling;
    if (!first || !last) return null;
    var h = last.getBoundingClientRect().bottom - first.getBoundingClientRect().top;
    var pages = Math.max(1, Math.ceil(h / PAGE - 0.002));
    return { h: h, pages: pages, fill: h / PAGE - (pages - 1) };
  }
  function fit() {
    set(0);
    var m0 = measure(), i, m;
    if (!m0 || m0.pages < 2) return;
    if (m0.fill < 0.33) {
      for (i = -1; i >= -2; i--) {
        set(i); m = measure();
        /* room for one fewer page; each extra page break can waste some space */
        if (m.h <= ((m0.pages - 1) - 0.08 * (m0.pages - 2) - 0.005) * PAGE) return;
      }
      set(0);
    }
    if (m0.fill >= 0.2) return;
    for (i = 1; i <= 3; i++) {
      set(i); m = measure();
      if (m.pages === m0.pages && m.fill >= 0.2 && m.fill <= 0.92) return;
    }
    set(0);
  }
  window.addEventListener("beforeprint", fit);
  function start() { (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(fit); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
</script>"""


def full_html(d: dict, lang: str, style: str = "bullet", font_mode: str = "file",
              print_help: bool = False, level: int = 0, auto_fit=None) -> str:
    """auto_fit (default: same as print_help) adds the in-browser page fit for HTML deliverables."""
    if auto_fit is None:
        auto_fit = print_help
    tpl = (ASSETS / f"template_{lang}.html").read_text(encoding="utf-8")
    text = "\n".join(iter_strings(d))
    title = (d.get("name") or "CV") + (" – السيرة الذاتية" if lang == "ar" else " – CV")
    extra = spacing_css(level, lang) + "\n.ltr{direction:ltr;unicode-bidi:isolate;}"
    if auto_fit:
        extra += "\n" + fit_classes_css(lang)
    out = (tpl.replace("/*{{FONT_FACES}}*/", font_face_css(lang, font_mode, text))
              .replace("/*{{EXTRA_CSS}}*/", extra)
              .replace("{{TITLE}}", e(title))
              .replace("{{AUTHOR}}", e(d.get("name")))
              .replace("{{PRINT_HELP}}", PRINT_HELP[lang] if print_help else "")
              .replace("{{CONTENT}}", body_html(d, lang, style)))
    if auto_fit:
        out = out.replace("</head>", FIT_SCRIPT + "\n</head>", 1)
    return out
