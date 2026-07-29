#!/usr/bin/env python3
"""Validate the cross-agent skill pack without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from render_walkthrough import render_developer_walkthrough, render_walkthrough


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ADR_NAME_RE = re.compile(r"^(?P<number>[0-9]{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")


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


def parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    return [
        item.strip().strip("'\"")
        for item in value[1:-1].split(",")
        if item.strip()
    ]


def parse_yaml_mapping(text: str, section: str) -> dict[str, str]:
    """Read one flat mapping from the kit's deliberately small YAML schema."""
    match = re.search(
        rf"^{re.escape(section)}:\s*$\n(?P<body>(?:^[ \t]+.*(?:\n|$))*)",
        text,
        re.MULTILINE,
    )
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group("body").splitlines():
        item = re.match(r"^\s+([a-z_]+):\s*([^#]+?)\s*$", line)
        if item:
            values[item.group(1)] = item.group(2).strip("'\"")
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat incomplete project-adoption configuration as an error.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        help="Validate an adopted repository instead of the bundled template.",
    )
    args = parser.parse_args()

    root = (
        args.project_root.resolve()
        if args.project_root
        else Path(__file__).resolve().parents[1]
    )
    errors: list[str] = []
    warnings: list[str] = []
    config = (root / "ai-sdlc.yaml").read_text(encoding="utf-8")
    configured_paths = parse_yaml_mapping(config, "paths")
    specs_path = configured_paths.get("specs", "specs")
    decisions_path = configured_paths.get("decisions", "docs/adr")
    initiatives_path = configured_paths.get("initiatives", "initiatives")
    required_artifact_paths = (
        ".ai/ARTIFACTS.md",
        ".ai/templates/CONTEXT.md",
        ".ai/templates/CONTEXT-MAP.md",
        ".ai/templates/adr.md",
        ".ai/templates/initiative-map.md",
        f"{specs_path}/_template/spec.md",
        f"{specs_path}/_template/plan.md",
        f"{specs_path}/_template/tasks.md",
        f"{specs_path}/_template/verification.md",
    )
    for relative_path in required_artifact_paths:
        if not (root / relative_path).is_file():
            errors.append(f"{relative_path}: required artifact guidance is missing")

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
    for skill in skills:
        positive_count = sum(skill in case.get("invoke", []) for case in routing_cases)
        negative_count = sum(skill in case.get("not_invoke", []) for case in routing_cases)
        if positive_count < 2:
            errors.append(
                f"routing cases need at least 2 positive cases for {skill}; "
                f"found {positive_count}"
            )
        if negative_count < 2:
            errors.append(
                f"routing cases need at least 2 negative cases for {skill}; "
                f"found {negative_count}"
            )

    behavior = load_json(root / "evals" / "behavior-cases.json", errors)
    behavior_cases = behavior.get("cases", []) if isinstance(behavior, dict) else []
    behavior_skills = {case.get("target_skill") for case in behavior_cases}
    if behavior_skills != skills:
        errors.append(f"behavior cases lack coverage for {sorted(skills - behavior_skills)}")
    for case in behavior_cases:
        if len(case.get("assertions", [])) < 2:
            errors.append(f"behavior case for {case.get('target_skill')} needs assertions")

    dialogues = load_json(root / "evals" / "dialogue-cases.json", errors)
    dialogue_cases = dialogues.get("cases", []) if isinstance(dialogues, dict) else []
    visible_modes = dialogues.get("visible_modes", {}) if isinstance(dialogues, dict) else {}
    mental_model = dialogues.get("developer_mental_model", {})
    for field in ("promise", "sequence", "examples", "uncertainty_rules"):
        if not mental_model.get(field):
            errors.append(f"developer mental model: {field} must not be empty")
    for item in mental_model.get("sequence", []):
        for field in ("step", "developer", "assistant"):
            if not item.get(field):
                errors.append(f"developer mental model sequence: {field} must not be empty")
    for example in mental_model.get("examples", []):
        for field in ("developer_says", "assistant_does"):
            if not example.get(field):
                errors.append(f"developer mental model example: {field} must not be empty")
    for rule in mental_model.get("uncertainty_rules", []):
        for field in ("signal", "example", "response", "route"):
            if not rule.get(field):
                errors.append(f"developer uncertainty rule: {field} must not be empty")
    required_dialogue_fields = {
        "id",
        "source_dialogue",
        "title",
        "repository_fixture",
        "developer_turns",
        "walkthrough_transcript",
        "expected_visible_modes",
        "expected_internal_route",
        "artifacts_created",
        "artifacts_skipped",
        "human_gates",
        "deterministic_commands",
        "allowed_mutations",
        "forbidden_mutations",
        "forbidden_behavior",
        "expected_terminal_state",
    }
    dialogue_ids = [case.get("id") for case in dialogue_cases]
    if len(dialogue_ids) != len(set(dialogue_ids)):
        errors.append("evals/dialogue-cases.json: duplicate case id")
    for case in behavior_cases:
        dialogue_id = case.get("dialogue_id")
        if dialogue_id and dialogue_id not in dialogue_ids:
            errors.append(f"behavior case references unknown dialogue {dialogue_id!r}")
    source_dialogues = [case.get("source_dialogue") for case in dialogue_cases]
    if (
        any(not isinstance(number, int) for number in source_dialogues)
        or sorted(source_dialogues) != list(range(1, len(dialogue_cases) + 1))
    ):
        errors.append(
            "evals/dialogue-cases.json: source_dialogue values must be unique "
            "and sequential from 1"
        )
    for case in dialogue_cases:
        missing = required_dialogue_fields - set(case)
        if missing:
            errors.append(
                f"dialogue case {case.get('id')!r}: missing fields {sorted(missing)}"
            )
        unknown_modes = set(case.get("expected_visible_modes", [])) - set(visible_modes)
        if unknown_modes:
            errors.append(
                f"dialogue case {case.get('id')!r}: unknown visible modes "
                f"{sorted(unknown_modes)}"
            )
        if not case.get("walkthrough_transcript"):
            errors.append(f"dialogue case {case.get('id')!r}: transcript is empty")
        if not case.get("expected_internal_route"):
            errors.append(f"dialogue case {case.get('id')!r}: route is empty")
        if not case.get("forbidden_behavior"):
            errors.append(f"dialogue case {case.get('id')!r}: forbidden behavior is empty")
        tracker_mutation = any(
            "tracker" in mutation.lower()
            for mutation in case.get("allowed_mutations", [])
        )
        tracker_gate = any(
            "authoriz" in gate.lower() and "tracker" in gate.lower()
            for gate in case.get("human_gates", [])
        )
        if tracker_mutation and not tracker_gate:
            errors.append(
                f"dialogue case {case.get('id')!r}: external tracker mutation "
                "requires explicit human gate"
            )

    selected_dialogues = dialogues.get("walkthrough_scenario_ids", [])
    if len(selected_dialogues) != len(set(selected_dialogues)):
        errors.append("evals/dialogue-cases.json: duplicate walkthrough scenario id")
    unknown_selected = set(selected_dialogues) - set(dialogue_ids)
    if unknown_selected:
        errors.append(
            "evals/dialogue-cases.json: walkthrough references unknown scenarios "
            f"{sorted(unknown_selected)}"
        )
    installed_dialogues = dialogues.get("installed_walkthrough_scenario_ids", [])
    if len(installed_dialogues) != len(set(installed_dialogues)):
        errors.append(
            "evals/dialogue-cases.json: duplicate installed walkthrough scenario id"
        )
    unknown_installed = set(installed_dialogues) - set(dialogue_ids)
    if unknown_installed:
        errors.append(
            "evals/dialogue-cases.json: installed walkthrough references unknown "
            f"scenarios {sorted(unknown_installed)}"
        )
    routing_boundaries = dialogues.get("routing_boundary_cases", [])
    boundary_ids = [case.get("id") for case in routing_boundaries]
    if len(boundary_ids) != len(set(boundary_ids)):
        errors.append("evals/dialogue-cases.json: duplicate routing boundary id")
    for case in routing_boundaries:
        for field in ("id", "prompt", "expected_route", "rejected_routes", "reason"):
            if not case.get(field):
                errors.append(
                    f"routing boundary {case.get('id')!r}: {field} must not be empty"
                )
    walkthrough = root / "evals" / "walkthrough-draft.md"
    if dialogue_cases and not unknown_selected:
        rendered = render_walkthrough(dialogues)
        current = walkthrough.read_text(encoding="utf-8") if walkthrough.exists() else ""
        if current != rendered:
            errors.append(
                "evals/walkthrough-draft.md: stale; run scripts/render_walkthrough.py"
            )
    if dialogue_cases and not unknown_installed:
        developer_walkthrough = root / ".ai" / "README.md"
        if not developer_walkthrough.exists():
            errors.append(".ai/README.md: generated developer walkthrough is missing")
        elif developer_walkthrough.read_text(
            encoding="utf-8"
        ) != render_developer_walkthrough(dialogues):
            errors.append(
                ".ai/README.md: stale; run scripts/render_walkthrough.py"
            )

    specs_root = root / specs_path
    for spec_path in sorted(specs_root.glob("*/spec.md")):
        if spec_path.parent.name == "_template":
            continue
        meta, _ = frontmatter(spec_path, errors)
        status = meta.get("status")
        if status not in {"draft", "accepted", "superseded"}:
            errors.append(
                f"{spec_path.relative_to(root).as_posix()}: invalid status {status!r}"
            )
        if status == "accepted" and not (
            meta.get("accepted_at") and meta.get("accepted_via")
        ):
            errors.append(
                f"accepted spec {spec_path.relative_to(root).as_posix()} "
                "requires accepted_at and accepted_via"
            )
        if status == "superseded" and not meta.get("superseded_by"):
            errors.append(
                f"superseded spec {spec_path.relative_to(root).as_posix()} "
                "requires superseded_by"
            )
        if not (spec_path.parent / "verification.md").exists():
            errors.append(
                f"{spec_path.relative_to(root).as_posix()} requires verification.md"
            )
        plan_path = spec_path.parent / "plan.md"
        if plan_path.exists():
            plan_meta, _ = frontmatter(plan_path, errors)
            if plan_meta.get("status") == "accepted" and not all(
                plan_meta.get(field)
                for field in ("accepted_at", "accepted_via", "accepted_spec")
            ):
                errors.append(
                    f"accepted plan {plan_path.relative_to(root).as_posix()} "
                    "requires accepted_at, accepted_via, and accepted_spec"
                )

    decisions_root = root / decisions_path
    decisions: dict[str, tuple[Path, list[str], list[str]]] = {}
    for decision_path in sorted(decisions_root.glob("*.md")):
        match = ADR_NAME_RE.fullmatch(decision_path.name)
        if not match:
            continue
        meta, _ = frontmatter(decision_path, errors)
        status = meta.get("status")
        if status not in {
            "proposed",
            "accepted",
            "rejected",
            "deprecated",
            "superseded",
        }:
            errors.append(
                f"{decision_path.relative_to(root).as_posix()}: "
                f"invalid ADR status {status!r}"
            )
        number = match.group("number")
        if number in decisions:
            errors.append(f"docs/adr: duplicate ADR number {number}")
            continue
        decisions[number] = (
            decision_path,
            parse_inline_list(meta.get("supersedes", "")),
            parse_inline_list(meta.get("superseded_by", "")),
        )
    for number, (decision_path, supersedes, superseded_by) in decisions.items():
        for target in superseded_by:
            replacement = decisions.get(target)
            if not replacement:
                errors.append(
                    f"{decision_path.relative_to(root).as_posix()}: "
                    f"superseded_by unknown ADR {target}"
                )
            elif number not in replacement[1]:
                errors.append(
                    f"{decision_path.relative_to(root).as_posix()}: "
                    f"superseded_by {target} requires reciprocal supersedes link"
                )
        for target in supersedes:
            replaced = decisions.get(target)
            if not replaced:
                errors.append(
                    f"{decision_path.relative_to(root).as_posix()}: "
                    f"supersedes unknown ADR {target}"
                )
            elif number not in replaced[2]:
                errors.append(
                    f"{decision_path.relative_to(root).as_posix()}: "
                    f"supersedes {target} requires reciprocal superseded_by link"
                )

    initiatives_root = root / initiatives_path
    for map_path in sorted(initiatives_root.glob("*/map.md")):
        if map_path.parent.name == "_template":
            continue
        meta, text = frontmatter(map_path, errors)
        status = meta.get("status")
        if status not in {"active", "completed", "paused", "superseded"}:
            errors.append(
                f"{map_path.relative_to(root).as_posix()}: "
                f"invalid initiative status {status!r}"
            )
        if "## Decision tracks" not in text:
            errors.append(
                f"{map_path.relative_to(root).as_posix()}: "
                "missing section '## Decision tracks'"
            )
        if status == "active" and "## Next branch" not in text:
            errors.append(
                f"{map_path.relative_to(root).as_posix()}: "
                "active initiative requires '## Next branch'"
            )

    if not re.search(r"^schema_version:\s*2\s*$", config, re.MULTILINE):
        errors.append("ai-sdlc.yaml: schema_version must be 2")
    if re.search(r"^kit_version:", config, re.MULTILINE):
        errors.append("ai-sdlc.yaml: kit_version belongs in .ai/kit.lock.json")
    required_config_fields = {
        "paths.initiatives": r"^  initiatives:\s*\S+",
        "paths.context_entry": r"^  context_entry:\s*\S+",
        "artifact_profiles.spec": r"^  spec:\s*\S+",
        "artifact_profiles.adr": r"^  adr:\s*\S+",
        "artifact_profiles.context": r"^  context:\s*\S+",
    }
    for field, pattern in required_config_fields.items():
        if not re.search(pattern, config, re.MULTILINE):
            errors.append(f"ai-sdlc.yaml: missing required schema v2 field {field}")
    if re.search(r"^\s+[a-z_]+:\s*\[\]\s*$", config, re.MULTILINE):
        warnings.append("ai-sdlc.yaml still contains empty command lists; complete adoption")

    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors or (args.strict and warnings):
        return 1
    print(
        f"Validated kit structure for {len(skills)} skills, "
        f"{len(routing_cases)} routing case definitions, "
        f"{len(behavior_cases)} behavior case definitions, and "
        f"{len(dialogue_cases)} dialogue case definitions."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
