"""Command-line interface for Quillfolio."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from quillfolio import __version__
from quillfolio.bundle import export_directory, export_zip
from quillfolio.diffing import diff_resumes, format_diff
from quillfolio.errors import Issue, ResumeError
from quillfolio.html_render import normalize_theme, render_html, theme_names
from quillfolio.markdown_render import render_markdown
from quillfolio.mutate import add_project, add_role, write_starter
from quillfolio.preview import make_preview_server
from quillfolio.resume_io import dump_text, load_resume, save_resume
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

    tailor = commands.add_parser("tailor", help="keep sections that match a target role")
    _add_resume_arg(tailor)
    tailor.add_argument("--role", required=True, help="target role, for example 'Python systems'")
    tailor.add_argument("--keyword", action="append", dest="keywords", help="extra word that should count as a match")
    tailor.add_argument("--out", type=Path, help="write the tailored resume here; default is stdout")
    tailor.add_argument("--max-roles", type=int)
    tailor.add_argument("--max-projects", type=int)
    tailor.set_defaults(func=cmd_tailor)

    render_md = commands.add_parser("render-md", help="render Markdown")
    _add_resume_arg(render_md)
    render_md.add_argument("--out", type=Path, help="write Markdown here; default is stdout")
    render_md.set_defaults(func=cmd_render_md)

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

    export = commands.add_parser("export", help="write Markdown, JSON, YAML, and both HTML themes")
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


def cmd_render_md(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    if _reject_errors(resume, args.path):
        return 1
    _write_output(render_markdown(resume), args.out)
    return 0


def cmd_render_html(args: argparse.Namespace) -> int:
    resume = load_resume(args.path)
    if _reject_errors(resume, args.path):
        return 1
    theme = normalize_theme(args.theme)
    _write_output(render_html(resume, theme), args.out)
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
