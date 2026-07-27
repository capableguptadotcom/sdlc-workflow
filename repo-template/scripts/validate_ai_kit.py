#!/usr/bin/env python3
"""Validate the cross-agent skill pack without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: cannot read valid JSON: {exc}")
        return {}


def frontmatter(path: Path, errors: list[str]) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"{path}: missing opening frontmatter delimiter")
        return {}, text
    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append(f"{path}: missing closing frontmatter delimiter")
        return {}, text
    values: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"{path}: unsupported frontmatter line: {line!r}")
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values, text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat incomplete project-adoption configuration as an error.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    warnings: list[str] = []
    skills_root = root / ".agents" / "skills"
    skill_files = sorted(skills_root.glob("*/SKILL.md"))
    if not skill_files:
        errors.append(f"{skills_root}: no skills found")

    skills: set[str] = set()
    for path in skill_files:
        meta, text = frontmatter(path, errors)
        unknown = set(meta) - {"name", "description"}
        if unknown:
            errors.append(f"{path}: non-portable frontmatter keys: {sorted(unknown)}")
        name = meta.get("name", "")
        description = meta.get("description", "")
        if name != path.parent.name:
            errors.append(f"{path}: name {name!r} must match directory {path.parent.name!r}")
        if not NAME_RE.fullmatch(name):
            errors.append(f"{path}: invalid skill name {name!r}")
        if "Use " not in description or "Do not use" not in description:
            errors.append(f"{path}: description needs explicit Use and Do not use triggers")
        if len(text.splitlines()) > 500:
            errors.append(f"{path}: exceeds the 500-line progressive-disclosure limit")
        skills.add(name)

    claude = root / ".claude" / "commands"
    wrappers = {p.stem for p in claude.glob("*.md")}
    if wrappers != skills:
        errors.append(
            f"{claude}: wrappers differ from canonical skills; "
            f"missing={sorted(skills - wrappers)}, extra={sorted(wrappers - skills)}"
        )
    for name in skills & wrappers:
        wrapper = (claude / f"{name}.md").read_text(encoding="utf-8")
        target = f".agents/skills/{name}/SKILL.md"
        if target not in wrapper:
            errors.append(f"{claude / (name + '.md')}: does not point to {target}")

    if "@AGENTS.md" not in (root / "CLAUDE.md").read_text(encoding="utf-8"):
        errors.append("CLAUDE.md: must import @AGENTS.md")
    if "AGENTS.md" not in (root / ".github" / "copilot-instructions.md").read_text(
        encoding="utf-8"
    ):
        errors.append(".github/copilot-instructions.md: must point to AGENTS.md")

    catalog = load_json(root / ".ai" / "skills-catalog.json", errors)
    catalog_entries = catalog.get("skills", []) if isinstance(catalog, dict) else []
    catalog_names = {entry.get("name") for entry in catalog_entries}
    if catalog_names != skills:
        errors.append(
            ".ai/skills-catalog.json: names differ from canonical skills; "
            f"missing={sorted(skills - catalog_names)}, "
            f"extra={sorted(catalog_names - skills)}"
        )

    lock = load_json(root / ".ai" / "skills.lock.json", errors)
    sources = lock.get("sources", []) if isinstance(lock, dict) else []
    source_ids = {source.get("id") for source in sources}
    for source in sources:
        sha = source.get("reviewed_commit", "")
        if not SHA_RE.fullmatch(sha):
            errors.append(f".ai/skills.lock.json: invalid commit for {source.get('id')!r}")
    for entry in catalog_entries:
        missing_sources = set(entry.get("sources", [])) - source_ids
        if missing_sources:
            errors.append(
                f".ai/skills-catalog.json: {entry.get('name')} has unknown sources "
                f"{sorted(missing_sources)}"
            )

    routing = load_json(root / "evals" / "routing-cases.json", errors)
    routing_cases = routing.get("cases", []) if isinstance(routing, dict) else []
    invoked = {name for case in routing_cases for name in case.get("invoke", [])}
    rejected = {name for case in routing_cases for name in case.get("not_invoke", [])}
    if invoked != skills:
        errors.append(f"routing cases lack positive coverage for {sorted(skills - invoked)}")
    if rejected != skills:
        errors.append(f"routing cases lack negative coverage for {sorted(skills - rejected)}")

    behavior = load_json(root / "evals" / "behavior-cases.json", errors)
    behavior_cases = behavior.get("cases", []) if isinstance(behavior, dict) else []
    behavior_skills = {case.get("target_skill") for case in behavior_cases}
    if behavior_skills != skills:
        errors.append(f"behavior cases lack coverage for {sorted(skills - behavior_skills)}")
    for case in behavior_cases:
        if len(case.get("assertions", [])) < 2:
            errors.append(f"behavior case for {case.get('target_skill')} needs assertions")

    config = (root / "ai-sdlc.yaml").read_text(encoding="utf-8")
    if re.search(r"^\s+[a-z_]+:\s*\[\]\s*$", config, re.MULTILINE):
        warnings.append("ai-sdlc.yaml still contains empty command lists; complete adoption")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors or (args.strict and warnings):
        return 1
    print(f"Validated {len(skills)} skills, {len(routing_cases)} routing cases, "
          f"and {len(behavior_cases)} behavior cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
