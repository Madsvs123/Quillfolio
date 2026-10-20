"""Render a resume as a self-contained HTML document."""

from __future__ import annotations

import html

from quillfolio.errors import ResumeError
from quillfolio.textutil import as_str, is_email, safe_href, string_list

THEMES = ("atelier", "signal", "ledger")

_ATELIER_CSS = """
*, *::before, *::after { box-sizing: border-box; }
html { font-size: 16px; }
body.theme-atelier {
  margin: 0;
  background: #e7dcc8;
  color: #221c16;
  font-family: Georgia, "Iowan Old Style", Palatino, "Palatino Linotype", "Times New Roman", serif;
  line-height: 1.45;
}
.sheet {
  max-width: 920px;
  margin: 2rem auto;
  background: #fbf7f0;
  padding: 2.5rem 2.75rem 2rem;
  border-top: 10px solid #8c3d2a;
  box-shadow: 0 18px 40px rgba(48, 32, 18, 0.12);
}
.kicker {
  margin: 0 0 0.35rem;
  color: #8c3d2a;
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
}
h1 {
  margin: 0;
  font-size: clamp(2.4rem, 5vw, 3.4rem);
  font-weight: 500;
  letter-spacing: -0.03em;
  line-height: 1.05;
}
.headline { margin: 0.4rem 0 0; font-style: italic; color: #5c5146; font-size: 1.15rem; }
.tailored {
  display: inline-block;
  margin: 0.9rem 0 0;
  padding: 0.15rem 0.55rem;
  border: 1px solid #8c3d2a;
  color: #8c3d2a;
  font-size: 0.82rem;
  letter-spacing: 0.04em;
}
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 230px;
  gap: 2.4rem;
  margin-top: 1.8rem;
}
aside {
  background: #f3ece1;
  padding: 1rem 1rem 1.2rem;
}
h2 {
  margin: 0 0 0.8rem;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  border-bottom: 1px solid #d9cbb8;
  padding-bottom: 0.35rem;
}
h3 { margin: 0; font-size: 1.12rem; font-weight: 600; }
.where, .when, .tech, .detail, dd, .group-name { color: #5c5146; }
.where { margin: 0.15rem 0 0; }
.when, .tech, .detail { margin: 0.2rem 0 0; font-size: 0.92rem; }
.role, .project, .edu { margin: 0 0 1.15rem; }
.role ul, .project ul { margin: 0.45rem 0 0; padding-left: 1.1rem; }
li { margin: 0.2rem 0; }
p { overflow-wrap: anywhere; }
a { color: #8c3d2a; }
dl { margin: 0; }
dt {
  margin-top: 0.7rem;
  font-size: 0.68rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #8c3d2a;
}
dd { margin: 0.1rem 0 0; }
.skill-block { margin: 0 0 0.85rem; }
.group-name { margin: 0; font-weight: 600; color: #221c16; }
.colophon {
  margin: 1.5rem 0 0;
  color: #7a6d60;
  font-size: 0.75rem;
}
@media (max-width: 720px) {
  .sheet { margin: 0; padding: 1.5rem 1.1rem 1.2rem; }
  .layout { grid-template-columns: 1fr; gap: 1.2rem; }
}
@media print {
  body.theme-atelier { background: #fff; }
  .sheet { box-shadow: none; margin: 0; max-width: none; }
  a { color: inherit; text-decoration: none; }
  .role, .project, .edu { break-inside: avoid; }
}
@page { margin: 0.6in; }
"""

