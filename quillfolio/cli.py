"""Command-line interface for Quillfolio."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from quillfolio import __version__
from quillfolio.bundle import export_directory, export_zip
from quillfolio.cover import render_cover_letter
from quillfolio.diffing import diff_resumes, format_diff
from quillfolio.errors import Issue, ResumeError
from quillfolio.html_render import normalize_theme, render_html, theme_names
from quillfolio.keywords import format_coverage, keyword_coverage, load_job_text
from quillfolio.merge import merge_resumes
from quillfolio.markdown_render import render_markdown
from quillfolio.mutate import add_project, add_role, write_starter
from quillfolio.plain_render import render_plain
from quillfolio.preview import make_preview_server
from quillfolio.reorder import reorder_entries, reorder_sections
from quillfolio.resume_io import dump_text, load_resume, save_resume
from quillfolio.schema_check import schema_errors, schema_text
from quillfolio.skills import add_skill, format_skills
from quillfolio.snapshots import format_snapshots, list_snapshots, restore_snapshot, take_snapshot
from quillfolio.stats import format_stats, resume_stats
from quillfolio.tailor import tailor_resume
from quillfolio.validate import validate_resume

_DESCRIPTION = """\
Build, tailor, and render your own resume from a local YAML or JSON file.

Quillfolio is a command-line tool for the person at the keyboard. It reads a
resume file you edit, checks it, and writes Markdown or HTML on this machine.
It does not create accounts or send the file to a service.
"""

_EPILOG = """\
examples:
  quillfolio init resume.yaml
  quillfolio validate examples/sample-resume.yaml
  quillfolio render-html examples/sample-resume.yaml --theme signal --out resume.html
  quillfolio preview examples/sample-resume.yaml
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quillfolio",
        description=_DESCRIPTION,
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"quillfolio {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="write a starter resume file")
    init.add_argument("path", nargs="?", default="resume.yaml", help="file or directory (default: resume.yaml)")
    init.add_argument("--force", action="store_true", help="replace an existing file")
    init.set_defaults(func=cmd_init)

    validate = commands.add_parser("validate", help="check a resume file")
    _add_resume_arg(validate)
    validate.add_argument("--strict", action="store_true", help="treat warnings as errors")
    validate.set_defaults(func=cmd_validate)

    schema_cmd = commands.add_parser("schema", help="check a resume against the bundled JSON Schema")
    schema_cmd.add_argument("path", nargs="?", type=Path, help="resume file (.yaml, .yml, or .json)")
    schema_cmd.add_argument("--show", action="store_true", help="print the JSON Schema")
    schema_cmd.set_defaults(func=cmd_schema)

    role = commands.add_parser("add-role", help="append an experience entry")
    _add_resume_arg(role)
    role.add_argument("--company", required=True)
    role.add_argument("--title", required=True)
    role.add_argument("--start", required=True, help="YYYY, YYYY-MM, or YYYY-MM-DD")
    role.add_argument("--end", help="date or present")
    role.add_argument("--location")
    role.add_argument("--id", dest="role_id")
    role.add_argument("--highlight", action="append", dest="highlights", help="repeat for each bullet")
    role.add_argument("--skill", action="append", dest="skills", help="repeat for each skill")
    role.set_defaults(func=cmd_add_role)

    project = commands.add_parser("add-project", help="append a project entry")
    _add_resume_arg(project)
    project.add_argument("--name", required=True)
    project.add_argument("--url")
    project.add_argument("--description")
    project.add_argument("--id", dest="project_id")
    project.add_argument("--highlight", action="append", dest="highlights")
    project.add_argument("--skill", action="append", dest="skills")
    project.set_defaults(func=cmd_add_project)

    reorder = commands.add_parser("reorder", help="reorder sections or entries")
    _add_resume_arg(reorder)
    reorder.add_argument(
        "--section",
        action="append",
        dest="sections",
        help="section to place next; repeat in the order you want",
    )
    reorder.add_argument(
        "--entries",
        help="reorder entries inside experience, projects, or education",
    )
    reorder.add_argument(
        "--id",
        action="append",
        dest="ids",
        help="entry id to place next; repeat in the order you want",
    )
    reorder.set_defaults(func=cmd_reorder)

    skills_cmd = commands.add_parser("skills", help="list skills grouped by category")
    _add_resume_arg(skills_cmd)
    skills_cmd.set_defaults(func=cmd_skills)

    add_skill_cmd = commands.add_parser("add-skill", help="add a skill to a category")
    _add_resume_arg(add_skill_cmd)
    add_skill_cmd.add_argument("--group", required=True, help="category name, for example Languages")
    add_skill_cmd.add_argument("--item", required=True, help="skill to add to that category")
    add_skill_cmd.set_defaults(func=cmd_add_skill)

    tailor = commands.add_parser("tailor", help="keep sections that match a target role")
    _add_resume_arg(tailor)
    tailor.add_argument("--role", required=True, help="target role, for example 'Python systems'")
    tailor.add_argument("--keyword", action="append", dest="keywords", help="extra word that should count as a match")
    tailor.add_argument("--out", type=Path, help="write the tailored resume here; default is stdout")
    tailor.add_argument("--max-roles", type=int)
    tailor.add_argument("--max-projects", type=int)
    tailor.set_defaults(func=cmd_tailor)

    keywords = commands.add_parser("keywords", help="compare the resume with a local job description")
    _add_resume_arg(keywords)
    keywords.add_argument("job", type=Path, help="UTF-8 job-description text file on this machine")
    keywords.add_argument("--min-length", type=int, default=4, help="shortest keyword to count (default: 4)")
    keywords.add_argument(
        "--fail-under",
        type=int,
        help="exit 1 when the coverage percent is below this value",
    )
    keywords.set_defaults(func=cmd_keywords)

    cover = commands.add_parser("cover-letter", help="draft a letter from this resume file")
    _add_resume_arg(cover)
    cover.add_argument("--role", required=True, help="role you are writing about")
    cover.add_argument("--company", required=True, help="name to address on the letter")
    cover.add_argument("--out", type=Path, help="write the letter here; default is stdout")
    cover.set_defaults(func=cmd_cover_letter)

    render_md = commands.add_parser("render-md", help="render Markdown")
    _add_resume_arg(render_md)
    render_md.add_argument("--out", type=Path, help="write Markdown here; default is stdout")
    render_md.set_defaults(func=cmd_render_md)

    render_txt = commands.add_parser("render-txt", help="render plain text")
    _add_resume_arg(render_txt)
    render_txt.add_argument("--width", type=int, default=72, help="line width from 40 to 120 (default: 72)")
    render_txt.add_argument("--out", type=Path, help="write text here; default is stdout")
    render_txt.set_defaults(func=cmd_render_txt)

    render_html_cmd = commands.add_parser("render-html", help="render HTML with a built-in theme")
    _add_resume_arg(render_html_cmd)
    render_html_cmd.add_argument(
        "--theme",
        default="atelier",
        help=f"built-in theme ({', '.join(theme_names())})",
    )
    render_html_cmd.add_argument("--out", type=Path, help="write HTML here; default is stdout")
    render_html_cmd.set_defaults(func=cmd_render_html)

    diff = commands.add_parser("diff", help="compare two resume files")
    diff.add_argument("left", type=Path)
    diff.add_argument("right", type=Path)
    diff.set_defaults(func=cmd_diff)

    merge_cmd = commands.add_parser("merge", help="merge two local resume files")
    merge_cmd.add_argument("left", type=Path, help="resume whose meta and ids win")
    merge_cmd.add_argument("right", type=Path, help="resume to add entries from")
    merge_cmd.add_argument("--out", type=Path, help="write the merged resume here; default is stdout")
    merge_cmd.set_defaults(func=cmd_merge)

    stats_cmd = commands.add_parser("stats", help="count words, roles, and years")
    _add_resume_arg(stats_cmd)
    stats_cmd.set_defaults(func=cmd_stats)

    snapshot = commands.add_parser("snapshot", help="save a copy of the resume beside the file")
    _add_resume_arg(snapshot)
    snapshot.add_argument("--label", required=True, help="short name for this version")
    snapshot.add_argument("--force", action="store_true", help="replace a snapshot with the same label")
    snapshot.set_defaults(func=cmd_snapshot)

    snapshots_cmd = commands.add_parser("snapshots", help="list saved resume versions")
    _add_resume_arg(snapshots_cmd)
    snapshots_cmd.set_defaults(func=cmd_snapshots)

    restore = commands.add_parser("restore", help="replace the resume with a saved version")
    _add_resume_arg(restore)
    restore.add_argument("--label", help="snapshot label to restore")
    restore.add_argument("--id", dest="snapshot_id", help="snapshot id to restore")
    restore.set_defaults(func=cmd_restore)

    export = commands.add_parser("export", help="write Markdown, JSON, YAML, and each HTML theme")
    _add_resume_arg(export)
    export.add_argument("--out", type=Path, help="directory to create")
    export.add_argument("--zip", dest="zip_path", type=Path, help="zip archive to create")
    export.set_defaults(func=cmd_export)

    preview = commands.add_parser("preview", help="serve the rendered resume on 127.0.0.1")
    _add_resume_arg(preview)
    preview.add_argument("--theme", default="atelier", help=f"built-in theme ({', '.join(theme_names())})")
    preview.add_argument("--port", type=int, default=8765)
    preview.set_defaults(func=cmd_preview)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ResumeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def console_main() -> None:
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        raise SystemExit(130) from None
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except OSError:
            pass
        raise SystemExit(0) from None


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if path.is_dir():
        path = path / "resume.yaml"
    if path.exists() and not args.force:
        print(f"error: refusing to overwrite {path}; pass --force to replace it", file=sys.stderr)
        return 1
    write_starter(path)
    print(f"wrote {path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    issues = validate_resume(resume)
    return _print_issues(issues, str(args.path), strict=args.strict)


def cmd_schema(args: argparse.Namespace) -> int:
    if args.show and args.path is not None:
        print("error: pass a resume file or --show, not both", file=sys.stderr)
        return 1
    if args.show:
        sys.stdout.write(schema_text())
        return 0
    if args.path is None:
        print("error: pass a resume file or --show", file=sys.stderr)
        return 1
    resume = load_resume(args.path)
    errors = schema_errors(resume)
    if not errors:
        print(f"ok: {args.path}")
        return 0
    for error in errors:
        print(f"error: {args.path}: {error}", file=sys.stderr)
    print(f"{args.path}: {len(errors)} schema error(s)", file=sys.stderr)
    return 1


def cmd_add_role(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    updated = add_role(
        resume,
        company=args.company,
        title=args.title,
        start=args.start,
        end=args.end,
        location=args.location,
        role_id=args.role_id,
        highlights=args.highlights,
        skills=args.skills,
    )
    save_resume(args.path, updated)
    print(f"added role at {args.company} to {args.path}")
    return 0


def cmd_add_project(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    updated = add_project(
        resume,
        name=args.name,
        url=args.url,
        description=args.description,
        project_id=args.project_id,
        highlights=args.highlights,
        skills=args.skills,
    )
    save_resume(args.path, updated)
    print(f"added project {args.name} to {args.path}")
    return 0


def cmd_skills(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    sys.stdout.write(format_skills(resume))
    return 0


def cmd_add_skill(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    updated = add_skill(resume, args.group, args.item)
    save_resume(args.path, updated)
    print(f"added {args.item} to {args.group} in {args.path}")
    return 0


def cmd_reorder(args: argparse.Namespace) -> int:
    if args.sections and (args.entries or args.ids):
        print("error: pass sections or entries, not both", file=sys.stderr)
        return 1
    if args.entries and not args.ids:
        print("error: pass at least one --id when reordering entries", file=sys.stderr)
        return 1
    if not args.sections and not args.entries:
        print("error: pass --section or --entries", file=sys.stderr)
        return 1
    resume = load_resume(args.path)
    if args.entries:
        updated = reorder_entries(resume, args.entries, args.ids)
        print(f"reordered {args.entries} in {args.path}")
    else:
        updated = reorder_sections(resume, args.sections)
        print(f"reordered sections in {args.path}")
    save_resume(args.path, updated)
    return 0


def cmd_tailor(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    if _reject_errors(resume, args.path):
        return 1
    result = tailor_resume(
        resume,
        args.role,
        keywords=args.keywords,
        max_roles=args.max_roles,
        max_projects=args.max_projects,
    )
    for note in result.notes:
        print(f"note: {note}", file=sys.stderr)
    print(
        "roles: " + (", ".join(result.kept_role_ids) if result.kept_role_ids else "(none)"),
        file=sys.stderr,
    )
    if result.dropped_role_ids:
        print("dropped roles: " + ", ".join(result.dropped_role_ids), file=sys.stderr)
    print(
        "projects: " + (", ".join(result.kept_project_ids) if result.kept_project_ids else "(none)"),
        file=sys.stderr,
    )
    if result.dropped_project_ids:
        print("dropped projects: " + ", ".join(result.dropped_project_ids), file=sys.stderr)
    if args.out:
        save_resume(args.out, result.resume)
        print(f"wrote {args.out}")
    else:
        sys.stdout.write(dump_text(result.resume, args.path))
    return 0


def cmd_keywords(args: argparse.Namespace) -> int:
    if args.fail_under is not None and not 0 <= args.fail_under <= 100:
        print("error: --fail-under must be from 0 to 100", file=sys.stderr)
        return 1
    resume = load_resume(args.path)
    if _reject_errors(resume, args.path):
        return 1
    report = keyword_coverage(resume, load_job_text(args.job), min_length=args.min_length)
    sys.stdout.write(format_coverage(report))
    if args.fail_under is not None and report.percent < args.fail_under:
        return 1
    return 0


def cmd_cover_letter(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    if _reject_errors(resume, args.path):
        return 1
    letter = render_cover_letter(resume, role=args.role, company=args.company)
    _write_output(letter, args.out)
    return 0


def cmd_render_md(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    if _reject_errors(resume, args.path):
        return 1
    _write_output(render_markdown(resume), args.out)
    return 0


def cmd_render_txt(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    if _reject_errors(resume, args.path):
        return 1
    _write_output(render_plain(resume, args.width), args.out)
    return 0


def cmd_render_html(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    if _reject_errors(resume, args.path):
        return 1
    theme = normalize_theme(args.theme)
    _write_output(render_html(resume, theme), args.out)
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    merged, notes = merge_resumes(load_resume(args.left), load_resume(args.right))
    for note in notes:
        print(f"note: {note}", file=sys.stderr)
    if args.out is None:
        sys.stdout.write(dump_text(merged, args.left))
    else:
        save_resume(args.out, merged)
        print(f"wrote {args.out}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    if _reject_errors(resume, args.path):
        return 1
    sys.stdout.write(format_stats(resume_stats(resume)))
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    saved = take_snapshot(args.path, args.label, force=args.force)
    print(f"saved snapshot {saved.number} ({saved.label}) beside {args.path}")
    return 0


def cmd_snapshots(args: argparse.Namespace) -> int:
    sys.stdout.write(format_snapshots(list_snapshots(args.path)))
    return 0


def cmd_restore(args: argparse.Namespace) -> int:
    if bool(args.label) == bool(args.snapshot_id):
        print("error: pass --label or --id", file=sys.stderr)
        return 1
    restored = restore_snapshot(args.path, label=args.label, number=args.snapshot_id)
    print(f"restored snapshot {restored.number} ({restored.label}) to {args.path}")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    left = load_resume(args.left)
    right = load_resume(args.right)
    changes = diff_resumes(left, right)
    sys.stdout.write(format_diff(changes))
    return 1 if changes else 0


def cmd_export(args: argparse.Namespace) -> int:
    if args.out is None and args.zip_path is None:
        print("error: pass --out, --zip, or both", file=sys.stderr)
        return 1
    resume = load_resume(args.path)
    if _reject_errors(resume, args.path):
        return 1
    if args.out is not None:
        written = export_directory(resume, args.out)
        for path in written:
            print(f"wrote {path}")
    if args.zip_path is not None:
        export_zip(resume, args.zip_path)
        print(f"wrote {args.zip_path}")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    theme = normalize_theme(args.theme)
    server = make_preview_server(args.path, theme, args.port)
    host, port = server.server_address
    print(f"Serving http://{host}:{port}/", flush=True)
    print(f"Rendering {args.path} with the {theme} theme.", flush=True)
    print("This preview reads only the local resume file and listens on 127.0.0.1.", flush=True)
    try:
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


def _add_resume_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", type=Path, help="resume file (.yaml, .yml, or .json)")


def _print_issues(issues: list[Issue], source: str, *, strict: bool) -> int:
    if not issues:
        print(f"ok: {source}")
        return 0
    ordered = sorted(issues, key=lambda issue: (0 if issue.severity == "error" else 1, issue.path))
    for issue in ordered:
        print(issue.format(source), file=sys.stderr)
    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    if errors:
        print(f"{source}: {errors} error(s), {warnings} warning(s)", file=sys.stderr)
        return 1
    print(f"{source}: {warnings} warning(s)")
    if strict:
        return 1
    return 0


def _reject_errors(resume: dict, source: Path) -> bool:
    issues = validate_resume(resume)
    errors = [issue for issue in issues if issue.severity == "error"]
    if not errors:
        return False
    _print_issues(errors, str(source), strict=False)
    return True


def _write_output(text: str, path: Path | None) -> None:
    if path is None:
        sys.stdout.write(text)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    console_main()
