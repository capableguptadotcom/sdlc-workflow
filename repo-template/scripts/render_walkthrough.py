#!/usr/bin/env python3
"""Render the tabletop walkthrough from canonical dialogue cases."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def render_walkthrough(data: dict) -> str:
    cases = {case["id"]: case for case in data["cases"]}
    mental_model = data["developer_mental_model"]
    lines = [
        "# AI Developer Kit walkthrough (draft)",
        "",
        "> Tabletop design only. This walkthrough describes the accepted product",
        "> contract; it does not claim the active skills implement every scenario yet.",
        "",
        "Describe work normally. The assistant inspects the repository, announces what",
        "it is doing in plain language, and uses the lightest reliable workflow.",
        "",
        "## The developer mental model",
        "",
        mental_model["promise"],
        "",
    ]
    for index, item in enumerate(mental_model["sequence"], start=1):
        lines.append(
            f"{index}. **{item['step']}** — Developer: {item['developer']} "
            f"Assistant: {item['assistant']}"
        )

    lines.extend(
        [
            "",
            "## Things developers can say",
            "",
            "| Developer says | Assistant does |",
            "| --- | --- |",
        ]
    )
    for example in mental_model["examples"]:
        lines.append(
            f"| {example['developer_says']} | {example['assistant_does']} |"
        )

    lines.extend(
        [
            "",
            "## How the assistant classifies uncertainty",
            "",
            "| Signal | Example | Response | Internal route |",
            "| --- | --- | --- | --- |",
        ]
    )
    for rule in mental_model["uncertainty_rules"]:
        lines.append(
            f"| {rule['signal']} | {rule['example']} | {rule['response']} | "
            f"`{rule['route']}` |"
        )

    lines.extend(
        [
            "",
            "## Visible modes",
            "",
        ]
    )
    for label in data["visible_modes"].values():
        lines.append(f"- {label}")

    for scenario_id in data["walkthrough_scenario_ids"]:
        case = cases[scenario_id]
        lines.extend(["", f"## {case['title']}", ""])
        for turn in case["walkthrough_transcript"]:
            lines.extend([f"**{turn['speaker']}:** {turn['text']}", ""])
        lines.extend(
            [
                f"- Route: {' -> '.join(case['expected_internal_route'])}",
                f"- Creates: {', '.join(case['artifacts_created']) or 'nothing'}",
                f"- Skips: {', '.join(case['artifacts_skipped']) or 'nothing'}",
                f"- Human gates: {', '.join(case['human_gates']) or 'none'}",
                f"- Checks: {', '.join(case['deterministic_commands']) or 'none'}",
                f"- Must not: {', '.join(case['forbidden_behavior'])}",
                f"- Terminal state: `{case['expected_terminal_state']}`",
            ]
        )

    return "\n".join(lines) + "\n"


def render_developer_walkthrough(data: dict) -> str:
    cases = {case["id"]: case for case in data["cases"]}
    mental_model = data["developer_mental_model"]
    lines = [
        "# AI Developer Kit",
        "",
        "> Workflow alpha. The repository guidance and structural checks are installed;",
        "> use them with project-specific validation and evidence.",
        "",
        mental_model["promise"],
        "",
        "Start with the [interactive workflow walkthrough](workflow-walkthrough.html) "
        "for visual, scenario-based tutorials and copyable example prompts.",
        "",
        "## How to work with it",
        "",
    ]
    for index, item in enumerate(mental_model["sequence"], start=1):
        lines.append(
            f"{index}. **{item['step']}** — {item['developer']} "
            f"The assistant will {item['assistant'][0].lower()}{item['assistant'][1:]}"
        )

    lines.extend(
        [
            "",
            "## Things you can say",
            "",
            "| You say | The assistant |",
            "| --- | --- |",
        ]
    )
    for example in mental_model["examples"]:
        lines.append(
            f"| {example['developer_says']} | {example['assistant_does']} |"
        )

    lines.extend(["", "## Examples in context", ""])
    for scenario_id in data["installed_walkthrough_scenario_ids"]:
        case = cases[scenario_id]
        lines.extend([f"### {case['title']}", ""])
        for turn in case["walkthrough_transcript"]:
            lines.extend([f"**{turn['speaker']}:** {turn['text']}", ""])

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when the checked-in draft differs from rendered dialogue data.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    source = root / "evals" / "dialogue-cases.json"
    outputs = {
        root / "evals" / "walkthrough-draft.md": render_walkthrough,
        root / ".ai" / "README.md": render_developer_walkthrough,
    }
    data = json.loads(source.read_text(encoding="utf-8"))

    if args.check:
        stale = []
        for output, render in outputs.items():
            current = output.read_text(encoding="utf-8") if output.exists() else ""
            if current != render(data):
                stale.append(output)
        if stale:
            for output in stale:
                print(f"{output}: stale; run {Path(__file__).name}", file=sys.stderr)
            return 1
        print(f"Validated walkthrough generated from {len(data['walkthrough_scenario_ids'])} scenarios.")
        return 0

    for output, render in outputs.items():
        output.write_text(render(data), encoding="utf-8")
        print(f"Rendered {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