_SIGNAL_CSS = """
*, *::before, *::after { box-sizing: border-box; }
html { font-size: 16px; }
body.theme-signal {
  margin: 0;
  background: #d9e2ea;
  color: #14202b;
  font-family: "Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif;
  line-height: 1.4;
}
.sheet {
  max-width: 800px;
  margin: 1.5rem auto;
  background: #f7f9fb;
  padding: 1.6rem 1.7rem 1.3rem;
  border-left: 8px solid #1f4e79;
}
.bar {
  display: flex;
  justify-content: space-between;
  gap: 1.5rem;
  align-items: flex-end;
  border-bottom: 2px solid #14202b;
  padding-bottom: 0.8rem;
}
h1 {
  margin: 0;
  font-size: clamp(1.8rem, 4vw, 2.4rem);
  letter-spacing: -0.03em;
  line-height: 1;
}
.headline { margin: 0.35rem 0 0; color: #4c5b6a; }
.contact-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 0.9rem;
  list-style: none;
  margin: 0;
  padding: 0;
  justify-content: flex-end;
  max-width: 320px;
  font-size: 0.84rem;
}
.contact-row span {
  display: block;
  color: #1f4e79;
  font-family: Consolas, "Courier New", monospace;
  font-size: 0.68rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.lead { font-size: 1.02rem; margin: 1rem 0 0.2rem; }
.tailored {
  margin: 0.8rem 0 0;
  color: #1f4e79;
  font-family: Consolas, "Courier New", monospace;
  font-size: 0.82rem;
}
section { margin-top: 1.15rem; }
h2 {
  margin: 0 0 0.55rem;
  font-size: 0.95rem;
  display: flex;
  gap: 0.55rem;
  align-items: baseline;
}
.idx {
  font-family: Consolas, "Courier New", monospace;
  color: #1f4e79;
  font-size: 0.78rem;
}
.row {
  display: grid;
  grid-template-columns: 8.2rem minmax(0, 1fr);
  gap: 0.8rem;
  margin: 0 0 0.85rem;
}
.dates {
  margin: 0.15rem 0 0;
  font-family: Consolas, "Courier New", monospace;
  font-size: 0.78rem;
  color: #1f4e79;
}
h3 { margin: 0; font-size: 1rem; }
.at { color: #4c5b6a; font-weight: 400; }
ul { margin: 0.3rem 0 0; padding-left: 1.05rem; }
li { margin: 0.15rem 0; }
.desc { margin: 0.25rem 0; color: #243140; }
.chip {
  display: inline-block;
  margin: 0.15rem 0.3rem 0.15rem 0;
  padding: 0.08rem 0.45rem;
  border: 1px solid #c5d2de;
  border-radius: 999px;
  font-size: 0.82rem;
}
.group-label { margin-right: 0.35rem; }
.edu h3 { font-size: 0.98rem; }
.when { margin: 0.15rem 0; color: #4c5b6a; font-size: 0.85rem; }
.colophon {
  margin: 1.2rem 0 0;
  color: #607180;
  font-size: 0.75rem;
  font-family: Consolas, "Courier New", monospace;
}
a { color: #1f4e79; }
p, li, h1, h3 { overflow-wrap: anywhere; }
@media (max-width: 720px) {
  .sheet { margin: 0; }
  .bar, .row { display: block; }
  .contact-row { justify-content: flex-start; max-width: none; margin-top: 0.8rem; }
}
@media (prefers-color-scheme: dark) {
  body.theme-signal { background: #0f141a; color: #e7eef5; }
  .sheet { background: #18222c; border-left-color: #8fb7de; }
  .bar { border-bottom-color: #d5e4f2; }
  .headline, .at, .when, .colophon { color: #b7c6d4; }
  .contact-row span, .idx, .dates, a, .tailored { color: #8fb7de; }
  .chip { border-color: #3d5366; }
}
@media print {
  body.theme-signal { background: #fff; color: #000; }
  .sheet { margin: 0; border-left: 4px solid #000; max-width: none; }
  a { color: inherit; text-decoration: none; }
  .row, .edu, .role { break-inside: avoid; }
}
@page { margin: 0.55in; }
"""

