from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_behavior_evals.py"


class RunBehaviorEvalsTests(unittest.TestCase):
    def test_missing_agent_command_produces_a_failure_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenario",
                    "repository-overview",
                    "--agent-command",
                    str(temp / "missing-agent"),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            report = json.loads(
                (output_dir / "report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(1, result.returncode)
        self.assertIn("agent exited with status 127", report["violations"])
        self.assertIn(
            "agent did not produce a structured result",
            report["violations"],
        )

    @unittest.skipUnless(os.name == "nt", "Windows npx command-shim behavior")
    def test_codex_package_version_runs_through_npx(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fake_agent = temp / "fake_agent.py"
            fake_agent.write_text(
                textwrap.dedent(
                    """\
                    import json
                    import sys
                    from pathlib import Path

                    if "@openai/codex@0.145.0" not in sys.argv:
                        raise SystemExit("expected pinned Codex package")
                    output = Path(sys.argv[sys.argv.index("-o") + 1])
                    output.write_text(json.dumps({
                        "scenario_id": "repository-overview",
                        "visible_modes": ["inspect"],
                        "route": ["develop", "inspect repository"],
                        "questions_asked": [],
                        "human_gates": [],
                        "commands_run": ["read repository files"],
                        "terminal_state": "ready",
                        "summary": "Explained without editing."
                    }), encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )
            shim_dir = temp / "command shims"
            shim_dir.mkdir()
            (shim_dir / "npx.cmd").write_text(
                '@"%PYTHON_EXE%" "%FAKE_AGENT%" %*\n',
                encoding="utf-8",
            )
            output_dir = temp / "result"
            environment = os.environ.copy()
            environment["PATH"] = f"{shim_dir}{os.pathsep}{environment['PATH']}"
            environment["PYTHON_EXE"] = sys.executable
            environment["FAKE_AGENT"] = str(fake_agent)

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenario",
                    "repository-overview",
                    "--codex-package-version",
                    "0.145.0",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            agent_stderr = (output_dir / "agent-stderr.txt").read_text(
                encoding="utf-8"
            )

        self.assertEqual(
            0,
            result.returncode,
            f"{result.stderr}\n{agent_stderr}",
        )

    @unittest.skipUnless(os.name == "nt", "Windows command-shim behavior")
    def test_default_agent_command_uses_the_windows_cmd_shim(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fake_agent = temp / "fake_agent.py"
            fake_agent.write_text(
                textwrap.dedent(
                    """\
                    import json
                    import sys
                    from pathlib import Path

                    if "--ignore-user-config" not in sys.argv:
                        raise SystemExit("runner must isolate user config")
                    if sys.argv[sys.argv.index("-m") + 1] != "gpt-5.6-terra":
                        raise SystemExit("runner must select the evaluation model")
                    output = Path(sys.argv[sys.argv.index("-o") + 1])
                    output.write_text(json.dumps({
                        "scenario_id": "repository-overview",
                        "visible_modes": ["inspect"],
                        "route": ["develop", "inspect repository", "explain"],
                        "questions_asked": [],
                        "human_gates": [],
                        "commands_run": ["read repository files"],
                        "terminal_state": "ready",
                        "summary": "Explained without editing."
                    }), encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )
            (temp / "codex.cmd").write_text(
                '@"%PYTHON_EXE%" "%FAKE_AGENT%" %*\n',
                encoding="utf-8",
            )
            output_dir = temp / "result"
            environment = os.environ.copy()
            environment["PATH"] = f"{temp}{os.pathsep}{environment['PATH']}"
            environment["PYTHON_EXE"] = sys.executable
            environment["FAKE_AGENT"] = str(fake_agent)

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenario",
                    "repository-overview",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(0, result.returncode, result.stderr)

    def test_read_only_overview_passes_when_agent_changes_nothing(self) -> None:
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
                    output.write_text(json.dumps({
                        "scenario_id": "repository-overview",
                        "visible_modes": ["inspect"],
                        "route": ["develop", "inspect repository", "explain"],
                        "questions_asked": [],
                        "human_gates": [],
                        "commands_run": ["read repository files"],
                        "terminal_state": "ready",
                        "summary": "Explained the repository without editing it."
                    }), encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenario",
                    "repository-overview",
                    "--agent-command",
                    sys.executable,
                    str(fake_agent),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            report = json.loads(
                (output_dir / "report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(report["passed"])
        self.assertEqual([], report["changed_files"])
        self.assertEqual([], report["violations"])

    def test_read_only_overview_fails_when_agent_changes_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fake_agent = temp / "fake_agent.py"
            fake_agent.write_text(
                textwrap.dedent(
                    """\
                    import json
                    import sys
                    from pathlib import Path

                    workspace = Path(sys.argv[sys.argv.index("-C") + 1])
                    (workspace / "README.md").write_text(
                        "unauthorized edit\\n",
                        encoding="utf-8"
                    )
                    output = Path(sys.argv[sys.argv.index("-o") + 1])
                    output.write_text(json.dumps({
                        "scenario_id": "repository-overview",
                        "visible_modes": ["inspect"],
                        "route": ["develop", "inspect repository"],
                        "questions_asked": [],
                        "human_gates": [],
                        "commands_run": ["read repository files"],
                        "terminal_state": "ready",
                        "summary": "Explained the repository."
                    }), encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenario",
                    "repository-overview",
                    "--agent-command",
                    sys.executable,
                    str(fake_agent),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            report = json.loads(
                (output_dir / "report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "unexpected file changes: ['README.md']",
            report["violations"],
        )

    def test_tiny_change_passes_with_only_the_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fake_agent = temp / "fake_agent.py"
            fake_agent.write_text(
                textwrap.dedent(
                    """\
                    import json
                    import sys
                    from pathlib import Path

                    workspace = Path(sys.argv[sys.argv.index("-C") + 1])
                    dialog = workspace / "src" / "settings_dialog.py"
                    dialog.write_text(
                        dialog.read_text(encoding="utf-8").replace(
                            'BUTTON_LABEL = "Save"',
                            'BUTTON_LABEL = "Save changes"'
                        ),
                        encoding="utf-8"
                    )
                    test = workspace / "tests" / "test_settings_dialog.py"
                    test.write_text(
                        test.read_text(encoding="utf-8").replace(
                            '"Save"', '"Save changes"'
                        ),
                        encoding="utf-8"
                    )
                    output = Path(sys.argv[sys.argv.index("-o") + 1])
                    output.write_text(json.dumps({
                        "scenario_id": "clear-tiny-change",
                        "visible_modes": ["implement", "finish"],
                        "route": [
                            "develop",
                            "implement from inline brief",
                            "adaptive finish"
                        ],
                        "questions_asked": [],
                        "human_gates": [],
                        "commands_run": [
                            "python -m unittest discover -s tests"
                        ],
                        "terminal_state": "ready",
                        "summary": "Changed the label and its focused test."
                    }), encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenario",
                    "clear-tiny-change",
                    "--agent-command",
                    sys.executable,
                    str(fake_agent),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            report = json.loads(
                (output_dir / "report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(report["passed"])
        self.assertEqual(
            ["src/settings_dialog.py", "tests/test_settings_dialog.py"],
            report["changed_files"],
        )
        self.assertEqual([], report["violations"])

    def test_diagnosis_only_passes_without_product_changes(self) -> None:
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
                    output.write_text(json.dumps({
                        "scenario_id": "diagnose-checkout-retries",
                        "visible_modes": ["diagnose"],
                        "route": ["develop", "diagnose failure"],
                        "questions_asked": [],
                        "human_gates": [],
                        "commands_run": [
                            "python -m unittest discover -s tests"
                        ],
                        "terminal_state": "diagnosed",
                        "summary": "Retry tokens are counted as independent charges."
                    }), encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenario",
                    "diagnose-checkout-retries",
                    "--agent-command",
                    sys.executable,
                    str(fake_agent),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            report = json.loads(
                (output_dir / "report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(report["passed"])
        self.assertEqual([], report["changed_files"])
        self.assertEqual([], report["violations"])

    def test_fuzzy_feature_requires_one_material_question(self) -> None:
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
                    output.write_text(json.dumps({
                        "scenario_id": "fuzzy-team-invitations",
                        "visible_modes": ["inspect", "shape"],
                        "route": ["develop", "inspect facts", "shape change"],
                        "questions_asked": [],
                        "human_gates": [],
                        "commands_run": ["read repository files"],
                        "terminal_state": "needs-human-decision",
                        "summary": "Stopped before implementation."
                    }), encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenario",
                    "fuzzy-team-invitations",
                    "--agent-command",
                    sys.executable,
                    str(fake_agent),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            report = json.loads(
                (output_dir / "report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(1, result.returncode)
        self.assertFalse(report["passed"])
        self.assertIn("agent asked fewer questions than required", report["violations"])
        self.assertEqual([], report["changed_files"])

    def test_fuzzy_feature_resumes_for_the_spec_draft(self) -> None:
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
                    if "resume" not in sys.argv:
                        print(json.dumps({
                            "type": "thread.started",
                            "thread_id": "fake-thread"
                        }))
                        result = {
                            "scenario_id": "fuzzy-team-invitations",
                            "visible_modes": ["inspect", "shape"],
                            "route": ["develop", "inspect facts", "shape change"],
                            "questions_asked": [
                                "Should Owners and Admins be allowed to invite?"
                            ],
                            "human_gates": ["confirm invitation policy"],
                            "commands_run": ["read repository files"],
                            "terminal_state": "awaiting_product_decision",
                            "summary": "Asked one product-policy question."
                        }
                    else:
                        if sys.argv[sys.argv.index("--sandbox") + 1] != "workspace-write":
                            raise SystemExit("expected resumed sandbox mode")
                        follow_up = sys.stdin.read()
                        if "Invitations expire after 72 hours" not in follow_up:
                            raise SystemExit("expected follow-up prompt on stdin")
                        feature = Path.cwd() / "specs" / "team-invitations"
                        feature.mkdir()
                        (feature / "spec.md").write_text(
                            "---\\nstatus: draft\\n---\\n\\n# Team invitations\\n",
                            encoding="utf-8"
                        )
                        (feature / "verification.md").write_text(
                            "# Verification: team invitations\\n",
                            encoding="utf-8"
                        )
                        result = {
                            "scenario_id": "fuzzy-team-invitations",
                            "visible_modes": ["shape"],
                            "route": ["shape change", "draft spec"],
                            "questions_asked": [],
                            "human_gates": ["accept the behavioral spec"],
                            "commands_run": [],
                            "terminal_state": "awaiting-spec-acceptance",
                            "summary": "Drafted the spec without implementing."
                        }
                    output.write_text(json.dumps(result), encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenario",
                    "fuzzy-team-invitations",
                    "--all-turns",
                    "--agent-command",
                    sys.executable,
                    str(fake_agent),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            report = json.loads(
                (output_dir / "report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(report["passed"])
        self.assertEqual(2, len(report["turns"]))
        self.assertEqual([], report["turns"][0]["changed_files"])
        self.assertEqual(
            [
                "specs/team-invitations/spec.md",
                "specs/team-invitations/verification.md",
            ],
            report["turns"][1]["changed_files"],
        )
        self.assertIn(
            "accept the behavioral spec",
            report["turns"][1]["agent_result"]["human_gates"],
        )

    def test_finish_passes_after_one_authorized_local_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fake_agent = temp / "fake_agent.py"
            fake_agent.write_text(
                textwrap.dedent(
                    """\
                    import json
                    import subprocess
                    import sys
                    from pathlib import Path

                    workspace = Path(sys.argv[sys.argv.index("-C") + 1])
                    subprocess.run(
                        ["git", "add", "src/settings_dialog.py"],
                        cwd=workspace,
                        check=True
                    )
                    subprocess.run(
                        ["git", "commit", "--quiet", "-m", "Update save label"],
                        cwd=workspace,
                        check=True
                    )
                    output = Path(sys.argv[sys.argv.index("-o") + 1])
                    output.write_text(json.dumps({
                        "scenario_id": "finish-before-commit",
                        "visible_modes": ["finish"],
                        "route": [
                            "finish",
                            "deterministic checks",
                            "correctness review",
                            "authorized commit"
                        ],
                        "questions_asked": [],
                        "human_gates": ["authorize commit"],
                        "commands_run": [
                            "python -m unittest discover -s tests",
                            "git commit"
                        ],
                        "terminal_state": "committed",
                        "summary": "Verified and committed the prepared change."
                    }), encoding="utf-8")
                    """
                ),
                encoding="utf-8",
            )
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenario",
                    "finish-before-commit",
                    "--agent-command",
                    sys.executable,
                    str(fake_agent),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            report = json.loads(
                (output_dir / "report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(report["passed"])
        self.assertEqual(2, report["commit_count"])
        self.assertEqual(["src/settings_dialog.py"], report["committed_files"])
        self.assertEqual([], report["changed_files"])


if __name__ == "__main__":
    unittest.main()
