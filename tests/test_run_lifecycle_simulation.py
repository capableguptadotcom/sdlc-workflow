from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts.run_lifecycle_simulation import (
    artifact_delta,
    artifact_inventory,
    comparison,
    developer_prompt,
    evaluate_phase_gate,
    installed_kit_version,
    operational_verification,
    parse_command_events,
    redact,
    redact_jsonl,
    snapshot_delta,
    verification_passed,
    workspace_snapshot,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_lifecycle_simulation.py"
SCENARIO = ROOT / "simulations" / "pantry-ledger" / "scenario.json"
ROLLBACK_ORACLE = ROOT / "scripts" / "pantry_ledger_rollback_acceptance.mjs"


class RunLifecycleSimulationTests(unittest.TestCase):
    def test_redaction_does_not_corrupt_relative_kit_paths(self) -> None:
        text = "lock=.ai/kit.lock.json source=/kit/scripts/runner.py"

        redacted = redact(text, [Path("/kit")])

        self.assertIn(".ai/kit.lock.json", redacted)
        self.assertIn("<local-path-1>/scripts/runner.py", redacted)

    def test_json_event_redaction_handles_escaped_windows_paths(self) -> None:
        local_path = Path(r"C:\Users\Example\secret-workspace")
        events = json.dumps({"path": str(local_path)}) + "\n"

        redacted = redact_jsonl(events, [local_path])

        self.assertNotIn("Example", redacted)
        self.assertEqual({"path": "<local-path-1>"}, json.loads(redacted))

    def test_every_release_gate_is_required(self) -> None:
        green = {
            key: {"status": 0}
            for key in (
                "package_json",
                "npm_test",
                "npm_lint",
                "npm_build",
                "npm_security",
                "npm_pack_dry_run",
                "git_diff_check",
                "external_acceptance",
                "initial_release_checkout",
                "initial_release_tests",
                "initial_release_acceptance",
                "final_clean_release_checkout",
                "final_clean_release_tests",
                "final_clean_release_acceptance",
                "cross_version_rollback_acceptance",
                "operations_runbook",
                "lifecycle_invariants",
            )
        }
        self.assertTrue(verification_passed(green, "baseline"))
        for gate in green:
            with self.subTest(gate=gate):
                red = {**green, gate: {"status": 1}}
                self.assertFalse(verification_passed(red, "baseline"))
        self.assertFalse(
            verification_passed({"external_acceptance": {"status": 0}}, "baseline")
        )
        self.assertFalse(verification_passed(green, "with-kit"))
        self.assertTrue(
            verification_passed(
                {
                    **green,
                    "kit_validator": {"status": 0},
                    "kit_rerun": {"status": 0},
                },
                "with-kit",
            )
        )

    def test_operational_verification_names_missing_rollback_checkpoints(
        self,
    ) -> None:
        cases = (
            ({}, "missing rollback checkpoints: initial_release, operations_handoff"),
            (
                {"initial_release": "present", "operations_handoff": ""},
                "missing rollback checkpoints: operations_handoff",
            ),
            (
                {"initial_release": "", "operations_handoff": "present"},
                "missing rollback checkpoints: initial_release",
            ),
        )
        for checkpoints, expected_error in cases:
            with self.subTest(checkpoints=checkpoints):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = Path(temp_dir)
                    workspace = root / "workspace"
                    arm_root = root / "arm"
                    workspace.mkdir()
                    arm_root.mkdir()

                    evidence = operational_verification(
                        workspace,
                        arm_root,
                        checkpoints,
                    )

                rollback = evidence["cross_version_rollback_acceptance"]
                self.assertEqual(2, rollback["status"])
                self.assertEqual(expected_error, rollback["stderr"])

    def test_missing_operations_handoff_reports_a_missing_runbook_checkpoint(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            arm_root = root / "arm"
            workspace.mkdir()
            arm_root.mkdir()

            evidence = operational_verification(
                workspace,
                arm_root,
                {"initial_release": "present"},
            )

        runbook = evidence["operations_runbook"]
        self.assertEqual(2, runbook["status"])
        self.assertEqual(
            "missing checkpoint: operations_handoff",
            runbook["stderr"],
        )

    def test_comparison_distinguishes_test_files_from_test_cases(self) -> None:
        reports = []
        for arm in ("baseline", "with-kit"):
            reports.append(
                {
                    "schema_version": 1,
                    "scenario_id": "comparison-test",
                    "arm": arm,
                    "passed": True,
                    "full_lifecycle_completed": True,
                    "turns": [],
                    "duration_seconds": 1,
                    "commit_delta": 0,
                    "artifacts_added": {
                        "specifications": [],
                        "plans": [],
                        "verification": [],
                        "handoffs": [],
                        "tests": [
                            "test/first.test.js",
                            "test/second.test.js",
                        ],
                    },
                    "final_verification": {},
                }
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            comparison(reports, output_root)
            payload = json.loads(
                (output_root / "comparison.json").read_text(encoding="utf-8")
            )
            markdown = (output_root / "comparison.md").read_text(
                encoding="utf-8"
            )

        self.assertEqual(1, payload["schema_version"])
        for metrics in payload["arms"].values():
            self.assertEqual(2, metrics["test_files_added"])
            self.assertEqual(2, metrics["tests"])
        self.assertIn("not test cases", payload["interpretation_note"])
        self.assertIn("| test files added | 2 | 2 |", markdown)
        self.assertNotIn("| tests |", markdown)

    def test_every_scenario_turn_resolves_its_developer_prompt(self) -> None:
        scenario = json.loads(SCENARIO.read_text(encoding="utf-8"))

        prompts = [
            developer_prompt(turn, scenario)
            for turns in scenario["arms"].values()
            for turn in turns
        ]

        self.assertEqual(16, len(prompts))
        self.assertTrue(all(prompt.strip() for prompt in prompts))

    def test_report_version_comes_from_the_installed_candidate_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            lock = workspace / ".ai" / "kit.lock.json"
            lock.parent.mkdir(parents=True)
            lock.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kit_version": "0.1.0-alpha.1",
                    }
                ),
                encoding="utf-8",
            )

            version = installed_kit_version(workspace)

        self.assertEqual("0.1.0-alpha.1", version)

    def test_full_run_requires_an_explicit_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "result"
            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--arm",
                    "baseline",
                    "--agent-command",
                    "unused-agent",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(2, result.returncode)
        self.assertIn("requires an explicit --sandbox", result.stderr)

    def test_artifact_inventory_excludes_kit_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            template = workspace / "specs" / "_template" / "spec.md"
            specification = workspace / "specs" / "pantry-ledger" / "spec.md"
            template.parent.mkdir(parents=True)
            specification.parent.mkdir(parents=True)
            template.write_text("template", encoding="utf-8")
            specification.write_text("actual", encoding="utf-8")

            inventory = artifact_inventory(workspace)

        self.assertEqual(
            ["specs/pantry-ledger/spec.md"],
            inventory["specifications"],
        )

    def test_phase_status_gate_excludes_kit_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            template = workspace / "specs" / "_template" / "spec.md"
            specification = workspace / "specs" / "pantry-ledger" / "spec.md"
            template.parent.mkdir(parents=True)
            specification.parent.mkdir(parents=True)
            template.write_text("---\nstatus: draft\n---\n", encoding="utf-8")
            specification.write_text(
                "---\nstatus: accepted\n---\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "init", "--quiet"], cwd=workspace, check=True)
            subprocess.run(
                ["git", "config", "user.name", "Test"],
                cwd=workspace,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=workspace,
                check=True,
            )
            subprocess.run(["git", "add", "-A"], cwd=workspace, check=True)
            subprocess.run(
                ["git", "commit", "--quiet", "-m", "fixture"],
                cwd=workspace,
                check=True,
            )
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=workspace,
                text=True,
            ).strip()

            gate = evaluate_phase_gate(
                workspace,
                {"required_status": {"specs/*/spec.md": "accepted"}},
                [],
                commit,
                commit,
                "",
                [],
            )

        self.assertTrue(gate["passed"], gate)

    def test_artifact_delta_counts_only_new_outputs(self) -> None:
        before = {
            "tests": ["test/health.test.mjs"],
            "specifications": [],
        }
        after = {
            "tests": ["test/health.test.mjs", "test/inventory.test.mjs"],
            "specifications": ["specs/pantry-ledger/spec.md"],
        }

        self.assertEqual(
            {
                "tests": ["test/inventory.test.mjs"],
                "specifications": ["specs/pantry-ledger/spec.md"],
            },
            artifact_delta(before, after),
        )

    def test_command_events_collapse_start_and_completion(self) -> None:
        item = {
            "id": "command-1",
            "type": "command_execution",
            "command": "git status --short",
        }
        events = "\n".join(
            [
                json.dumps(
                    {
                        "type": "item.started",
                        "item": {**item, "status": "in_progress"},
                    }
                ),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            **item,
                            "status": "completed",
                            "exit_code": 0,
                        },
                    }
                ),
            ]
        )

        commands = parse_command_events(events, [])

        self.assertEqual(1, len(commands))
        self.assertEqual(0, commands[0]["exit_code"])

    def test_command_events_preserve_an_unfinished_attempt(self) -> None:
        events = json.dumps(
            {
                "type": "item.started",
                "item": {
                    "id": "command-1",
                    "type": "command_execution",
                    "command": "npm test",
                    "status": "in_progress",
                    "exit_code": None,
                },
            }
        )

        commands = parse_command_events(events, [])

        self.assertEqual(
            [
                {
                    "command": "npm test",
                    "status": "interrupted",
                    "exit_code": None,
                }
            ],
            commands,
        )

    def test_phase_gate_rejects_an_interrupted_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            gate = evaluate_phase_gate(
                Path(temp_dir),
                {},
                [],
                "",
                "",
                "",
                [
                    {
                        "command": "npm test",
                        "status": "interrupted",
                        "exit_code": None,
                    }
                ],
            )

        self.assertFalse(gate["passed"], gate)

    def test_rollback_oracle_rejects_a_previous_release_that_mutates_data(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            current = root / "current"
            previous = root / "previous"
            (current / "src").mkdir(parents=True)
            (previous / "src").mkdir(parents=True)
            (current / "src" / "server.js").write_text(
                textwrap.dedent(
                    """\
                    import { createServer } from "node:http";
                    import { existsSync, readFileSync, writeFileSync } from "node:fs";

                    const file = process.env.PANTRY_DATA_FILE;
                    const data = existsSync(file)
                      ? JSON.parse(readFileSync(file, "utf8"))
                      : { items: [], idempotencyRecords: [] };
                    const send = (response, status, body) => {
                      response.writeHead(status, { "content-type": "application/json" });
                      response.end(JSON.stringify(body));
                    };
                    createServer((request, response) => {
                      if (request.method === "GET" && request.url === "/health") {
                        return send(response, 200, { status: "ok" });
                      }
                      if (request.method === "GET" && request.url === "/api/inventory") {
                        return send(response, 200, {
                          items: data.items.map((item) => ({
                            ...item,
                            lowStock: item.quantity <= item.lowStockThreshold,
                          })),
                        });
                      }
                      if (request.method === "POST" && request.url === "/api/movements") {
                        let raw = "";
                        request.on("data", (chunk) => { raw += chunk; });
                        request.on("end", () => {
                          const key = request.headers["idempotency-key"];
                          const prior = data.idempotencyRecords.find(
                            (record) => record.key === key,
                          );
                          if (prior) return send(response, prior.status, prior.body);
                          const movement = JSON.parse(raw);
                          const item = {
                            name: movement.item,
                            quantity: movement.quantity,
                            lowStockThreshold: 5,
                          };
                          data.items = [item];
                          const body = {
                            item: { ...item, lowStock: false },
                          };
                          data.idempotencyRecords.push({ key, status: 201, body });
                          writeFileSync(file, JSON.stringify(data));
                          send(response, 201, body);
                        });
                        return;
                      }
                      send(response, 404, { error: "not found" });
                    }).listen(Number(process.env.PORT), "127.0.0.1");
                    """
                ),
                encoding="utf-8",
            )
            (previous / "src" / "server.js").write_text(
                textwrap.dedent(
                    """\
                    import { createServer } from "node:http";
                    import { readFileSync, writeFileSync } from "node:fs";

                    const file = process.env.PANTRY_DATA_FILE;
                    const data = JSON.parse(readFileSync(file, "utf8"));
                    writeFileSync(file, `${JSON.stringify(data)}\\n`);
                    const send = (response, status, body) => {
                      response.writeHead(status, { "content-type": "application/json" });
                      response.end(JSON.stringify(body));
                    };
                    createServer((request, response) => {
                      if (request.url === "/health") {
                        return send(response, 200, { status: "ok" });
                      }
                      if (request.url === "/api/inventory") {
                        return send(response, 200, {
                          items: data.items.map((item) => ({
                            ...item,
                            lowStock: item.quantity <= item.lowStockThreshold,
                          })),
                        });
                      }
                      send(response, 404, { error: "not found" });
                    }).listen(Number(process.env.PORT), "127.0.0.1");
                    """
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "node",
                    str(ROLLBACK_ORACLE),
                    str(current),
                    str(previous),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

        self.assertEqual(1, result.returncode, result.stdout)
        self.assertIn(
            "previous release changed the current release data file",
            result.stderr,
        )

    def test_snapshot_delta_is_per_turn_with_prior_uncommitted_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            first = workspace / "first.txt"
            second = workspace / "second.txt"
            first.write_text("already changed\n", encoding="utf-8")
            before = workspace_snapshot(workspace)
            second.write_text("this turn\n", encoding="utf-8")

            changed, patch = snapshot_delta(before, workspace_snapshot(workspace))

        self.assertEqual(["second.txt"], changed)
        self.assertNotIn("first.txt", patch)
        self.assertIn("second.txt", patch)

    def test_baseline_probe_preserves_workspace_and_conversation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fake_agent = temp / "fake_agent.py"
            fake_agent.write_text(
                textwrap.dedent(
                    """\
                    import json
                    import sys
                    from pathlib import Path

                    output = Path(sys.argv[sys.argv.index("-o") + 1])
                    prompt = sys.argv[-1]
                    phase = next(
                        line.split(": ", 1)[1]
                        for line in prompt.splitlines()
                        if line.startswith("Current phase: ")
                    )
                    response = f"Handled {phase} without external effects."
                    output.write_text(response, encoding="utf-8")
                    print(json.dumps({
                        "type": "thread.started",
                        "thread_id": f"fake-{phase}"
                    }))
                    print(json.dumps({
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": response}
                    }))
                    print(json.dumps({
                        "type": "item.completed",
                        "item": {
                            "type": "command_execution",
                            "command": "git status --short",
                            "status": "completed",
                            "exit_code": 0
                        }
                    }))
                    """
                ),
                encoding="utf-8",
            )
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--arm",
                    "baseline",
                    "--turn-limit",
                    "1",
                    "--agent-command",
                    sys.executable,
                    str(fake_agent),
                    "--sandbox",
                    "danger-full-access",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            report = json.loads(
                (output_dir / "baseline" / "report.json").read_text(
                    encoding="utf-8"
                )
            )
            transcript = [
                json.loads(line)
                for line in (
                    output_dir / "baseline" / "transcript.jsonl"
                ).read_text(encoding="utf-8").splitlines()
            ]

            self.assertEqual(
                0,
                result.returncode,
                f"{result.stderr}\n{json.dumps(report, indent=2)}",
            )
            self.assertEqual("baseline", report["arm"])
            self.assertEqual(1, len(report["turns"]))
            self.assertEqual(["human", "assistant"], [
                event["actor"] for event in transcript
            ])
            self.assertTrue((output_dir / "baseline" / "workspace" / ".git").is_dir())
            self.assertTrue(
                (
                    output_dir
                    / "baseline"
                    / "turns"
                    / "01-feature"
                    / "agent-events.jsonl"
                ).is_file()
            )
            self.assertEqual(0, report["final_verification"]["npm_test"]["status"])

    def test_probe_with_only_failed_commands_is_not_a_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fake_agent = temp / "blocked_agent.py"
            fake_agent.write_text(
                textwrap.dedent(
                    """\
                    import json
                    import sys
                    from pathlib import Path

                    output = Path(sys.argv[sys.argv.index("-o") + 1])
                    output.write_text("Blocked before repository access.", encoding="utf-8")
                    print(json.dumps({
                        "type": "item.completed",
                        "item": {
                            "type": "command_execution",
                            "command": "git status --short",
                            "status": "failed",
                            "exit_code": 1
                        }
                    }))
                    """
                ),
                encoding="utf-8",
            )
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--arm",
                    "baseline",
                    "--turn-limit",
                    "1",
                    "--agent-command",
                    sys.executable,
                    str(fake_agent),
                    "--sandbox",
                    "danger-full-access",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            report = json.loads(
                (output_dir / "baseline" / "report.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(1, result.returncode)
        self.assertFalse(report["probe_passed"])
        self.assertFalse(report["passed"])

    def test_noop_full_run_fails_external_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fake_agent = temp / "noop_agent.py"
            fake_agent.write_text(
                textwrap.dedent(
                    """\
                    import sys
                    from pathlib import Path

                    output = Path(sys.argv[sys.argv.index("-o") + 1])
                    output.write_text("No repository changes.", encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--arm",
                    "baseline",
                    "--agent-command",
                    sys.executable,
                    str(fake_agent),
                    "--sandbox",
                    "danger-full-access",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            report = json.loads(
                (output_dir / "baseline" / "report.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(1, result.returncode)
        self.assertFalse(report["passed"])
        self.assertFalse(report["full_lifecycle_completed"])
        self.assertEqual(
            1,
            report["final_verification"]["external_acceptance"]["status"],
        )
        self.assertEqual(report["initial_commit"], report["final_commit"])


if __name__ == "__main__":
    unittest.main()