_LEDGER_CSS = """
*, *::before, *::after { box-sizing: border-box; }
html { font-size: 16px; }
body.theme-ledger {
  margin: 0;
  background: #e4d7b8;
  color: #1c1a16;
  font-family: Consolas, "Courier New", Courier, monospace;
  line-height: 1.45;
}
.sheet {
  max-width: 760px;
  margin: 1.5rem auto;
  background: #f7f1e2;
  padding: 1.6rem 1.7rem 1.4rem;
  border: 3px double #3a3428;
}
.mast { text-align: center; margin-bottom: 0.4rem; }
.folio {
  margin: 0;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  font-size: 0.68rem;
  color: #6b5b3e;
}
h1 {
  margin: 0.35rem 0 0;
  font-size: clamp(1.6rem, 4vw, 2.15rem);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.headline { margin: 0.45rem 0 0; color: #4a4338; }
.rule {
  margin: 0.85rem 0;
  border: 0;
  border-top: 1px solid #3a3428;
}
.tailored { margin: 0.4rem 0 0; color: #6b5b3e; }
h2 {
  margin: 0 0 0.55rem;
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
h3 { margin: 0; font-size: 1rem; font-weight: 700; }
.entry { margin: 0 0 0.9rem; }
.meta, .detail, .group-name { color: #4a4338; }
.meta, .detail { margin: 0.15rem 0 0; }
ul { margin: 0.3rem 0 0; padding-left: 1.1rem; }
li { margin: 0.12rem 0; }
.contact { margin: 0; padding: 0; list-style: none; }
.contact li { margin: 0.15rem 0; }
.skill-line { margin: 0.2rem 0; }
a { color: #1c1a16; }
p, li, h1, h3 { overflow-wrap: anywhere; }
.colophon {
  margin: 0.4rem 0 0;
  color: #6b5b3e;
  font-size: 0.75rem;
  text-align: center;
}
@media print {
  body.theme-ledger { background: #fff; }
  .sheet { margin: 0; max-width: none; border-color: #000; }
  a { color: inherit; text-decoration: none; }
  .entry { break-inside: avoid; }
}
@page { margin: 0.6in; }
"""


def theme_names() -> list[str]:
    return list(THEMES)


def normalize_theme(theme: str) -> str:
    if not isinstance(theme, str):
        raise ResumeError("theme must be text")
    key = theme.strip().lower()
    if key not in THEMES:
        known = ", ".join(THEMES)
        raise ResumeError(f"unknown theme {theme!r}. Choose one of: {known}")
    return key


def render_html(resume: dict, theme: str = "atelier") -> str:
    """Render the resume with a built-in theme. The document loads no remote assets."""
    if not isinstance(resume, dict):
        raise ResumeError("resume must be a mapping")
    chosen = normalize_theme(theme)
    if chosen == "atelier":
        return _render_atelier(resume)
    if chosen == "signal":
        return _render_signal(resume)
    return _render_ledger(resume)


def _render_atelier(resume: dict) -> str:
    meta = _meta(resume)
    name = as_str(meta.get("name")) or "Resume"
    body = [
        '<article class="sheet">',
        "  <header>",
        '    <p class="kicker">Resume</p>',
        "    <h1>" + _esc(name) + "</h1>",
        _optional_paragraph("headline", as_str(meta.get("headline"))),
        _tailored(meta),
        "  </header>",
        '  <div class="layout">',
        "    <main>",
        _summary_section(meta),
        _atelier_experience(resume.get("experience")),
        _atelier_projects(resume.get("projects")),
        "    </main>",
        "    <aside>",
        _contact_section(meta),
        _atelier_skills(resume.get("skills")),
        _atelier_education(resume.get("education")),
        "    </aside>",
        "  </div>",
        '  <p class="colophon">Rendered locally with Quillfolio.</p>',
        "</article>",
    ]
    return _shell("theme-atelier", _ATELIER_CSS, f"{name} - Resume", "\n".join(line for line in body if line))


def _render_signal(resume: dict) -> str:
    meta = _meta(resume)
    name = as_str(meta.get("name")) or "Resume"
    numbers = _counter()
    chunks = [
        '<article class="sheet">',
        '  <header class="bar">',
        "    <div>",
        "      <h1>" + _esc(name) + "</h1>",
        _optional_paragraph("headline", as_str(meta.get("headline"))),
        "    </div>",
        _signal_contact(meta),
        "  </header>",
        _tailored(meta),
        _lead(meta),
        _signal_experience(resume.get("experience"), numbers),
        _signal_projects(resume.get("projects"), numbers),
        _signal_education(resume.get("education"), numbers),
        _signal_skills(resume.get("skills"), numbers),
        '  <p class="colophon">Rendered locally with Quillfolio.</p>',
        "</article>",
    ]
    return _shell("theme-signal", _SIGNAL_CSS, f"{name} - Resume", "\n".join(line for line in chunks if line))


