# Quillfolio

Quillfolio is a local command-line tool that turns a resume file you write into Markdown, HTML, and plain text. It is for the person maintaining their own CV on their own computer. The resume lives in a YAML or JSON file in a folder you choose. Quillfolio checks that file, can add a role or project, can keep the sections that match a target role, and can show the differences between two versions.

It does not collect other people's resumes, run accounts, or send your file anywhere. The preview command serves the rendered page only on `127.0.0.1`.

The samples in `examples/` are fiction. Marlowe Voss and Sable Quinn are invented names, and the only email addresses in those files are on `example.com`.

## Install

Quillfolio needs Python 3.10 or newer.

```text
py -3 -m pip install -e .
```

On a machine where the Python 3 command is `python`, use `python -m pip install -e .` in place of `py -3`.

The install registers a `quillfolio` console script. If that script is not on your `PATH`, run the module instead. The examples below use the module form so they work either way:

```text
py -3 -m quillfolio --help
```

Install the test runner with the same interpreter when you want to run the suite:

```text
py -3 -m pip install -r requirements.txt
py -3 -m pytest
```

## Resume file

A resume is a mapping with `meta`, `experience`, `projects`, `education`, and `skills`. `init` writes a starter you replace with your own history. `examples/sample-resume.yaml` is a fictional engineering resume, and `examples/sable-quinn.yaml` is a fictional writing resume. The same keys work in JSON when the file ends in `.json`.

Dates are `YYYY`, `YYYY-MM`, `YYYY-MM-DD`, or `present` for an end date. Quote phone numbers and month-precision dates so they stay text. Commands that rewrite the file, such as `add-role`, save clean YAML or JSON and do not keep comments.

## Commands

### init

Write a starter resume. The command refuses to replace an existing file unless you pass `--force`. If you pass a directory, it writes `resume.yaml` inside that directory.

```text
py -3 -m quillfolio init resume.yaml
py -3 -m quillfolio init resumes --force
```

### validate

Check required fields, dates, ids, email, and URLs. Warnings cover missing highlights and other soft gaps. The process exits `0` when there is no error. `--strict` also fails on warnings.

```text
py -3 -m quillfolio validate resume.yaml
py -3 -m quillfolio validate examples/sample-resume.yaml --strict
```

### lint

Flag missing dates and empty bullets. Experience and education need a start and an end (`present` is an end). Experience and projects need at least one highlight that is not blank. `validate` still allows a missing end as a warning. `lint` treats that gap as an error and exits `1`.

```text
py -3 -m quillfolio lint resume.yaml
```

### schema

Check the resume against the JSON Schema shipped in `quillfolio/resume.schema.json`. Dates must be quoted text (`YYYY`, `YYYY-MM`, or `YYYY-MM-DD`). `--show` prints the schema. This check is structural. `validate` still reports the editorial warnings.

```text
py -3 -m quillfolio schema resume.yaml
py -3 -m quillfolio schema --show
```

### add-role

Append one experience entry. Repeat `--highlight` and `--skill` for each bullet and skill. `--start` is required. `--end` may be a date or `present`.

```text
py -3 -m quillfolio add-role resume.yaml --company "Example Studio" --title "Engineer" --start 2024-01 --end present --location "City, Region" --highlight "Describe one result from your own work." --skill python
```

### add-project

Append one project. `--name` and at least one `--highlight` are required.

```text
py -3 -m quillfolio add-project resume.yaml --name "Example Project" --url https://example.com/project --description "A short description." --highlight "Say what you built." --skill python
```

### skills

Print skills grouped by category, in the order they appear in the file.

```text
py -3 -m quillfolio skills resume.yaml
```

### add-skill

Add one skill to a category. The category name is matched without regard to case, and the existing spelling is kept. A new category is created when the name is new. The same skill cannot be added twice to one category.

```text
py -3 -m quillfolio add-skill resume.yaml --group Languages --item Rust
```

### reorder

Change the order of top-level sections, or the order of entries inside `experience`, `projects`, or `education`. Named items move to the front in the order you give. Anything you do not name keeps its previous order after those. The command rewrites the file.

```text
py -3 -m quillfolio reorder resume.yaml --section skills --section experience
py -3 -m quillfolio reorder resume.yaml --entries experience --id paperfinch --id cedar-circuit
```

### tailor

Keep experience entries and projects whose title, skills, or highlights share words with a target role. Extra `--keyword` values count too. Matching skill groups stay, with matching skills listed first. Education stays as it is. The original file is unchanged unless you point `--out` at that same path.

```text
py -3 -m quillfolio tailor examples/sample-resume.yaml --role "Python observability" --out tailored.yaml
py -3 -m quillfolio tailor resume.yaml --role "platform services" --keyword python --max-roles 2 --out tailored.yaml
```

