from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "repo-template"
VALIDATOR = TEMPLATE / "scripts" / "validate_ai_kit.py"


class ValidateAiKitTests(unittest.TestCase):
    def copy_template(self, temp_dir: str) -> Path:
        project = Path(temp_dir) / "project"
        shutil.copytree(TEMPLATE, project)
        return project

    def run_validator(self, project: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--project-root",
                str(project),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_finish_requires_failure_safe_runtime_cleanup(self) -> None:
        finish = (
            TEMPLATE / ".agents" / "skills" / "finish" / "SKILL.md"
        ).read_text(encoding="utf-8")
        behavior = json.loads(
            (TEMPLATE / "evals" / "behavior-cases.json").read_text(
                encoding="utf-8"
            )
        )
        cases = [
            case
            for case in behavior["cases"]
            if case.get("id") == "finish-runtime-process-cleanup"
        ]

        self.assertIn("failure-safe cleanup", finish)
        self.assertIn("terminal event", finish)
        self.assertIn("not-ready", finish)
        self.assertEqual(1, len(cases))
        self.assertIn(
            "stops every started process even when a check fails",
            cases[0]["assertions"],
        )
        self.assertIn(
            "does not report ready while any command lacks a terminal event",
            cases[0]["assertions"],
        )

    def test_validator_does_not_create_import_bytecode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            cache = project / "scripts" / "__pycache__"
            shutil.rmtree(cache, ignore_errors=True)

            result = self.run_validator(project)

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertFalse(cache.exists())

    def test_feature_spec_requires_verification_companion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            feature = project / "specs" / "team-invitations"
            feature.mkdir()
            (feature / "spec.md").write_text(
                "# Feature specification: team invitations\n",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "specs/team-invitations/spec.md requires verification.md",
            result.stderr,
        )

    def test_accepted_spec_requires_durable_acceptance_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            feature = project / "specs" / "team-invitations"
            feature.mkdir()
            (feature / "spec.md").write_text(
                """\
---
status: accepted
accepted_at:
accepted_via:
superseded_by:
---

# Feature specification: team invitations
""",
                encoding="utf-8",
            )
            (feature / "verification.md").write_text(
                "# Verification: team invitations\n",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "accepted spec specs/team-invitations/spec.md requires accepted_at and accepted_via",
            result.stderr,
        )

    def test_superseded_spec_names_its_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            feature = project / "specs" / "team-invitations"
            feature.mkdir()
            (feature / "spec.md").write_text(
                """\
---
status: superseded
accepted_at: 2026-07-20
accepted_via: interactive-review
superseded_by:
---

# Feature specification: team invitations
""",
                encoding="utf-8",
            )
            (feature / "verification.md").write_text(
                "# Verification: team invitations\n",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "superseded spec specs/team-invitations/spec.md requires superseded_by",
            result.stderr,
        )

    def test_accepted_plan_requires_durable_acceptance_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            feature = project / "specs" / "team-invitations"
            feature.mkdir()
            (feature / "spec.md").write_text(
                """\
---
status: accepted
accepted_at: 2026-07-26
accepted_via: interactive-review
superseded_by:
---

# Feature specification: team invitations
""",
                encoding="utf-8",
            )
            (feature / "verification.md").write_text(
                "# Verification: team invitations\n",
                encoding="utf-8",
            )
            (feature / "plan.md").write_text(
                """\
---
status: accepted
accepted_at:
accepted_via:
accepted_spec:
---

# Implementation plan: team invitations
""",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "accepted plan specs/team-invitations/plan.md requires accepted_at, "
            "accepted_via, and accepted_spec",
            result.stderr,
        )

    def test_adr_supersession_requires_bidirectional_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            decisions = project / "docs" / "adr"
            decisions.mkdir(parents=True)
            (decisions / "0001-use-synchronous-http.md").write_text(
                """\
---
status: superseded
date: 2026-07-01
supersedes: []
superseded_by: [0002]
related_adrs: []
related_specs: []
---

# Use synchronous HTTP
""",
                encoding="utf-8",
            )
            (decisions / "0002-use-domain-events.md").write_text(
                """\
---
status: accepted
date: 2026-07-26
supersedes: []
superseded_by: []
related_adrs: []
related_specs: []
---

# Use domain events
""",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "docs/adr/0001-use-synchronous-http.md: superseded_by 0002 "
            "requires reciprocal supersedes link",
            result.stderr,
        )

    def test_adr_supersession_link_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            decisions = project / "docs" / "adr"
            decisions.mkdir(parents=True)
            (decisions / "0002-use-domain-events.md").write_text(
                """\
---
status: accepted
date: 2026-07-26
supersedes: [0001]
superseded_by: []
related_adrs: []
related_specs: []
---

# Use domain events
""",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "docs/adr/0002-use-domain-events.md: supersedes unknown ADR 0001",
            result.stderr,
        )

    def test_adr_numbers_are_unique(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            decisions = project / "docs" / "adr"
            decisions.mkdir(parents=True)
            for name in ("0001-use-http.md", "0001-use-events.md"):
                (decisions / name).write_text(
                    """\
---
status: proposed
date: 2026-07-26
supersedes: []
superseded_by: []
related_adrs: []
related_specs: []
---

# Decision
""",
                    encoding="utf-8",
                )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn("docs/adr: duplicate ADR number 0001", result.stderr)

    def test_adr_status_is_from_the_documented_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            decisions = project / "docs" / "adr"
            decisions.mkdir(parents=True)
            (decisions / "0001-use-http.md").write_text(
                """\
---
status: active
date: 2026-07-26
supersedes: []
superseded_by: []
related_adrs: []
related_specs: []
---

# Use HTTP
""",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "docs/adr/0001-use-http.md: invalid ADR status 'active'",
            result.stderr,
        )

    def test_active_initiative_map_requires_decision_tracks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            initiative = project / "initiatives" / "customer-platform"
            initiative.mkdir(parents=True)
            (initiative / "map.md").write_text(
                """\
---
status: active
---

# Initiative: customer platform

## Outcomes

- One customer identity across channels.

## Current branch

Tenant boundaries.

## Next branch

Identity and authorization.
""",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "initiatives/customer-platform/map.md: missing section '## Decision tracks'",
            result.stderr,
        )

    def test_active_initiative_map_names_the_next_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            initiative = project / "initiatives" / "customer-platform"
            initiative.mkdir(parents=True)
            (initiative / "map.md").write_text(
                """\
---
status: active
---

# Initiative: customer platform

## Outcomes

- One customer identity across channels.

## Decision tracks

1. Tenant boundaries.
2. Identity and authorization.

## Current branch

Tenant boundaries.
""",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "initiatives/customer-platform/map.md: active initiative requires "
            "'## Next branch'",
            result.stderr,
        )

    def test_initiative_status_is_from_the_documented_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            initiative = project / "initiatives" / "customer-platform"
            initiative.mkdir(parents=True)
            (initiative / "map.md").write_text(
                """\
---
status: draft
---

# Initiative: customer platform

## Decision tracks

- Tenant boundaries.
""",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "initiatives/customer-platform/map.md: invalid initiative status 'draft'",
            result.stderr,
        )

    def test_external_tracker_mutation_requires_human_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            dialogues_path = project / "evals" / "dialogue-cases.json"
            dialogues = json.loads(dialogues_path.read_text(encoding="utf-8"))
            case = next(
                case
                for case in dialogues["cases"]
                if case["id"] == "clear-tiny-change"
            )
            case["allowed_mutations"].append("create external tracker ticket")
            dialogues_path.write_text(
                json.dumps(dialogues, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "dialogue case 'clear-tiny-change': external tracker mutation "
            "requires explicit human gate",
            result.stderr,
        )

    def test_project_config_does_not_store_the_kit_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            config_path = project / "ai-sdlc.yaml"
            config = config_path.read_text(encoding="utf-8")
            if "\nkit_version:" not in config:
                config = config.replace(
                    "\n\ncommands:",
                    "\nkit_version: 0.1.0\n\ncommands:",
                    1,
                )
                config_path.write_text(config, encoding="utf-8")

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "ai-sdlc.yaml: kit_version belongs in .ai/kit.lock.json",
            result.stderr,
        )

    def test_project_config_uses_schema_version_two(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            config_path = project / "ai-sdlc.yaml"
            config = config_path.read_text(encoding="utf-8")
            config = config.replace("schema_version: 2", "schema_version: 1", 1)
            config_path.write_text(config, encoding="utf-8")

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn("ai-sdlc.yaml: schema_version must be 2", result.stderr)

    def test_project_config_declares_progressive_artifact_locations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            config_path = project / "ai-sdlc.yaml"
            config = config_path.read_text(encoding="utf-8")
            for line in (
                "  initiatives: initiatives\n",
                "  context_entry: CONTEXT.md\n",
                "artifact_profiles:\n",
                "  spec: ai-sdlc-v1\n",
                "  adr: ai-sdlc-v1\n",
                "  context: glossary-v1\n",
            ):
                config = config.replace(line, "")
            config_path.write_text(config, encoding="utf-8")

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        for field in (
            "paths.initiatives",
            "paths.context_entry",
            "artifact_profiles.spec",
            "artifact_profiles.adr",
            "artifact_profiles.context",
        ):
            self.assertIn(
                f"ai-sdlc.yaml: missing required schema v2 field {field}",
                result.stderr,
            )

    def test_behavior_case_references_an_existing_dialogue(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            behavior_path = project / "evals" / "behavior-cases.json"
            behavior = json.loads(behavior_path.read_text(encoding="utf-8"))
            behavior["cases"][0]["dialogue_id"] = "missing-dialogue"
            behavior_path.write_text(
                json.dumps(behavior, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "behavior case references unknown dialogue 'missing-dialogue'",
            result.stderr,
        )

    def test_required_artifact_templates_ship_with_the_kit(self) -> None:
        required_paths = (
            ".ai/ARTIFACTS.md",
            ".ai/templates/CONTEXT.md",
            ".ai/templates/CONTEXT-MAP.md",
            ".ai/templates/adr.md",
            ".ai/templates/initiative-map.md",
            "specs/_template/spec.md",
            "specs/_template/plan.md",
            "specs/_template/tasks.md",
            "specs/_template/verification.md",
        )
        for relative_path in required_paths:
            with self.subTest(path=relative_path):
                with tempfile.TemporaryDirectory() as temp_dir:
                    project = self.copy_template(temp_dir)
                    (project / relative_path).unlink()

                    result = self.run_validator(project)

                self.assertEqual(1, result.returncode)
                self.assertIn(
                    f"{relative_path}: required artifact guidance is missing",
                    result.stderr,
                )

    def test_installed_walkthrough_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            walkthrough = project / ".ai" / "README.md"
            if walkthrough.exists():
                walkthrough.unlink()

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            ".ai/README.md: generated developer walkthrough is missing",
            result.stderr,
        )

    def test_validator_uses_configured_spec_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            config_path = project / "ai-sdlc.yaml"
            config = config_path.read_text(encoding="utf-8").replace(
                "  specs: specs",
                "  specs: product/specifications",
                1,
            )
            config_path.write_text(config, encoding="utf-8")
            specs = project / "product" / "specifications"
            shutil.copytree(project / "specs" / "_template", specs / "_template")
            feature = specs / "team-invitations"
            feature.mkdir()
            (feature / "spec.md").write_text(
                "# Feature specification: team invitations\n",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "product/specifications/team-invitations/spec.md requires verification.md",
            result.stderr,
        )

    def test_validator_uses_configured_decision_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            config_path = project / "ai-sdlc.yaml"
            config = config_path.read_text(encoding="utf-8").replace(
                "  decisions: docs/adr",
                "  decisions: architecture/decisions",
                1,
            )
            config_path.write_text(config, encoding="utf-8")
            decisions = project / "architecture" / "decisions"
            decisions.mkdir(parents=True)
            (decisions / "0001-use-http.md").write_text(
                """\
---
status: active
supersedes: []
superseded_by: []
---

# Use HTTP
""",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "architecture/decisions/0001-use-http.md: invalid ADR status 'active'",
            result.stderr,
        )

    def test_validator_uses_configured_initiative_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            config_path = project / "ai-sdlc.yaml"
            config = config_path.read_text(encoding="utf-8").replace(
                "  initiatives: initiatives",
                "  initiatives: product/initiatives",
                1,
            )
            config_path.write_text(config, encoding="utf-8")
            initiative = project / "product" / "initiatives" / "platform"
            initiative.mkdir(parents=True)
            (initiative / "map.md").write_text(
                """\
---
status: active
---

# Initiative: platform

## Decision tracks

- Identity.
""",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "product/initiatives/platform/map.md: active initiative requires "
            "'## Next branch'",
            result.stderr,
        )

    def test_dialogue_source_numbers_can_extend_sequentially(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            dialogues_path = project / "evals" / "dialogue-cases.json"
            dialogues = json.loads(dialogues_path.read_text(encoding="utf-8"))
            extra = dict(dialogues["cases"][-1])
            extra["id"] = "future-dialogue"
            extra["source_dialogue"] = len(dialogues["cases"]) + 1
            dialogues["cases"].append(extra)
            dialogues_path.write_text(
                json.dumps(dialogues, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(0, result.returncode, result.stderr)

    def test_every_skill_has_two_positive_and_negative_routing_cases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = self.copy_template(temp_dir)
            routing_path = project / "evals" / "routing-cases.json"
            routing = json.loads(routing_path.read_text(encoding="utf-8"))
            positive_cases = [
                case for case in routing["cases"] if "learn" in case["invoke"]
            ]
            positive_cases[0]["invoke"].remove("learn")
            routing_path.write_text(
                json.dumps(routing, indent=2) + "\n",
                encoding="utf-8",
            )

            result = self.run_validator(project)

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "routing cases need at least 2 positive cases for learn; found 1",
            result.stderr,
        )

    def test_installed_walkthrough_omits_unimplemented_adoption_command(self) -> None:
        installed_walkthrough = (TEMPLATE / ".ai" / "README.md").read_text(
            encoding="utf-8"
        )

        self.assertNotIn(
            "npx @innovate-x/ai-sdlc@alpha",
            installed_walkthrough,
        )


if __name__ == "__main__":
    unittest.main()