def _render_ledger(resume: dict) -> str:
    meta = _meta(resume)
    name = as_str(meta.get("name")) or "Resume"
    chunks = [
        '<article class="sheet">',
        '  <header class="mast">',
        '    <p class="folio">Resume</p>',
        "    <h1>" + _esc(name) + "</h1>",
        _optional_paragraph("headline", as_str(meta.get("headline"))),
        _tailored(meta),
        "  </header>",
        '  <hr class="rule">',
        _ledger_contact(meta),
        _ledger_summary(meta),
        _ledger_experience(resume.get("experience")),
        _ledger_projects(resume.get("projects")),
        _ledger_education(resume.get("education")),
        _ledger_skills(resume.get("skills")),
        '  <hr class="rule">',
        '  <p class="colophon">Rendered locally with Quillfolio.</p>',
        "</article>",
    ]
    return _shell("theme-ledger", _LEDGER_CSS, f"{name} - Resume", "\n".join(line for line in chunks if line))


def _ledger_contact(meta: dict) -> str:
    rows = _contact_rows(meta)
    if not rows:
        return ""
    items = [f"      <li>{content}</li>" for _label, content in rows]
    return "\n".join(
        [
            '  <section id="contact">',
            *_ledger_heading("Contact"),
            '    <ul class="contact">',
            *items,
            "    </ul>",
            "  </section>",
        ]
    )


def _ledger_summary(meta: dict) -> str:
    summary = as_str(meta.get("summary"))
    if not summary:
        return ""
    return "\n".join(
        [
            '  <section id="summary">',
            *_ledger_heading("Summary"),
            f"    <p>{_esc(summary)}</p>",
            "  </section>",
        ]
    )


def _ledger_heading(title: str) -> list[str]:
    return ['    <hr class="rule">', f"    <h2>{_esc(title)}</h2>"]


def _ledger_experience(entries: object) -> str:
    roles = _mappings(entries)
    if not roles:
        return ""
    blocks = ['  <section id="experience">', *_ledger_heading("Experience")]
    for role in roles:
        title = as_str(role.get("title")) or "Role"
        company = as_str(role.get("company"))
        heading = _esc(title)
        if company:
            heading += f" / {_esc(company)}"
        blocks.append('    <article class="entry">')
        blocks.append(f"      <h3>{heading}</h3>")
        when = _when_where(role)
        if when:
            blocks.append(f'      <p class="meta">{when}</p>')
        blocks.append(_bullets(string_list(role.get("highlights"))))
        skills = string_list(role.get("skills"))
        if skills:
            blocks.append(f'      <p class="detail">{_esc(", ".join(skills))}</p>')
        blocks.append("    </article>")
    blocks.append("  </section>")
    return "\n".join(line for line in blocks if line)


def _ledger_projects(entries: object) -> str:
    projects = _mappings(entries)
    if not projects:
        return ""
    blocks = ['  <section id="projects">', *_ledger_heading("Projects")]
    for project in projects:
        name = as_str(project.get("name")) or "Project"
        link = _linkify(project.get("url"), name)
        blocks.append('    <article class="entry">')
        blocks.append(f"      <h3>{link or _esc(name)}</h3>")
        description = as_str(project.get("description"))
        if description:
            blocks.append(f'      <p class="detail">{_esc(description)}</p>')
        blocks.append(_bullets(string_list(project.get("highlights"))))
        blocks.append("    </article>")
    blocks.append("  </section>")
    return "\n".join(line for line in blocks if line)