### keywords

Read a job description from a text file on this machine and report which of its words already appear in the resume. Matching is whole-word and ignores case. Words shorter than `--min-length` (default 4) and a small set of common filler words are skipped. Nothing is uploaded. `--fail-under` exits `1` when the coverage percent is below the number you pass.

```text
py -3 -m quillfolio keywords resume.yaml job.txt
py -3 -m quillfolio keywords resume.yaml job.txt --min-length 3 --fail-under 40
```

### cover-letter

Draft a plain-text letter from the same resume file. The command uses your name, contact lines, summary, and up to three experience highlights. It does not look up the company and it does not send the file. The resume itself is left unchanged.

```text
py -3 -m quillfolio cover-letter resume.yaml --role "Systems engineer" --company "Northwind Archive" --out letter.txt
```

### render-md

Render Markdown to stdout, or to a file with `--out`.

```text
py -3 -m quillfolio render-md examples/sample-resume.yaml --out resume.md
```

### render-txt

Render plain text with no Markdown marks. `--width` sets the line length from 40 to 120. The default is 72. Long words stay on one line.

```text
py -3 -m quillfolio render-txt examples/sample-resume.yaml --out resume.txt
py -3 -m quillfolio render-txt resume.yaml --width 60
```

### render-html

Render one self-contained HTML file. The built-in themes are `atelier` (a serif sheet with a sidebar), `signal` (a compact sans-serif page), and `ledger` (a monospace page ruled like a bound book). They use fonts already on the computer. They do not load remote fonts, scripts, or images. Each page embeds `quillfolio/print.css`, which sets letter-size paper, drops screen color and shadow, keeps roles from splitting across pages, and prints the address after a web link.

```text
py -3 -m quillfolio render-html examples/sample-resume.yaml --theme atelier --out resume.html
py -3 -m quillfolio render-html examples/sample-resume.yaml --theme signal --out resume-signal.html
py -3 -m quillfolio render-html examples/sample-resume.yaml --theme ledger --out resume-ledger.html
```

### diff

Compare two resume files and print added, removed, and changed fields. Exit code `0` means the files match. Exit code `1` means they differ.

```text
py -3 -m quillfolio diff resume.yaml tailored.yaml
```

### merge

Combine two resume files you already have. The first file keeps its meta values and any entry whose id is already present. New roles, projects, and education entries from the second file are appended. Skill categories with the same name are united, and repeated skills are stored once. Notes about skipped ids are printed to standard error. The command does not contact a service.

```text
py -3 -m quillfolio merge resume.yaml other.yaml --out merged.yaml
```

### stats

Count words, roles, projects, schools, skills, and bullets. `years` is the sum of each experience entry from its start to its end, in years with one decimal place. A missing end, or `present`, runs through today. Overlapping roles are both counted.

```text
py -3 -m quillfolio stats resume.yaml
```

### snapshot, snapshots, and restore

`snapshot` copies the resume bytes into `.quillfolio-snapshots/` next to the file. The label uses letters, numbers, hyphens, or underscores. `snapshots` lists what has been saved. `restore` writes a saved copy back over the resume. Pass `--force` to replace a label that already exists. These commands do not upload the file.

```text
py -3 -m quillfolio snapshot resume.yaml --label before-edit
py -3 -m quillfolio snapshots resume.yaml
py -3 -m quillfolio restore resume.yaml --label before-edit
```

### export

Write `resume.md`, `resume.json`, `resume.yaml`, and one HTML file for each built-in theme (`resume.atelier.html`, `resume.signal.html`, and `resume.ledger.html`). Use `--out` for a directory, `--zip` for an archive, or both.

```text
py -3 -m quillfolio export examples/sample-resume.yaml --out dist
py -3 -m quillfolio export resume.yaml --zip resume-bundle.zip
```

### preview

Render the file you name and serve that HTML on `127.0.0.1`. The server reads the file again on each refresh, answers only `/` and `/index.html`, and does not upload the resume. Stop it with Ctrl+C.

```text
py -3 -m quillfolio preview examples/sample-resume.yaml --theme atelier --port 8765
```

Open `http://127.0.0.1:8765/` in a browser on the same machine.

## Themes

| Theme | Layout |
| --- | --- |
| `atelier` | Warm paper page, serif type, experience in the main column, contact and skills in a sidebar |
| `signal` | Cool compact page, sans-serif type, dated rows, skill chips, and a dark-mode stylesheet for the operating system setting |
| `ledger` | Warm ruled page, monospace type, centered name, and a single column separated by horizontal rules |

## Tests

```text
py -3 -m pytest
```

The suite covers validation, tailoring, Markdown rendering, and diffs, and it also exercises HTML themes, export, and the loopback preview.

## License

MIT License. Copyright (c) 2026 Madsvs123.
