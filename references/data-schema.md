# CV data format (JSON)

The builder reads one UTF-8 JSON file. Only `name` plus at least one `experience` or `education` entry are required; every other field is optional and empty sections are simply left out. Working files are in `assets/examples/` (`en_senior.json`, `en_graduate.json`, `ar_mid.json`).

## Top-level fields

| Field | Type | Notes |
| :--- | :--- | :--- |
| `name` | text | Required. Full name exactly as the candidate writes it. |
| `email`, `phone` | text | Give at least one. Phone in international format, e.g. `+966 55 555 0123`. |
| `city`, `country` | text | Printed as "City, Country". Use `location` instead if you only have one string. |
| `linkedin`, `website` | text | Short form without `https://` reads best, e.g. `linkedin.com/in/name`. |
| `personal_details` | list of text | Optional line under the contacts, e.g. `["Nationality: Jordanian", "Driving licence: UAE"]`. Only add what the target market expects and the candidate agreed to share. |
| `summary` | text | 3–4 lines, no "I/my". |
| `strengths` | list of text | Skill groups, one line each, e.g. `"Tools: SAP, Power BI, Excel"`. |
| `experience` | list of objects | Newest first. See below. |
| `education` | list of objects | Newest first. |
| `projects`, `certifications`, `volunteer`, `awards`, `publications`, `languages` | list of objects | Optional sections. |
| `section_order` | list of section keys | Optional. Default: `summary, strengths, experience, education, projects, certifications, volunteer, awards, publications, languages`. Sections you leave out of the list are added at the end. |
| `labels` | object | Optional heading overrides, e.g. `{"strengths": "Technical Skills"}`. |
| `lang` | `"en"` or `"ar"` | Optional. Without it the language is detected from the text. |
| `target_role`, `notes`, `_comment` | text | Ignored by the renderer; use them for your own notes. |

## Section objects

| Section | Fields (bold = should be present) |
| :--- | :--- |
| `experience` | **`company`**, **`title`**, **`dates`**, `location`, `project` (one-line scope or context), **`bullets`** (list of text) |
| `education` | **`degree`**, **`university`**, `location`, `date`, `details` (honours, GPA, thesis) |
| `projects` | **`name`**, `date`, `description`, `technologies` |
| `certifications` | **`name`**, `issuer`, `date` |
| `volunteer` | **`role`**, `organization`, `date`, `description` |
| `awards` | **`name`**, `issuer`, `date` |
| `publications` | **`title`**, `journal`, `date` |
| `languages` | **`name`**, `level` |

Dates are free text, so use one style throughout: `03/2021 – Present`, `2019 – 2022`, or in Arabic `03/2021 – الحاضر`. The builder estimates years of experience from these dates. It recognises Present, Current, Now, الحاضر, حتى الآن and حاليًا.

## Accepted alternative names

Common field names from other tools are converted automatically, so data pasted from another format still works:

| You can write | Becomes |
| :--- | :--- |
| `full_name` | `name` |
| `skills`, `core_skills`, `key_skills`, `competencies` | `strengths` |
| `work_experience`, `employment`, `jobs`, `work` | `experience` |
| `profile`, `objective`, `about` | `summary` |
| `certificates`, `courses`, `training` | `certifications` |
| `mobile`, `telephone` → `phone`; `linkedin_url` → `linkedin`; `portfolio`, `url` → `website` | |
| `volunteering` → `volunteer`; `honors` → `awards`; `personal_info` → `personal_details` | |
| `contact: {email, phone, ...}` | flattened into the top level |
| in experience: `employer`, `organization` → `company`; `position`, `role`, `job_title` → `title`; `date`, `period`, `duration` → `dates`; `achievements`, `responsibilities`, `highlights` → `bullets`; `scope` → `project` | |
| in education: `institution`, `school`, `college` → `university`; `year`, `dates`, `graduation` → `date`; `gpa`, `honors` → `details` | |
| in projects: `title` → `name`; `tech`, `stack`, `tools` → `technologies`; `summary` → `description` | |
| in languages: `language`, `lang` → `name`; `proficiency` → `level` | |

## What stops the build (errors)

The builder writes nothing and exits with code 1 when:

1. the file is not valid JSON (the message gives line and column);
2. `name` is missing, or there is neither an experience nor an education entry;
3. a field has the wrong type. For example, `bullets` given as one string instead of a list is rejected, because it would otherwise print one bullet per character;
4. placeholder text is left in: `Lorem ipsum`, `{{...}}`, `TODO`/`TBD`, `[Company Name]`, `XXX`, `اسم الشركة`, and similar;
5. a character is not in the bundled fonts (emoji, icons, decorative symbols), since it would print as an empty box.

Warnings never block the build unless you pass `--strict`. They cover missing contact details, weak phrases such as "responsible for" or "مسؤول عن", first-person summaries, very long bullets, missing dates, and `example.com` addresses.

## Minimal valid file

```json
{
  "name": "Full Name",
  "email": "name@mail.com",
  "phone": "+971 50 000 0000",
  "city": "Dubai",
  "country": "UAE",
  "summary": "Three to four lines that state role, years of experience, strongest areas and the value offered.",
  "strengths": ["Area: skill, skill, skill"],
  "experience": [
    {
      "company": "Company",
      "location": "City, Country",
      "title": "Job Title",
      "dates": "01/2022 – Present",
      "bullets": ["Action verb + what was done + measurable result the candidate confirmed."]
    }
  ],
  "education": [
    {"degree": "B.Sc. Subject", "university": "University", "date": "2021"}
  ]
}
```