def _ledger_education(entries: object) -> str:
    schools = _mappings(entries)
    if not schools:
        return ""
    blocks = ['  <section id="education">', *_ledger_heading("Education")]
    for school in schools:
        degree = as_str(school.get("degree")) or "Study"
        name = as_str(school.get("school"))
        blocks.append('    <article class="entry">')
        blocks.append(f"      <h3>{_esc(degree)}</h3>")
        if name:
            blocks.append(f'      <p class="meta">{_esc(name)}</p>')
        span = _date_span(school.get("start"), school.get("end"))
        if span:
            blocks.append(f'      <p class="detail">{span}</p>')
        details = as_str(school.get("details"))
        if details:
            blocks.append(f"      <p>{_esc(details)}</p>")
        blocks.append("    </article>")
    blocks.append("  </section>")
    return "\n".join(blocks)


def _ledger_skills(entries: object) -> str:
    groups = _mappings(entries)
    visible = [(group, string_list(group.get("items"))) for group in groups]
    visible = [(group, items) for group, items in visible if items]
    if not visible:
        return ""
    blocks = ['  <section id="skills">', *_ledger_heading("Skills")]
    for group, items in visible:
        label = as_str(group.get("group")) or "Skills"
        blocks.append(
            f'    <p class="skill-line"><span class="group-name">{_esc(label)}:</span> {_esc(", ".join(items))}</p>'
        )
    blocks.append("  </section>")
    return "\n".join(blocks)


def _shell(theme_class: str, css: str, title: str, body: str) -> str:
    return "\n".join(
        [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1">',
            '  <meta name="robots" content="noindex">',
            "  <title>" + _esc(title) + "</title>",
            "  <style>",
            css.strip(),
            "  </style>",
            "</head>",
            f'<body class="{theme_class}">',
            body,
            "</body>",
            "</html>",
            "",
        ]
    )


def _meta(resume: dict) -> dict:
    meta = resume.get("meta")
    return meta if isinstance(meta, dict) else {}


def _mappings(entries: object) -> list[dict]:
    if not isinstance(entries, list):
        return []
    return [item for item in entries if isinstance(item, dict)]


def _esc(value: object) -> str:
    return html.escape(as_str(value), quote=True)


def _optional_paragraph(class_name: str, text: str) -> str:
    if not text:
        return ""
    return f'    <p class="{class_name}">{_esc(text)}</p>'


def _tailored(meta: dict) -> str:
    text = as_str(meta.get("tailored_for"))
    if not text:
        return ""
    return f'    <p class="tailored">Tailored for {_esc(text)}</p>'


def _lead(meta: dict) -> str:
    summary = as_str(meta.get("summary"))
    if not summary:
        return ""
    return f'  <p class="lead">{_esc(summary)}</p>'


def _summary_section(meta: dict) -> str:
    summary = as_str(meta.get("summary"))
    if not summary:
        return ""
    return "\n".join(
        [
            '      <section id="summary">',
            "        <h2>Summary</h2>",
            f"        <p>{_esc(summary)}</p>",
            "      </section>",
        ]
    )


def _contact_section(meta: dict) -> str:
    rows = _contact_rows(meta)
    if not rows:
        return ""
    body = ['      <section id="contact">', "        <h2>Contact</h2>", "        <dl>"]
    for label, content in rows:
        body.append(f"          <dt>{_esc(label)}</dt>")
        body.append(f"          <dd>{content}</dd>")
    body.append("        </dl>")
    body.append("      </section>")
    return "\n".join(body)


def _signal_contact(meta: dict) -> str:
    rows = _contact_rows(meta)
    if not rows:
        return ""
    items = [f'        <li><span>{_esc(label)}</span>{content}</li>' for label, content in rows]
    return "\n".join(['      <ul class="contact-row">', *items, "      </ul>"])


def _contact_rows(meta: dict) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    email = as_str(meta.get("email"))
    if email:
        rows.append(("Email", _email_html(email)))
    phone = as_str(meta.get("phone"))
    if phone:
        rows.append(("Phone", _esc(phone)))
    location = as_str(meta.get("location"))
    if location:
        rows.append(("Location", _esc(location)))
    website = as_str(meta.get("website"))
    linked = _linkify(website)
    if linked:
        rows.append(("Web", linked))
    return rows


