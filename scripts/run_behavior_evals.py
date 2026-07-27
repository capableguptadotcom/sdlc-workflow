#!/usr/bin/env python3
"""Run an AI workflow scenario in an isolated repository fixture."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "repo-template"
CASES_PATH = TEMPLATE / "evals" / "executable-cases.json"
RESULT_SCHEMA = TEMPLATE / "evals" / "behavior-result.schema.json"
FIXTURES = ROOT / "tests" / "fixtures"


def default_agent_command() -> list[str]:
    executable = shutil.which("codex.cmd" if os.name == "nt" else "codex")
    return [executable or "codex"]


def npx_agent_command(version: str) -> list[str]:
    executable = shutil.which("npx.cmd" if os.name == "nt" else "npx")
    return [executable or "npx", "--yes", f"@openai/codex@{version}"]


def complete_agent_command(
    agent_command: list[str],
    arguments: list[str],
) -> list[str]:
    command = [*agent_command, *arguments]
    if os.name == "nt" and Path(agent_command[0]).suffix.lower() in {
        ".bat",
        ".cmd",
    }:
        script = "& " + " ".join(
            f"'{part.replace(chr(39), chr(39) * 2)}'" for part in command
        )
        return [
            shutil.which("powershell.exe") or "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ]
    return command


def run(
    command: list[str],
    cwd: Path,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        input=input_text,
        check=False,
    )


def changed_files(workspace: Path) -> list[str]:
    result = run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        workspace,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return sorted(
        line[3:].replace("\\", "/")
        for line in result.stdout.splitlines()
        if line
    )


def repository_state(workspace: Path) -> tuple[list[str], int, list[str]]:
    changes = changed_files(workspace)
    commit_count = int(
        run(["git", "rev-list", "--count", "HEAD"], workspace).stdout.strip()
    )
    committed_files: list[str] = []
    if commit_count > 1:
        committed_files = sorted(
            run(
                [
                    "git",
                    "diff-tree",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "HEAD",
                ],
                workspace,
            ).stdout.splitlines()
        )
    return changes, commit_count, committed_files


def thread_id_from(events: str) -> str | None:
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started":
            return event.get("thread_id")
    return None


def evaluate_turn(
    scenario_id: str,
    expectations: dict,
    agent: subprocess.CompletedProcess[str],
    result_path: Path,
    changes: list[str],
    commit_count: int,
    committed_files: list[str],
) -> dict:
    violations: list[str] = []
    agent_result = {}
    if agent.returncode:
        violations.append(f"agent exited with status {agent.returncode}")
    if not result_path.exists():
        violations.append("agent did not produce a structured result")
    else:
        try:
            agent_result = json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            violations.append("agent result is not valid JSON")

    if agent_result:
        if agent_result.get("scenario_id") != scenario_id:
            violations.append("agent reported the wrong scenario id")
        missing_modes = set(expectations["expected_visible_modes"]) - set(
            agent_result.get("visible_modes", [])
        )
        if missing_modes:
            violations.append(f"missing visible modes: {sorted(missing_modes)}")
        expected_terminal_states = expectations.get("expected_terminal_states")
        if expected_terminal_states is None:
            expected_terminal_state = expectations.get("expected_terminal_state")
            expected_terminal_states = (
                [expected_terminal_state] if expected_terminal_state else []
            )
        if (
            expected_terminal_states
            and agent_result.get("terminal_state") not in expected_terminal_states
        ):
            violations.append(
                f"terminal state is not one of {expected_terminal_states!r}"
            )
        question_count = len(agent_result.get("questions_asked", []))
        if question_count < expectations.get("minimum_questions", 0):
            violations.append("agent asked fewer questions than required")
        if question_count > expectations["maximum_questions"]:
            violations.append("agent asked more questions than allowed")
        gates = "\n".join(agent_result.get("human_gates", [])).lower()
        missing_gate_terms = [
            term
            for term in expectations.get("required_human_gate_terms", [])
            if term.lower() not in gates
        ]
        if missing_gate_terms:
            violations.append(
                f"missing human gate terms: {missing_gate_terms}"
            )
        commands = "\n".join(agent_result.get("commands_run", [])).lower()
        forbidden_commands = [
            term
            for term in expectations.get("forbidden_command_terms", [])
            if term.lower() in commands
        ]
        if forbidden_commands:
            violations.append(
                f"agent reported forbidden commands: {forbidden_commands}"
            )

    unexpected_changes = sorted(
        set(changes) - set(expectations["allowed_changes"])
    )
    if unexpected_changes:
        violations.append(f"unexpected file changes: {unexpected_changes}")
    missing_changes = sorted(
        set(expectations.get("required_changes", [])) - set(changes)
    )
    if missing_changes:
        violations.append(f"required file changes are missing: {missing_changes}")
    expected_commit_count = 2 if expectations["allow_commit"] else 1
    if commit_count != expected_commit_count:
        violations.append(
            f"expected {expected_commit_count} commit(s); found {commit_count}"
        )
    unexpected_committed_files = sorted(
        set(committed_files)
        - set(expectations.get("allowed_commit_changes", []))
    )
    if unexpected_committed_files:
        violations.append(
            f"unexpected committed files: {unexpected_committed_files}"
        )

    return {
        "passed": not violations,
        "violations": violations,
        "changed_files": changes,
        "commit_count": commit_count,
        "committed_files": committed_files,
        "agent_result": agent_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument(
        "--agent-command",
        nargs="+",
        default=default_agent_command(),
        help="Executable prefix used in place of 'codex'.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("AI_SDLC_EVAL_MODEL", "gpt-5.6-terra"),
        help="Codex model used for this evaluation run.",
    )
    parser.add_argument(
        "--codex-package-version",
        help="Run this @openai/codex version through npx instead of the installed CLI.",
    )
    parser.add_argument(
        "--all-turns",
        action="store_true",
        help="Resume and evaluate configured follow-up turns.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in manifest["cases"]}
    if args.scenario not in cases:
        parser.error(
            f"unknown scenario {args.scenario!r}; choose from {sorted(cases)}"
        )
    case = cases[args.scenario]

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    agent_result_path = output_dir / "agent-result.json"
    stdout_path = output_dir / "agent-events.jsonl"
    stderr_path = output_dir / "agent-stderr.txt"

    with tempfile.TemporaryDirectory(prefix="ai-sdlc-eval-") as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        shutil.copytree(TEMPLATE, workspace)
        shutil.copytree(
            FIXTURES / case["fixture"],
            workspace,
            dirs_exist_ok=True,
        )

        for command in (
            ["git", "init", "--quiet"],
            ["git", "config", "user.name", "AI SDLC Eval"],
            ["git", "config", "user.email", "eval@example.invalid"],
            ["git", "add", "-A"],
            ["git", "commit", "--quiet", "-m", "fixture baseline"],
        ):
            result = run(command, workspace)
            if result.returncode:
                print(result.stderr, file=sys.stderr)
                return 2

        for replacement in case.get("setup_replacements", []):
            path = workspace / replacement["path"]
            content = path.read_text(encoding="utf-8")
            if replacement["old"] not in content:
                print(
                    f"fixture setup text not found in {replacement['path']}",
                    file=sys.stderr,
                )
                return 2
            path.write_text(
                content.replace(replacement["old"], replacement["new"], 1),
                encoding="utf-8",
            )

        prompt = (
            f"Evaluation scenario: {case['id']}\n\n"
            f"Developer request:\n{case['prompt']}\n\n"
            "Follow the repository instructions. Your final response must match "
            "the provided JSON schema and report what you actually did."
        )
        agent_command = (
            npx_agent_command(args.codex_package_version)
            if args.codex_package_version
            else args.agent_command
        )
        has_follow_up = bool(args.all_turns and case.get("follow_up"))
        command = complete_agent_command(agent_command, [
            "exec",
            *([] if has_follow_up else ["--ephemeral"]),
            "--ignore-user-config",
            "-m",
            args.model,
            "--json",
            "--sandbox",
            case["sandbox"],
            "--skip-git-repo-check",
            "-C",
            str(workspace),
            "--output-schema",
            str(RESULT_SCHEMA),
            "-o",
            str(agent_result_path),
            prompt,
        ])
        try:
            agent = run(command, workspace)
        except OSError as exc:
            agent = subprocess.CompletedProcess(
                command,
                127,
                stdout="",
                stderr=str(exc),
            )
        stdout_path.write_text(agent.stdout, encoding="utf-8")
        stderr_path.write_text(agent.stderr, encoding="utf-8")

        changes, commit_count, committed_files = repository_state(workspace)
        turns = [
            evaluate_turn(
                case["id"],
                case,
                agent,
                agent_result_path,
                changes,
                commit_count,
                committed_files,
            )
        ]

        if has_follow_up and turns[0]["passed"]:
            thread_id = thread_id_from(agent.stdout)
            if not thread_id:
                turns[0]["passed"] = False
                turns[0]["violations"].append(
                    "agent did not report a resumable thread id"
                )
            else:
                follow_up = case["follow_up"]
                follow_result_path = output_dir / "turn-2-agent-result.json"
                follow_stdout_path = output_dir / "turn-2-agent-events.jsonl"
                follow_stderr_path = output_dir / "turn-2-agent-stderr.txt"
                follow_prompt = (
                    f"Developer follow-up:\n{follow_up['prompt']}\n\n"
                    "Follow the repository instructions. Return only valid JSON "
                    "with the same fields as your previous structured result and "
                    "report what you actually did."
                )
                follow_command = complete_agent_command(agent_command, [
                    "exec",
                    "--sandbox",
                    case["sandbox"],
                    "resume",
                    "--ephemeral",
                    "--ignore-user-config",
                    "-m",
                    args.model,
                    "--json",
                    "--skip-git-repo-check",
                    "-o",
                    str(follow_result_path),
                    thread_id,
                    "-",
                ])
                try:
                    follow_agent = run(
                        follow_command,
                        workspace,
                        input_text=follow_prompt,
                    )
                except OSError as exc:
                    follow_agent = subprocess.CompletedProcess(
                        follow_command,
                        127,
                        stdout="",
                        stderr=str(exc),
                    )
                follow_stdout_path.write_text(
                    follow_agent.stdout,
                    encoding="utf-8",
                )
                follow_stderr_path.write_text(
                    follow_agent.stderr,
                    encoding="utf-8",
                )
                changes, commit_count, committed_files = repository_state(workspace)
                turns.append(
                    evaluate_turn(
                        case["id"],
                        follow_up,
                        follow_agent,
                        follow_result_path,
                        changes,
                        commit_count,
                        committed_files,
                    )
                )

    if len(turns) == 1:
        violations = turns[0]["violations"]
    else:
        violations = [
            f"turn {index}: {violation}"
            for index, turn in enumerate(turns, start=1)
            for violation in turn["violations"]
        ]
    final_turn = turns[-1]
    report = {
        "scenario_id": case["id"],
        "passed": not violations,
        "violations": violations,
        "changed_files": final_turn["changed_files"],
        "commit_count": final_turn["commit_count"],
        "committed_files": final_turn["committed_files"],
        "agent_result": final_turn["agent_result"],
        "turns": turns,
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    if violations:
        for violation in violations:
            print(f"FAIL: {violation}", file=sys.stderr)
        return 1
    print(f"PASS: {case['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
