from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.run_behavior_evals import evaluate_turn, run


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_behavior_evals.py"
RESULT_SCHEMA = ROOT / "repo-template" / "evals" / "behavior-result.schema.json"


class RunBehaviorEvalsTests(unittest.TestCase):
    def test_subprocess_output_is_decoded_as_utf8(self) -> None:
        result = run(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write('\\u009d'.encode('utf-8'))",
            ],
            ROOT,
        )

        self.assertEqual(0, result.returncode)
        self.assertEqual("\u009d", result.stdout)

    def test_result_schema_uses_ai_sdlc_semantic_enums(self) -> None:
        schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))

        self.assertEqual(
            [
                "inspect",
                "shape",
                "plan",
                "implement",
                "diagnose",
                "initiative",
                "finish",
                "learn",
                "update",
            ],
            schema["properties"]["visible_modes"]["items"]["enum"],
        )
        self.assertEqual(
            [
                "ready",
                "adopted",
                "accepted-decision",
                "mapped",
                "diagnosed",
                "needs-human-decision",
                "awaiting_product_decision",
                "awaiting-spec-acceptance",
                "committed",
                "resumed",
                "conflict",
            ],
            schema["properties"]["terminal_state"]["enum"],
        )

    def test_forbidden_commands_use_observed_events_not_self_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "agent-result.json"
            result_path.write_text(
                json.dumps(
                    {
                        "scenario_id": "finish-before-commit",
                        "visible_modes": ["finish"],
                        "route": ["finish"],
                        "questions_asked": [],
                        "human_gates": [],
                        "commands_run": ["git commit"],
                        "terminal_state": "committed",
                        "summary": "Committed locally.",
                    }
                ),
                encoding="utf-8",
            )
            result = evaluate_turn(
                "finish-before-commit",
                {
                    "expected_visible_modes": ["finish"],
                    "expected_terminal_state": "committed",
                    "maximum_questions": 0,
                    "allowed_changes": [],
                    "allow_commit": True,
                    "allowed_commit_changes": [],
                    "forbidden_command_terms": ["push"],
                },
                subprocess.CompletedProcess([], 0, "", ""),
                result_path,
                [],
                2,
                [],
                ["git push origin main"],
            )

        self.assertFalse(result["passed"])
        self.assertIn(
            "agent attempted forbidden commands: ['push']",
            result["violations"],
        )

    def test_prompt_defines_the_global_semantic_vocabulary_without_answers(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fake_agent = temp / "fake_agent.py"
            fake_agent.write_text(
                textwrap.dedent(
                    """\
                    import json
                    import sys
                    from pathlib import Path

                    prompt = sys.argv[-1]
                    required_phrases = [
                        "AI-SDLC semantic labels",
                        "not Codex UI or message-channel labels",
                        "visible_modes",
                        "terminal_state",
                    ]
                    missing = [
                        phrase for phrase in required_phrases
                        if phrase not in prompt
                    ]
                    if missing:
                        raise SystemExit(f"missing semantic guidance: {missing}")
                    leaked_answers = [
                        "expected semantic visible_modes",
                        "terminal_state is one of",
                    ]
                    found = [phrase for phrase in leaked_answers if phrase in prompt]
                    if found:
                        raise SystemExit(f"prompt leaked expected answers: {found}")
                    schema = json.loads(
                        Path(
                            sys.argv[sys.argv.index("--output-schema") + 1]
                        ).read_text(encoding="utf-8")
                    )
                    if schema["properties"]["visible_modes"]["items"]["enum"] != [
                        "inspect", "shape", "plan", "implement", "diagnose",
                        "initiative", "finish", "learn", "update"
                    ]:
                        raise SystemExit("turn schema must retain the global modes")
                    if schema["properties"]["terminal_state"]["enum"] != [
                        "ready", "adopted", "accepted-decision", "mapped",
                        "diagnosed", "needs-human-decision",
                        "awaiting_product_decision", "awaiting-spec-acceptance",
                        "committed", "resumed", "conflict"
                    ]:
                        raise SystemExit("turn schema must retain the global states")
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

        self.assertEqual(0, result.returncode, result.stderr)

    def test_global_policy_precedes_exec_and_preserves_requested_sandbox(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fake_agent = temp / "fake_agent.py"
            fake_agent.write_text(
                textwrap.dedent(
                    """\
                    import json
                    import sys
                    from pathlib import Path

                    exec_index = sys.argv.index("exec")
                    approval_index = sys.argv.index("--ask-for-approval")
                    sandbox_index = sys.argv.index("--sandbox")
                    if approval_index >= exec_index or sandbox_index >= exec_index:
                        raise SystemExit("global policy must precede exec")
                    if sys.argv[approval_index + 1] != "never":
                        raise SystemExit("approval policy must be never")
                    if sys.argv[sandbox_index + 1] != "read-only":
                        raise SystemExit("requested sandbox was not preserved")
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

        self.assertEqual(0, result.returncode, result.stderr)

    def test_fixture_copy_omits_python_cache_artifacts(self) -> None:
        fixture_source = ROOT / "tests" / "fixtures" / "brownfield-mini" / "src"
        cache_dir = fixture_source / "__pycache__"
        cache_dir.mkdir(exist_ok=True)
        cache_marker = cache_dir / "behavior_eval_copy_test.pyc"
        stray_marker = fixture_source / "behavior_eval_copy_test.pyc"
        cache_marker.write_bytes(b"cache marker")
        stray_marker.write_bytes(b"stray bytecode marker")
        try:
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
                        copied = [
                            workspace / "src" / "__pycache__"
                            / "behavior_eval_copy_test.pyc",
                            workspace / "src" / "behavior_eval_copy_test.pyc",
                        ]
                        if any(path.exists() for path in copied):
                            raise SystemExit("fixture copied Python cache artifacts")
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
        finally:
            cache_marker.unlink(missing_ok=True)
            stray_marker.unlink(missing_ok=True)

        self.assertEqual(0, result.returncode, result.stderr)

    def test_transcript_records_the_prompt_and_redacted_structured_response(
        self,
    ) -> None:
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
                    output = Path(sys.argv[sys.argv.index("-o") + 1])
                    output.write_text(json.dumps({
                        "scenario_id": "repository-overview",
                        "visible_modes": ["inspect"],
                        "route": ["develop", "inspect repository"],
                        "questions_asked": [],
                        "human_gates": [],
                        "commands_run": [str(workspace / "README.md")],
                        "terminal_state": "ready",
                        "summary": f"Inspected {workspace} without editing."
                    }), encoding="utf-8")
                    print(json.dumps({
                        "type": "item.completed",
                        "item": {
                            "type": "command_execution",
                            "command": f"read {workspace / 'README.md'}",
                            "status": "completed",
                            "exit_code": 0
                        }
                    }))
                    print(f"workspace={workspace}", file=sys.stderr)
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
            transcript_text = (output_dir / "transcript.json").read_text(
                encoding="utf-8"
            )
            transcript = json.loads(transcript_text)
            event_text = (output_dir / "agent-events.jsonl").read_text(
                encoding="utf-8"
            )
            stderr_text = (output_dir / "agent-stderr.txt").read_text(
                encoding="utf-8"
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(1, transcript["schema_version"])
        self.assertEqual("repository-overview", transcript["scenario_id"])
        self.assertTrue(transcript["redacted"])
        self.assertEqual(
            ["human", "assistant"],
            [message["role"] for message in transcript["messages"]],
        )
        self.assertIn(
            "Give me a read-only overview of this repository",
            transcript["messages"][0]["content"],
        )
        self.assertEqual(
            "ready",
            transcript["messages"][1]["content"]["terminal_state"],
        )
        self.assertNotIn(str(temp), transcript_text)
        self.assertIn("<workspace>", transcript_text)
        self.assertNotIn(str(temp), event_text)
        self.assertIn("<workspace>", event_text)
        self.assertNotIn(str(temp), stderr_text)
        self.assertIn("<workspace>", stderr_text)

    def test_report_records_reproducible_run_metadata(self) -> None:
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
            output_dir = temp / "result"

            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--scenario",
                    "repository-overview",
                    "--model",
                    "metadata-test-model",
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
        metadata = report["metadata"]
        self.assertEqual("metadata-test-model", metadata["model"])
        self.assertEqual("read-only", metadata["requested_sandbox"])
        self.assertEqual("explicit-command", metadata["codex"]["selection"])
        self.assertEqual(
            [sys.executable, str(fake_agent)],
            metadata["codex"]["command_prefix"],
        )
        self.assertIsNone(metadata["codex"]["package_version"])
        started = datetime.fromisoformat(
            metadata["timing"]["started_at_utc"].replace("Z", "+00:00")
        )
        ended = datetime.fromisoformat(
            metadata["timing"]["ended_at_utc"].replace("Z", "+00:00")
        )
        self.assertEqual(timezone.utc, started.tzinfo)
        self.assertEqual(timezone.utc, ended.tzinfo)
        self.assertGreaterEqual(ended, started)
        self.assertGreaterEqual(metadata["timing"]["duration_seconds"], 0)
        expected_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        expected_version = json.loads(
            (ROOT / "package.json").read_text(encoding="utf-8")
        )["version"]
        self.assertEqual(expected_commit, metadata["kit_source"]["commit"])
        self.assertEqual(expected_version, metadata["kit_source"]["version"])

    def test_output_reuse_clears_only_known_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            output_dir = temp / "result"
            output_dir.mkdir()
            stale_names = [
                "agent-result.json",
                "turn-2-agent-result.json",
                "turn-2-agent-events.jsonl",
                "turn-2-agent-stderr.txt",
            ]
            for name in stale_names:
                (output_dir / name).write_text("stale\n", encoding="utf-8")
            preserved = output_dir / "keep-me.txt"
            preserved.write_text("user-owned\n", encoding="utf-8")

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

            self.assertFalse((output_dir / "agent-result.json").exists())
            for name in stale_names[1:]:
                self.assertFalse((output_dir / name).exists())
            self.assertEqual(
                "user-owned\n",
                preserved.read_text(encoding="utf-8"),
            )

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "agent did not produce a structured result",
            report["violations"],
        )

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
                    exec_index = sys.argv.index("exec")
                    approval_index = sys.argv.index("--ask-for-approval")
                    sandbox_index = sys.argv.index("--sandbox")
                    if approval_index >= exec_index or sandbox_index >= exec_index:
                        raise SystemExit("global policy must precede exec")
                    if sys.argv[approval_index + 1] != "never":
                        raise SystemExit("approval policy must be never")
                    if sys.argv[sandbox_index + 1] != "read-only":
                        raise SystemExit("requested sandbox was not preserved")
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
            report = json.loads(
                (output_dir / "report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(
            0,
            result.returncode,
            f"{result.stderr}\n{agent_stderr}",
        )
        self.assertEqual(
            "npx-package",
            report["metadata"]["codex"]["selection"],
        )
        self.assertEqual(
            "0.145.0",
            report["metadata"]["codex"]["package_version"],
        )
        self.assertIn(
            "@openai/codex@0.145.0",
            report["metadata"]["codex"]["command_prefix"],
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
                    exec_index = sys.argv.index("exec")
                    approval_index = sys.argv.index("--ask-for-approval")
                    sandbox_index = sys.argv.index("--sandbox")
                    if approval_index >= exec_index or sandbox_index >= exec_index:
                        raise SystemExit("global policy must precede exec")
                    if sys.argv[approval_index + 1] != "never":
                        raise SystemExit("approval policy must be never")
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
            report = json.loads(
                (output_dir / "report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "installed-cli",
            report["metadata"]["codex"]["selection"],
        )

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

    def test_tiny_change_fails_when_agent_reports_ready_without_editing(self) -> None:
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
                        "scenario_id": "clear-tiny-change",
                        "visible_modes": ["implement", "finish"],
                        "route": ["develop", "implement-slice", "finish"],
                        "questions_asked": [],
                        "human_gates": [],
                        "commands_run": [],
                        "terminal_state": "ready",
                        "summary": "Could not edit the read-only workspace."
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

        self.assertEqual(1, result.returncode)
        self.assertIn(
            "required file changes are missing: "
            "['src/settings_dialog.py', 'tests/test_settings_dialog.py']",
            report["violations"],
        )

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
                        exec_index = sys.argv.index("exec")
                        approval_index = sys.argv.index("--ask-for-approval")
                        sandbox_index = sys.argv.index("--sandbox")
                        if approval_index >= exec_index or sandbox_index >= exec_index:
                            raise SystemExit("resumed global policy must precede exec")
                        if sys.argv[approval_index + 1] != "never":
                            raise SystemExit("resumed approval policy must be never")
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
            transcript = json.loads(
                (output_dir / "transcript.json").read_text(encoding="utf-8")
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
        self.assertEqual(
            ["human", "assistant", "human", "assistant"],
            [message["role"] for message in transcript["messages"]],
        )
        self.assertIn(
            "Add team invitations.",
            transcript["messages"][0]["content"],
        )
        self.assertEqual(
            "awaiting_product_decision",
            transcript["messages"][1]["content"]["terminal_state"],
        )
        self.assertIn(
            "Invitations expire after 72 hours",
            transcript["messages"][2]["content"],
        )
        self.assertEqual(
            "awaiting-spec-acceptance",
            transcript["messages"][3]["content"]["terminal_state"],
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