def _email_html(email: str) -> str:
    escaped = _esc(email)
    if is_email(email) and safe_href(f"mailto:{email}"):
        return f'<a href="mailto:{escaped}">{escaped}</a>'
    return escaped


def _linkify(url: object, label: str | None = None) -> str:
    href = safe_href(url)
    if href is None:
        return ""
    text = _esc(label if label else as_str(url))
    return f'<a href="{_esc(href)}">{text}</a>'


def _bullets(items: list[str]) -> str:
    if not items:
        return ""
    lis = "\n".join(f"          <li>{_esc(item)}</li>" for item in items)
    return f"        <ul>\n{lis}\n        </ul>"


def _date_span(start: object, end: object) -> str:
    left = as_str(start)
    right = as_str(end)
    if left and right:
        return f"{_esc(left)} &ndash; {_esc(right)}"
    return _esc(left or right)


def _when_where(entry: dict) -> str:
    span = _date_span(entry.get("start"), entry.get("end"))
    location = as_str(entry.get("location"))
    if span and location:
        return f"{span} &middot; {_esc(location)}"
    return span or _esc(location)


def _atelier_experience(entries: object) -> str:
    roles = _mappings(entries)
    if not roles:
        return ""
    blocks = ['      <section id="experience">', "        <h2>Experience</h2>"]
    for role in roles:
        title = as_str(role.get("title")) or "Role"
        company = as_str(role.get("company"))
        blocks.append('        <article class="role">')
        blocks.append(f"          <h3>{_esc(title)}</h3>")
        if company:
            blocks.append(f'          <p class="where">{_esc(company)}</p>')
        when = _when_where(role)
        if when:
            blocks.append(f'          <p class="when">{when}</p>')
        blocks.append(_bullets(string_list(role.get("highlights"))))
        skills = string_list(role.get("skills"))
        if skills:
            blocks.append(f'          <p class="tech">{_esc(", ".join(skills))}</p>')
        blocks.append("        </article>")
    blocks.append("      </section>")
    return "\n".join(line for line in blocks if line)


def _atelier_projects(entries: object) -> str:
    projects = _mappings(entries)
    if not projects:
        return ""
    blocks = ['      <section id="projects">', "        <h2>Projects</h2>"]
    for project in projects:
        name = as_str(project.get("name")) or "Project"
        link = _linkify(project.get("url"), name)
        heading = link or _esc(name)
        blocks.append('        <article class="project">')
        blocks.append(f"          <h3>{heading}</h3>")
        description = as_str(project.get("description"))
        if description:
            blocks.append(f'          <p class="detail">{_esc(description)}</p>')
        blocks.append(_bullets(string_list(project.get("highlights"))))
        blocks.append("        </article>")
    blocks.append("      </section>")
    return "\n".join(line for line in blocks if line)


def _atelier_skills(entries: object) -> str:
    groups = _mappings(entries)
    visible = [(group, string_list(group.get("items"))) for group in groups]
    visible = [(group, items) for group, items in visible if items]
    if not visible:
        return ""
    blocks = ['      <section id="skills">', "        <h2>Skills</h2>"]
    for group, items in visible:
        label = as_str(group.get("group")) or "Skills"
        blocks.append('        <div class="skill-block">')
        blocks.append(f'          <p class="group-name">{_esc(label)}</p>')
        blocks.append(f"          <p>{_esc(', '.join(items))}</p>")
        blocks.append("        </div>")
    blocks.append("      </section>")
    return "\n".join(blocks)


def _atelier_education(entries: object) -> str:
    schools = _mappings(entries)
    if not schools:
        return ""
    blocks = ['      <section id="education">', "        <h2>Education</h2>"]
    for school in schools:
        degree = as_str(school.get("degree")) or "Study"
        name = as_str(school.get("school"))
        blocks.append('        <article class="edu">')
        blocks.append(f"          <h3>{_esc(degree)}</h3>")
        if name:
            blocks.append(f'          <p class="where">{_esc(name)}</p>')
        span = _date_span(school.get("start"), school.get("end"))
        if span:
            blocks.append(f'          <p class="when">{span}</p>')
        details = as_str(school.get("details"))
        if details:
            blocks.append(f'          <p class="detail">{_esc(details)}</p>')
        blocks.append("        </article>")
    blocks.append("      </section>")
    return "\n".join(blocks)


