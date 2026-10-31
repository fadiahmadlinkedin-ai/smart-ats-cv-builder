# Content guide

How to turn a candidate's raw material into strong, honest CV content. Read it before writing the JSON.

## 1. The rule that overrides everything: never invent facts

Every company, title, date, degree, certificate, number and percentage must come from the candidate. A CV with invented metrics can cost the candidate the job, or the job later, once the claim is checked in an interview or a reference call.

- Numbers the candidate gave: use them exactly as given.
- No numbers given: ask once (questions below). If the candidate cannot answer, write a strong bullet without numbers. Do not estimate.
- Unclear facts (dates, titles): ask, or leave the item out. Do not guess.
- You may improve wording, order, and focus. You may not add achievements, tools, or responsibilities the candidate did not mention.

| Candidate said | Wrong (invented) | Right (honest and strong) |
| :--- | :--- | :--- |
| "I fix laptops" | "Repaired 30+ laptops weekly with a 96% fix rate" | "Diagnosed and repaired laptops, phones and game consoles, handling hardware and software faults end to end" |
| "I managed a team" | "Led a 12-person team to 35% growth" | "Led the sales team through weekly pipeline reviews and individual coaching" |
| "صيانة لابتوبات" | "أصلح أكثر من 30 جهازا أسبوعيا بنسبة نجاح 96%" | "شخص وأصلح أعطال الحواسيب المحمولة والهواتف وأجهزة الألعاب، من القطع إلى البرمجيات" |

## 2. Questions to ask (once, all together)

Ask only for facts that are missing. Keep it to one message:

1. Target job title, country, and (if available) the job advert text.
2. For each recent role: team size, budget or volume handled (customers, tickets, orders, projects, devices per week), and one result they are proud of with an approximate number.
3. Exact month/year for each role, and whether the latest role is current.
4. Certificates and degrees with year and issuer.
5. Languages and level.

Arabic version for Arabic-speaking candidates:

> لتقوية سيرتك الذاتية أحتاج بعض الأرقام التقريبية إن وجدت: كم شخصا في فريقك؟ كم عميلا أو طلبا أو جهازا تتعامل معه أسبوعيا؟ هل هناك تحسن لاحظته (وقت، تكلفة، مبيعات) ونسبته التقريبية؟ وما تاريخ بداية ونهاية كل وظيفة (الشهر والسنة)؟

If the candidate says they do not know, continue without numbers. Do not ask a second time.

## 3. Writing achievement bullets

Use the X-Y-Z pattern when the facts exist: accomplished **X**, measured by **Y**, by doing **Z**.

> Cut month-end close from 10 to 6 working days (Y) for five subsidiaries (X) by automating bank reconciliations in SAP (Z).

- Start every bullet with a strong action verb, and vary the verbs. `references/action-verbs-and-keywords.md` has lists in English and Arabic.
- Keep each bullet to one or two printed lines. Put 3–6 bullets on recent roles and 1–3 on older ones.
- Lead with results, not duties. Avoid "responsible for", "duties included", "tasked with", "helped with", "worked on", "مسؤول عن", "المهام تشمل", "ساعدت في".
- Do not use first person (I, my, أنا, خبرتي). Arabic bullets should start with a past-tense verb: قاد، طور، خفض، أدار. Write Arabic without diacritics (harakat, shadda) or stretched letters (tatweel); the builder removes them anyway, because ATS keyword search may not match them.
- Use the candidate's gender for Arabic verb forms (قاد / قادت), and keep it consistent.
- Optional `project` line under a job: one sentence of context (scope, team, product). It is not a bullet.

## 4. Professional summary

Three or four lines, 40–80 words, written without pronouns. It should state:

1. the target title and total years of experience,
2. two or three areas of real strength, matching the target job,
3. one proof point (a result, scale, or credential),
4. optionally, the kind of role or industry sought.

## 5. Skills (`strengths`)

Group skills on 2–4 lines, e.g. `"Systems: SAP S/4HANA, Power BI, Excel (advanced)"`. List tools and methods the candidate actually uses. Put the exact terms from the job advert first when they are true, because ATS keyword matching compares literal words. Spell out an acronym once if both forms are common, e.g. "Search Engine Optimisation (SEO)". Leave out soft-skill clichés such as "hard-working" or "team player"; show them in the bullets instead.

## 6. Tailoring to a job advert

When the candidate shares a job advert:

1. Extract the job title, the must-have skills, tools, certificates and years of experience.
2. Use the advert's exact job title in the summary if the candidate's experience truly matches it.
3. Reorder bullets and skills so the most relevant ones come first.
4. Mirror the advert's wording for skills the candidate really has (e.g. "stakeholder management" rather than "dealing with people").
5. Never add a requirement the candidate does not meet. Mention real gaps to the candidate instead of hiding them in the CV.

## 7. Section order

- Experienced candidates: Summary, Strengths, Experience, Education, then the rest (default order).
- Fresh graduates or career changers: Summary, Education, Projects, Experience, Skills. Set `section_order` and rename the skills heading with `labels`, as in `assets/examples/en_graduate.json`.
- Order sections and entries newest first.

## 8. Length

The builder estimates years of experience from the dates and warns when the page count exceeds the norm:

| Experience | Recommended length |
| :--- | :--- |
| under 5 years | 1 page |
| 5–15 years | 1–2 pages |
| over 15 years | 2–3 pages |

When content runs long, shorten older roles first (one or two bullets, or a single line). Do not shrink the font.

## 9. Regional norms

| Market | Usual practice |
| :--- | :--- |
| USA, Canada | No photo, age, date of birth, gender, marital status or nationality. "Resume", 1–2 pages. |
| UK, Ireland | No photo or date of birth. "CV", usually 2 pages. |
| Germany, Austria, Switzerland | Exact month/year dates are expected. A photo is traditional but optional; this design has no photo slot. |
| Gulf (Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, Oman) | Nationality, visa status, notice period and driving licence are commonly listed under `personal_details` if the candidate agrees. If an employer insists on a photo, send it separately. |
| Arab countries generally | Arabic CVs are welcome for local employers. Multinationals usually expect English; build both if the candidate needs both. |

Never include religion, health, ID or passport numbers, or a full home address. A city and country are enough.

## 10. What makes a CV ATS-friendly (and what this builder already does)

The builder outputs a single-column layout with no tables, text boxes, icons, images or columns. It uses real text with embedded fonts, standard section headings, contacts in the body (not in a page header), and a plain "Page N" footer only. Keep the content side clean too: no emoji, no special symbols, no skill bars or ratings such as "Excel 4/5". Write the same date format everywhere.
