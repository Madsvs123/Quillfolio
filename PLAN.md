# Further local CLI work

Quillfolio stays a command-line tool for the resume file on this machine. The ideas below extend that file, the commands that edit it, and the pages rendered from it. They do not add accounts, a hosted service, or any collection of other people's resumes. Examples remain fictional.

## File shape

- Add an optional `publications` list to the same resume file, with title, venue, date, and URL, and teach the themes and the plain-text export to render it.
- Allow a resume to include one local fragment, such as `experience.yaml` beside the main file, and document that the fragment is read from disk only when a command runs.
- Keep a local bullet bank, a YAML file of highlight lines the operator writes, and add a command that copies one line into a role by id.

## Checks

- Warn when the same highlight text appears twice in the file, including across roles.
- Check highlights against a word list the operator supplies as a local text file, and print the unknown words without contacting a dictionary service.
- Extend `lint` with an optional line-length limit for plain-text export, aimed at pasting into a form the operator already has open.
- Add `stats --json` so a script on this machine can read the counts without scraping the text report.
- Note overlapping experience dates in `stats`, since overlapping roles are currently added together.

## Rendering

- Add `diff --html` that writes a single local HTML file of added, removed, and changed fields, using the same print stylesheet as the resume themes.
- Record a short contrast and heading-order note for each built-in theme in the repository, and fail a test if a theme drops its single `h1`.
- Add a command that writes the print-oriented HTML only, still self-contained, for the operator to open in a browser and print.

## Editing

- Add `--dry-run` to commands that rewrite the file (`reorder`, `sort`, `add-role`, `add-bullet`, `add-skill`, `merge`, `restore`) so they print the result and leave the file untouched.
- Add a `which` command that prints the resume path, the config file that was found, and the theme that would be used.

## Packaging

- Keep the license MIT.
- Keep the dependency set small. A PDF export, if one is added, should call a converter the operator already installed and should refuse to download one.
- Continue to ship fictional examples only, with `example.com` addresses, and keep `doctor` as the check that the install and one chosen file are readable offline.