def _counter() -> dict[str, int]:
    return {"n": 0}


def _next_heading(title: str, numbers: dict[str, int]) -> str:
    numbers["n"] += 1
    return f'    <h2><span class="idx">{numbers["n"]:02d}</span> {_esc(title)}</h2>'


def _signal_experience(entries: object, numbers: dict[str, int]) -> str:
    roles = _mappings(entries)
    if not roles:
        return ""
    blocks = ["  <section>", _next_heading("Experience", numbers)]
    for role in roles:
        title = as_str(role.get("title")) or "Role"
        company = as_str(role.get("company"))
        heading = _esc(title)
        if company:
            heading += f' <span class="at">at {_esc(company)}</span>'
        blocks.append('    <article class="row role">')
        blocks.append(f'      <p class="dates">{_date_span(role.get("start"), role.get("end"))}</p>')
        blocks.append("      <div>")
        blocks.append(f"        <h3>{heading}</h3>")
        location = as_str(role.get("location"))
        if location:
            blocks.append(f'        <p class="when">{_esc(location)}</p>')
        blocks.append(_bullets(string_list(role.get("highlights"))))
        blocks.append("      </div>")
        blocks.append("    </article>")
    blocks.append("  </section>")
    return "\n".join(line for line in blocks if line)


def _signal_projects(entries: object, numbers: dict[str, int]) -> str:
    projects = _mappings(entries)
    if not projects:
        return ""
    blocks = ["  <section>", _next_heading("Projects", numbers)]
    for project in projects:
        name = as_str(project.get("name")) or "Project"
        link = _linkify(project.get("url"), name)
        blocks.append('    <article class="role">')
        blocks.append(f"      <h3>{link or _esc(name)}</h3>")
        description = as_str(project.get("description"))
        if description:
            blocks.append(f'      <p class="desc">{_esc(description)}</p>')
        blocks.append(_bullets(string_list(project.get("highlights"))))
        skills = string_list(project.get("skills"))
        if skills:
            chips = "".join(f'<span class="chip">{_esc(skill)}</span>' for skill in skills)
            blocks.append(f"      <p>{chips}</p>")
        blocks.append("    </article>")
    blocks.append("  </section>")
    return "\n".join(line for line in blocks if line)


def _signal_education(entries: object, numbers: dict[str, int]) -> str:
    schools = _mappings(entries)
    if not schools:
        return ""
    blocks = ["  <section>", _next_heading("Education", numbers)]
    for school in schools:
        degree = as_str(school.get("degree")) or "Study"
        name = as_str(school.get("school"))
        blocks.append('    <article class="edu">')
        blocks.append(f"      <h3>{_esc(degree)}</h3>")
        if name:
            blocks.append(f"      <p>{_esc(name)}</p>")
        span = _date_span(school.get("start"), school.get("end"))
        if span:
            blocks.append(f'      <p class="when">{span}</p>')
        details = as_str(school.get("details"))
        if details:
            blocks.append(f"      <p>{_esc(details)}</p>")
        blocks.append("    </article>")
    blocks.append("  </section>")
    return "\n".join(blocks)


def _signal_skills(entries: object, numbers: dict[str, int]) -> str:
    groups = _mappings(entries)
    visible = [(group, string_list(group.get("items"))) for group in groups]
    visible = [(group, items) for group, items in visible if items]
    if not visible:
        return ""
    blocks = ["  <section>", _next_heading("Skills", numbers)]
    for group, items in visible:
        label = as_str(group.get("group")) or "Skills"
        chips = "".join(f'<span class="chip">{_esc(item)}</span>' for item in items)
        blocks.append(f'    <p><strong class="group-label">{_esc(label)}</strong>{chips}</p>')
    blocks.append("  </section>")
    return "\n".join(blocks)
