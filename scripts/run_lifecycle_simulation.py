#!/usr/bin/env python3
"""Run the paired Pantry Ledger lifecycle simulation in isolated Git workspaces."""

from __future__ import annotations

import argparse
import difflib
import fnmatch
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_PATH = ROOT / "simulations" / "pantry-ledger" / "scenario.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(
    command: list[str],
    cwd: Path,
    *,
    input_text: str | None = None,
    timeout: int = 900,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            input=input_text,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        stdout = getattr(error, "stdout", "") or ""
        stderr = getattr(error, "stderr", "") or str(error)
        return subprocess.CompletedProcess(command, 124, stdout, stderr)


def command_for_windows_shim(command: list[str]) -> list[str]:
    if os.name != "nt" or Path(command[0]).suffix.lower() not in {".cmd", ".bat"}:
        return command
    invocation = "& " + " ".join(
        f"'{part.replace(chr(39), chr(39) * 2)}'" for part in command
    )
    script = (
        "$OutputEncoding = [Console]::OutputEncoding = "
        "[Text.UTF8Encoding]::new(); "
        + invocation
    )
    return [
        shutil.which("powershell.exe") or "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        script,
    ]


def git(workspace: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return run(["git", *arguments], workspace, timeout=120)


def git_output(workspace: Path, *arguments: str) -> str:
    result = git(workspace, *arguments)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def workspace_snapshot(workspace: Path) -> dict[str, bytes]:
    snapshot: dict[str, bytes] = {}
    ignored_parts = {".git", "node_modules", "__pycache__", "data"}
    for path in sorted(item for item in workspace.rglob("*") if item.is_file()):
        relative = path.relative_to(workspace)
        if ignored_parts.intersection(relative.parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        snapshot[relative.as_posix()] = path.read_bytes()
    return snapshot


def snapshot_delta(
    before: dict[str, bytes],
    after: dict[str, bytes],
) -> tuple[list[str], str]:
    changed = sorted(
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
    )
    patch: list[str] = []
    for path in changed:
        old = before.get(path)
        new = after.get(path)
        try:
            old_lines = (
                old.decode("utf-8").splitlines(keepends=True) if old is not None else []
            )
            new_lines = (
                new.decode("utf-8").splitlines(keepends=True) if new is not None else []
            )
        except UnicodeDecodeError:
            patch.append(f"Binary file changed: {path}\n")
            continue
        patch.extend(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{path}" if old is not None else "/dev/null",
                tofile=f"b/{path}" if new is not None else "/dev/null",
            )
        )
    return changed, "".join(patch)


def digest_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def initialize_repository(
    seed: Path,
    workspace: Path,
    evidence_path: Path,
    redaction_paths: list[Path],
) -> dict[str, Any]:
    shutil.copytree(
        seed,
        workspace,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    evidence: dict[str, Any] = {
        "seed": str(seed),
        "workspace": str(workspace),
        "commands": [],
    }
    commands = [
        ["git", "init", "--quiet", "--initial-branch=main"],
        ["git", "config", "core.filemode", "false"],
        ["git", "config", "user.name", "AI SDLC Simulation"],
        ["git", "config", "user.email", "simulation@example.invalid"],
        ["git", "add", "-A"],
        ["git", "commit", "--quiet", "-m", "Create Pantry Ledger seed"],
    ]
    for command in commands:
        result = run(command, workspace, timeout=120)
        evidence["commands"].append(
            {
                "command": command,
                "status": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        evidence_path.write_text(
            json.dumps(redact_value(evidence, redaction_paths), indent=2) + "\n",
            encoding="utf-8",
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    evidence["commit"] = git_output(workspace, "rev-parse", "HEAD")
    evidence_path.write_text(
        json.dumps(redact_value(evidence, redaction_paths), indent=2) + "\n",
        encoding="utf-8",
    )
    return evidence


def install_kit(
    workspace: Path,
    command_prefix: list[str],
    evidence_path: Path,
    redaction_paths: list[Path],
) -> dict[str, Any]:
    command = [*command_prefix, "--yes"]
    result = run(command, workspace, timeout=180)
    evidence: dict[str, Any] = {
        "command": command,
        "status": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    evidence_path.write_text(
        json.dumps(redact_value(evidence, redaction_paths), indent=2) + "\n",
        encoding="utf-8",
    )
    if result.returncode:
        raise RuntimeError(
            "AI SDLC adoption failed: " + (result.stderr.strip() or result.stdout.strip())
        )

    validator = run(
        [sys.executable, "-B", "scripts/validate_ai_kit.py"],
        workspace,
        timeout=180,
    )
    evidence["validator"] = {
        "status": validator.returncode,
        "stdout": validator.stdout,
        "stderr": validator.stderr,
    }
    evidence_path.write_text(
        json.dumps(redact_value(evidence, redaction_paths), indent=2) + "\n",
        encoding="utf-8",
    )
    if validator.returncode:
        raise RuntimeError(
            "Installed kit validation failed: "
            + (validator.stderr.strip() or validator.stdout.strip())
        )

    for arguments in (
        ["git", "add", "-A"],
        ["git", "commit", "--quiet", "-m", "Adopt AI SDLC workflow"],
    ):
        result = run(arguments, workspace, timeout=120)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    evidence["commit"] = git_output(workspace, "rev-parse", "HEAD")
    evidence_path.write_text(
        json.dumps(redact_value(evidence, redaction_paths), indent=2) + "\n",
        encoding="utf-8",
    )
    return evidence


def installed_kit_version(workspace: Path) -> str:
    lock_path = workspace / ".ai" / "kit.lock.json"
    try:
        version = json.loads(lock_path.read_text(encoding="utf-8"))["kit_version"]
    except (OSError, KeyError, json.JSONDecodeError, TypeError) as error:
        raise RuntimeError(
            f"Cannot read installed kit version from {lock_path}"
        ) from error
    if not isinstance(version, str) or not version:
        raise RuntimeError(f"Invalid installed kit version in {lock_path}")
    return version


def process_node() -> str:
    return shutil.which("node") or "node"


def process_npm() -> str:
    executable = "npm.cmd" if os.name == "nt" else "npm"
    return shutil.which(executable) or executable


def runtime_versions() -> dict[str, dict[str, Any]]:
    commands = {
        "node": [process_node(), "--version"],
        "npm": [process_npm(), "--version"],
        "python": [sys.executable, "--version"],
        "git": ["git", "--version"],
        "ripgrep": ["rg", "--version"],
    }
    versions: dict[str, dict[str, Any]] = {}
    for name, command in commands.items():
        result = run(command, ROOT, timeout=60)
        versions[name] = {
            "status": result.returncode,
            "version": (result.stdout or result.stderr).splitlines()[0]
            if (result.stdout or result.stderr).splitlines()
            else "",
        }
    return versions


def default_agent_command(codex_package_version: str) -> list[str]:
    executable = shutil.which("npx.cmd" if os.name == "nt" else "npx")
    return [
        executable or "npx",
        "--yes",
        f"@openai/codex@{codex_package_version}",
        "--ask-for-approval",
        "never",
    ]


def redact(text: str, paths: list[Path]) -> str:
    redacted = text
    for index, path in enumerate(paths, start=1):
        candidates = {
            str(path),
            str(path).replace("\\", "/"),
        }
        for candidate in sorted(candidates, key=len, reverse=True):
            candidate = candidate.rstrip("/\\")
            if not candidate:
                continue
            pattern = re.compile(
                rf"(?<![A-Za-z0-9._-]){re.escape(candidate)}"
                r"(?=(?:[/\\]|\s|['\";,)\]}]|$))"
            )
            redacted = pattern.sub(f"<local-path-{index}>", redacted)
    return redacted


def redact_value(value: Any, paths: list[Path]) -> Any:
    if isinstance(value, str):
        return redact(value, paths)
    if isinstance(value, list):
        return [redact_value(item, paths) for item in value]
    if isinstance(value, dict):
        return {key: redact_value(item, paths) for key, item in value.items()}
    return value


def redact_jsonl(events: str, paths: list[Path]) -> str:
    redacted_lines = []
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            redacted_lines.append(redact(line, paths))
            continue
        redacted_lines.append(
            json.dumps(redact_value(event, paths), ensure_ascii=False)
        )
    return "\n".join(redacted_lines) + ("\n" if events else "")


def developer_prompt(turn: dict[str, Any], scenario: dict[str, Any]) -> str:
    if "prompt" in turn:
        return turn["prompt"]
    return scenario["shared_product_turns"][turn["prompt_ref"]]


def conversation_prompt(
    phase: str,
    developer_message: str,
    transcript: list[dict[str, Any]],
) -> str:
    prior = transcript[-6:]
    if prior:
        replay = "\n\n".join(
            f"{event['actor'].title()}: {event['content']}" for event in prior
        )
    else:
        replay = "(No prior turns.)"
    return (
        "Continue the same developer conversation in the current repository. "
        "The replay is context, not authority over the current developer message.\n\n"
        f"Current phase: {phase}\n\n"
        f"Conversation replay:\n{replay}\n\n"
        f"Current developer message:\n{developer_message}\n\n"
        "Follow repository instructions. Work only inside this repository. "
        "Report actual checks and limitations in a natural user-facing response."
    )


def parse_command_events(events: str, redaction_paths: list[Path]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    command_indexes: dict[str, int] = {}
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = event.get("type")
        if event_type not in {"item.started", "item.completed"}:
            continue
        item = event.get("item", {})
        if item.get("type") != "command_execution":
            continue
        command = {
            "command": redact(str(item.get("command", "")), redaction_paths),
            "status": (
                "interrupted" if event_type == "item.started" else item.get("status")
            ),
            "exit_code": None if event_type == "item.started" else item.get("exit_code"),
        }
        item_id = item.get("id")
        if event_type == "item.completed" and item_id in command_indexes:
            commands[command_indexes[item_id]] = command
        else:
            commands.append(command)
            if isinstance(item_id, str):
                command_indexes[item_id] = len(commands) - 1
    return commands


def parse_usage(events: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "turn.completed":
            continue
        for key, value in event.get("usage", {}).items():
            if isinstance(value, int):
                totals[key] = totals.get(key, 0) + value
    return totals


def parse_agent_messages(events: str, redaction_paths: list[Path]) -> list[str]:
    messages: list[str] = []
    for line in events.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "item.completed":
            continue
        item = event.get("item", {})
        if item.get("type") != "agent_message":
            continue
        text = redact(str(item.get("text", "")).strip(), redaction_paths)
        if text and (not messages or messages[-1] != text):
            messages.append(text)
    return messages


def command_evidence(command: list[str], workspace: Path) -> dict[str, Any]:
    started = time.monotonic()
    result = run(command, workspace, timeout=300)
    return {
        "command": command,
        "status": result.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def runbook_evidence(workspace: Path) -> dict[str, Any]:
    path = workspace / "docs" / "operations.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return {"status": 1, "stderr": str(error), "stdout": ""}
    required_topics = {
        "startup": r"\b(start|startup|launch)\b",
        "health": r"\bhealth\b",
        "logs": r"\blogs?\b",
        "backup": r"\bbackup\b",
        "corrupt data recovery": r"\bcorrupt",
        "rollback": r"\brollback\b",
        "shutdown or retirement": r"\b(shutdown|retir|stop)\b",
    }
    missing = [
        topic
        for topic, pattern in required_topics.items()
        if not re.search(pattern, text, flags=re.IGNORECASE)
    ]
    return {
        "command": ["validate", "docs/operations.md"],
        "status": 1 if missing else 0,
        "stdout": "operations runbook covers required topics" if not missing else "",
        "stderr": f"missing runbook topics: {', '.join(missing)}" if missing else "",
    }


def operational_verification(
    workspace: Path,
    arm_root: Path,
    checkpoints: dict[str, str],
) -> dict[str, Any]:
    operations_root = arm_root / "operations"
    operations_root.mkdir(exist_ok=True)
    evidence: dict[str, Any] = {}
    releases = (
        ("initial_release", "feature"),
        ("operations_handoff", "full"),
    )
    for checkpoint_name, mode in releases:
        revision = checkpoints.get(checkpoint_name)
        prefix = "initial_release" if mode == "feature" else "final_clean_release"
        if not revision:
            missing = {
                "status": 2,
                "stdout": "",
                "stderr": f"missing checkpoint: {checkpoint_name}",
            }
            evidence[f"{prefix}_checkout"] = missing
            evidence[f"{prefix}_tests"] = missing
            evidence[f"{prefix}_acceptance"] = missing
            continue
        release = operations_root / checkpoint_name
        clone = command_evidence(
            [
                "git",
                "clone",
                "--quiet",
                "--no-hardlinks",
                str(workspace),
                str(release),
            ],
            operations_root,
        )
        evidence[f"{prefix}_checkout"] = clone
        if clone["status"]:
            evidence[f"{prefix}_tests"] = clone
            evidence[f"{prefix}_acceptance"] = clone
            continue
        checkout = command_evidence(
            ["git", "checkout", "--quiet", "--detach", revision],
            release,
        )
        evidence[f"{prefix}_checkout"] = checkout
        if checkout["status"]:
            evidence[f"{prefix}_tests"] = checkout
            evidence[f"{prefix}_acceptance"] = checkout
            continue
        run(["git", "config", "core.filemode", "false"], release, timeout=120)
        evidence[f"{prefix}_tests"] = command_evidence(
            [process_npm(), "test"],
            release,
        )
        evidence[f"{prefix}_acceptance"] = command_evidence(
            [
                process_node(),
                str(ROOT / "scripts" / "pantry_ledger_acceptance.mjs"),
                str(release),
                "--mode",
                mode,
            ],
            release,
        )
    final_release = operations_root / "operations_handoff"
    initial_release = operations_root / "initial_release"
    missing_rollback_checkpoints = [
        name
        for name in ("initial_release", "operations_handoff")
        if not checkpoints.get(name)
    ]
    if missing_rollback_checkpoints:
        evidence["cross_version_rollback_acceptance"] = {
            "status": 2,
            "stdout": "",
            "stderr": (
                "missing rollback checkpoints: "
                + ", ".join(missing_rollback_checkpoints)
            ),
        }
    else:
        evidence["cross_version_rollback_acceptance"] = command_evidence(
            [
                process_node(),
                str(ROOT / "scripts" / "pantry_ledger_rollback_acceptance.mjs"),
                str(final_release),
                str(initial_release),
            ],
            operations_root,
        )
    if checkpoints.get("operations_handoff"):
        evidence["operations_runbook"] = runbook_evidence(final_release)
    else:
        evidence["operations_runbook"] = {
            "status": 2,
            "stdout": "",
            "stderr": "missing checkpoint: operations_handoff",
        }
    return evidence


def lifecycle_invariant_evidence(
    arm: str,
    workspace: Path,
    turns: list[dict[str, Any]],
    artifacts_added: dict[str, list[str]],
    checkpoints: dict[str, str],
    commit_delta: int,
    final_status: list[str],
) -> dict[str, Any]:
    expected_commits = sum(
        int(turn.get("expect", {}).get("commit_delta", 0)) for turn in turns
    )
    expected_checkpoints = {
        checkpoint
        for turn in turns
        if (checkpoint := turn.get("expect", {}).get("checkpoint"))
    }
    checks: dict[str, bool] = {
        "clean_worktree": not final_status,
        "authorized_commit_count": commit_delta == expected_commits,
        "release_checkpoints": expected_checkpoints == set(checkpoints),
    }
    details: dict[str, Any] = {
        "final_status": final_status,
        "commit_delta": commit_delta,
        "expected_commit_delta": expected_commits,
        "checkpoints": checkpoints,
        "expected_checkpoints": sorted(expected_checkpoints),
    }
    if arm == "with-kit":
        for group in ("specifications", "verification", "plans", "handoffs"):
            checks[f"created_{group}"] = bool(artifacts_added.get(group))
        specification_statuses = {
            relative: document_status(workspace / relative)
            for relative in artifacts_added.get("specifications", [])
        }
        plan_statuses = {
            relative: document_status(workspace / relative)
            for relative in artifacts_added.get("plans", [])
        }
        checks["accepted_specifications"] = bool(specification_statuses) and all(
            status == "accepted" for status in specification_statuses.values()
        )
        checks["accepted_plans"] = bool(plan_statuses) and all(
            status == "accepted" for status in plan_statuses.values()
        )
        details["specification_statuses"] = specification_statuses
        details["plan_statuses"] = plan_statuses
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "command": ["validate", "lifecycle-invariants"],
        "status": 1 if failed else 0,
        "stdout": "all lifecycle invariants passed" if not failed else "",
        "stderr": f"failed lifecycle invariants: {', '.join(failed)}" if failed else "",
        "checks": checks,
        "details": details,
    }


def project_verification(
    workspace: Path,
    arm: str,
    kit_command: list[str],
    initial_commit: str,
) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    try:
        package = json.loads(
            (workspace / "package.json").read_text(encoding="utf-8")
        )
        scripts = package.get("scripts", {})
        if not isinstance(scripts, dict):
            raise ValueError("package.json scripts must be an object")
        evidence["package_json"] = {"status": 0, "stdout": "valid package.json"}
    except (OSError, ValueError, json.JSONDecodeError) as error:
        scripts = {}
        evidence["package_json"] = {"status": 1, "stderr": str(error)}
    for key, script in (
        ("npm_test", "test"),
        ("npm_lint", "lint"),
        ("npm_build", "build"),
        ("npm_security", "security"),
    ):
        if script in scripts:
            evidence[key] = command_evidence(
                [process_npm(), "run", script],
                workspace,
            )
        else:
            evidence[key] = {
                "command": [process_npm(), "run", script],
                "status": 2,
                "stdout": "",
                "stderr": f"required package script is missing: {script}",
            }
    evidence["npm_pack_dry_run"] = command_evidence(
        [process_npm(), "pack", "--dry-run", "--json"],
        workspace,
    )
    evidence["git_diff_check"] = command_evidence(
        ["git", "diff", "--check", initial_commit],
        workspace,
    )
    evidence["external_acceptance"] = command_evidence(
        [
            process_node(),
            str(ROOT / "scripts" / "pantry_ledger_acceptance.mjs"),
            str(workspace),
        ],
        workspace,
    )
    if arm == "with-kit":
        evidence["kit_validator"] = command_evidence(
            [sys.executable, "-B", "scripts/validate_ai_kit.py"],
            workspace,
        )
        evidence["kit_rerun"] = command_evidence(
            [*kit_command, "--dry-run"],
            workspace,
        )
    return evidence


COMMON_REQUIRED_GATES = {
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
}
KIT_REQUIRED_GATES = {"kit_validator", "kit_rerun"}


def verification_passed(evidence: dict[str, Any], arm: str) -> bool:
    required = set(COMMON_REQUIRED_GATES)
    if arm == "with-kit":
        required.update(KIT_REQUIRED_GATES)
    return all(
        key in evidence
        and isinstance(evidence[key], dict)
        and evidence[key].get("status") == 0
        for key in required
    )


def artifact_inventory(workspace: Path) -> dict[str, list[str]]:
    groups = {
        "specifications": "specs/*/spec.md",
        "verification": "specs/*/verification.md",
        "plans": "specs/*/plan.md",
        "decisions": "docs/adr/*.md",
        "handoffs": "artifacts/ai/handoffs/*",
        "tests": "test/*",
    }
    return {
        group: sorted(
            path.relative_to(workspace).as_posix()
            for path in workspace.glob(pattern)
            if "_template" not in path.relative_to(workspace).parts
        )
        for group, pattern in groups.items()
    }


def artifact_delta(
    before: dict[str, list[str]],
    after: dict[str, list[str]],
) -> dict[str, list[str]]:
    return {
        group: sorted(set(paths) - set(before.get(group, [])))
        for group, paths in after.items()
    }


def matching_paths(paths: list[str], pattern: str) -> list[str]:
    return sorted(path for path in paths if fnmatch.fnmatch(path, pattern))


def document_status(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    match = re.search(r"^status:\s*(\S+)\s*$", text, flags=re.MULTILINE)
    return match.group(1) if match else None


def evaluate_phase_gate(
    workspace: Path,
    expectation: dict[str, Any],
    changed_paths: list[str],
    before_commit: str,
    after_commit: str,
    status_after: str,
    commands: list[dict[str, Any]],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def record(name: str, passed: bool, actual: Any, expected: Any) -> None:
        checks.append(
            {
                "name": name,
                "passed": passed,
                "actual": actual,
                "expected": expected,
            }
        )

    all_paths = [
        path.relative_to(workspace).as_posix()
        for path in workspace.rglob("*")
        if path.is_file()
        and ".git" not in path.relative_to(workspace).parts
        and "_template" not in path.relative_to(workspace).parts
    ]
    for pattern in expectation.get("required_artifacts", []):
        matches = matching_paths(all_paths, pattern)
        record(f"required artifact {pattern}", bool(matches), matches, "one or more")

    for pattern, expected_status in expectation.get("required_status", {}).items():
        matches = matching_paths(all_paths, pattern)
        statuses = {
            relative: document_status(workspace / relative) for relative in matches
        }
        record(
            f"document status {pattern}",
            bool(statuses)
            and all(status == expected_status for status in statuses.values()),
            statuses,
            expected_status,
        )

    for pattern in expectation.get("required_changes", []):
        matches = matching_paths(changed_paths, pattern)
        record(f"required change {pattern}", bool(matches), matches, "one or more")

    for pattern in expectation.get("forbidden_changes", []):
        matches = matching_paths(changed_paths, pattern)
        record(f"forbidden change {pattern}", not matches, matches, [])

    if "commit_delta" in expectation:
        commit_delta = int(
            git_output(workspace, "rev-list", "--count", f"{before_commit}..{after_commit}")
        )
        record(
            "commit delta",
            commit_delta == expectation["commit_delta"],
            commit_delta,
            expectation["commit_delta"],
        )

    if expectation.get("clean_worktree"):
        record("clean worktree", not status_after, status_after.splitlines(), [])

    if expectation.get("successful_command"):
        successful = [
            command
            for command in commands
            if command.get("status") == "completed" and command.get("exit_code") == 0
        ]
        record("successful repository command", bool(successful), len(successful), ">= 1")

    interrupted = [
        command for command in commands if command.get("status") == "interrupted"
    ]
    record(
        "no interrupted repository commands",
        not interrupted,
        [command["command"] for command in interrupted],
        [],
    )

    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def write_transcript(
    arm_root: Path,
    scenario_title: str,
    transcript: list[dict[str, Any]],
) -> None:
    with (arm_root / "transcript.jsonl").open("w", encoding="utf-8") as handle:
        for event in transcript:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    markdown = [f"# {scenario_title}: {arm_root.name}", ""]
    for event in transcript:
        markdown.extend(
            [
                f"## Turn {event['turn']} · {event['phase']} · {event['actor'].title()}",
                "",
            ]
        )
        if event.get("updates"):
            markdown.extend(["### Progress updates", ""])
            for update in event["updates"]:
                markdown.extend([update, ""])
            markdown.extend(["### Final response", ""])
        markdown.extend([event["content"], ""])
    (arm_root / "transcript.md").write_text(
        "\n".join(markdown).rstrip() + "\n",
        encoding="utf-8",
    )


def run_arm(
    *,
    arm: str,
    output_root: Path,
    scenario: dict[str, Any],
    agent_command: list[str],
    model: str,
    turn_limit: int | None,
    kit_command: list[str],
    kit_source: Path,
    kit_source_kind: str,
    codex_package_version: str,
    sandbox: str,
    isolation_image: str | None,
) -> dict[str, Any]:
    arm_root = output_root / arm
    if arm_root.exists():
        raise RuntimeError(f"Refusing to overwrite existing run directory: {arm_root}")
    arm_root.mkdir(parents=True)
    workspace = arm_root / "workspace"
    turns_root = arm_root / "turns"
    turns_root.mkdir()

    seed = ROOT / scenario["seed"]
    started_at = utc_now()
    started_timer = time.monotonic()
    setup_started = time.monotonic()
    adoption = None
    setup = None
    seed_commit = None
    try:
        setup = initialize_repository(
            seed,
            workspace,
            arm_root / "setup.json",
            [workspace, output_root, ROOT],
        )
        seed_commit = git_output(workspace, "rev-parse", "HEAD")
        if arm == "with-kit":
            adoption = install_kit(
                workspace,
                kit_command,
                arm_root / "adoption.json",
                [workspace, output_root, ROOT],
            )
        initial_commit = git_output(workspace, "rev-parse", "HEAD")
        setup_commit_count = int(
            git_output(workspace, "rev-list", "--count", "HEAD")
        )
        initial_artifacts = artifact_inventory(workspace)
    except (OSError, RuntimeError) as error:
        report = {
            "schema_version": 1,
            "scenario_id": scenario["id"],
            "arm": arm,
            "started_at_utc": started_at,
            "ended_at_utc": utc_now(),
            "duration_seconds": round(time.monotonic() - started_timer, 3),
            "setup_duration_seconds": round(
                time.monotonic() - setup_started,
                3,
            ),
            "setup_error": str(error),
            "setup": setup,
            "seed_commit": seed_commit,
            "initial_commit": None,
            "final_commit": None,
            "commit_count": 0,
            "commit_delta": 0,
            "turns": [],
            "artifacts": {
                "specifications": [],
                "verification": [],
                "plans": [],
                "decisions": [],
                "handoffs": [],
                "tests": [],
            },
            "initial_artifacts": {
                "specifications": [],
                "verification": [],
                "plans": [],
                "decisions": [],
                "handoffs": [],
                "tests": [],
            },
            "artifacts_added": {
                "specifications": [],
                "verification": [],
                "plans": [],
                "decisions": [],
                "handoffs": [],
                "tests": [],
            },
            "final_status": [],
            "final_verification": {},
            "probe_passed": None,
            "full_lifecycle_completed": False,
            "passed": False,
        }
        (arm_root / "report.json").write_text(
            json.dumps(
                redact_value(report, [workspace, output_root, ROOT]),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return report

    setup_duration = round(time.monotonic() - setup_started, 3)
    workflow_started = time.monotonic()
    print(
        f"START {arm}: setup completed in {setup_duration}s",
        flush=True,
    )
    transcript: list[dict[str, Any]] = []
    command_log: list[dict[str, Any]] = []
    turn_reports: list[dict[str, Any]] = []
    checkpoints: dict[str, str] = {}
    all_arm_turns = scenario["arms"][arm]
    arm_turns = all_arm_turns
    if turn_limit is not None:
        arm_turns = arm_turns[:turn_limit]

    for turn_number, turn in enumerate(arm_turns, start=1):
        phase = turn["phase"]
        print(
            f"TURN {arm} {turn_number}/{len(arm_turns)}: {phase}",
            flush=True,
        )
        developer_message = developer_prompt(turn, scenario)
        transcript.append(
            {
                "turn": turn_number,
                "phase": phase,
                "actor": "human",
                "timestamp_utc": utc_now(),
                "content": developer_message,
            }
        )
        turn_slug = f"{turn_number:02d}-{phase}"
        turn_root = turns_root / turn_slug
        turn_root.mkdir()
        response_path = turn_root / "assistant-response.md"
        before_commit = git_output(workspace, "rev-parse", "HEAD")
        before_status = git_output(
            workspace,
            "status",
            "--porcelain",
            "--untracked-files=all",
        )
        before_snapshot = workspace_snapshot(workspace)

        prompt = conversation_prompt(phase, developer_message, transcript[:-1])
        command = [
            *agent_command,
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "-m",
            model,
            "--json",
            "--sandbox",
            sandbox,
            "--skip-git-repo-check",
            "-C",
            str(workspace),
            "-o",
            str(response_path),
            prompt,
        ]
        started_turn = time.monotonic()
        agent = run(command_for_windows_shim(command), workspace)
        duration = round(time.monotonic() - started_turn, 3)
        events = redact_jsonl(agent.stdout, [workspace, output_root, ROOT])
        stderr = redact(agent.stderr, [workspace, output_root, ROOT])
        (turn_root / "agent-events.jsonl").write_text(events, encoding="utf-8")
        (turn_root / "agent-stderr.txt").write_text(stderr, encoding="utf-8")

        response = (
            response_path.read_text(encoding="utf-8")
            if response_path.exists()
            else f"[Assistant produced no final response; exit status {agent.returncode}.]"
        )
        response = redact(response, [workspace, output_root, ROOT])
        response_path.write_text(response, encoding="utf-8")
        agent_messages = parse_agent_messages(
            agent.stdout,
            [workspace, output_root, ROOT],
        )
        progress_updates = [
            message for message in agent_messages if message.strip() != response.strip()
        ]
        transcript.append(
            {
                "turn": turn_number,
                "phase": phase,
                "actor": "assistant",
                "timestamp_utc": utc_now(),
                "content": response,
                "updates": progress_updates,
            }
        )

        commands = parse_command_events(agent.stdout, [workspace, output_root, ROOT])
        usage = parse_usage(agent.stdout)
        for item in commands:
            command_log.append(
                {"turn": turn_number, "phase": phase, **item}
            )
        after_commit = git_output(workspace, "rev-parse", "HEAD")
        after_status = git_output(
            workspace,
            "status",
            "--porcelain",
            "--untracked-files=all",
        )
        after_snapshot = workspace_snapshot(workspace)
        changed_paths, diff = snapshot_delta(before_snapshot, after_snapshot)
        phase_gate = evaluate_phase_gate(
            workspace,
            turn.get("expect", {}),
            changed_paths,
            before_commit,
            after_commit,
            after_status,
            commands,
        )
        acceptance_mode = turn.get("expect", {}).get("acceptance")
        if acceptance_mode:
            acceptance = command_evidence(
                [
                    process_node(),
                    str(ROOT / "scripts" / "pantry_ledger_acceptance.mjs"),
                    str(workspace),
                    "--mode",
                    acceptance_mode,
                ],
                workspace,
            )
            phase_gate["acceptance"] = acceptance
            phase_gate["checks"].append(
                {
                    "name": f"{acceptance_mode} acceptance",
                    "passed": acceptance["status"] == 0,
                    "actual": acceptance["status"],
                    "expected": 0,
                }
            )
            phase_gate["passed"] = phase_gate["passed"] and acceptance["status"] == 0
        checkpoint = turn.get("expect", {}).get("checkpoint")
        if checkpoint and phase_gate["passed"]:
            checkpoints[checkpoint] = after_commit
        (turn_root / "git-status-before.txt").write_text(
            before_status + ("\n" if before_status else ""),
            encoding="utf-8",
        )
        (turn_root / "git-status-after.txt").write_text(
            after_status + ("\n" if after_status else ""),
            encoding="utf-8",
        )
        (turn_root / "repository-delta.patch").write_text(
            diff + ("\n" if diff else ""),
            encoding="utf-8",
        )
        (turn_root / "phase-gate.json").write_text(
            json.dumps(
                redact_value(phase_gate, [workspace, output_root, ROOT]),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        focused_test = command_evidence([process_npm(), "test"], workspace)
        (turn_root / "harness-test.json").write_text(
            json.dumps(
                redact_value(
                    focused_test,
                    [workspace, output_root, ROOT],
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        turn_reports.append(
            {
                "turn": turn_number,
                "phase": phase,
                "agent_status": agent.returncode,
                "duration_seconds": duration,
                "commands": commands,
                "progress_updates": progress_updates,
                "usage": usage,
                "before_commit": before_commit,
                "after_commit": after_commit,
                "status_before": before_status.splitlines(),
                "status_after": after_status.splitlines(),
                "changed_paths": changed_paths,
                "harness_test_status": focused_test["status"],
                "phase_gate": phase_gate,
            }
        )
        write_transcript(arm_root, scenario["title"], transcript)
        print(
            f"DONE {arm} {turn_number}: agent={agent.returncode} "
            f"test={focused_test['status']} duration={duration}s",
            flush=True,
        )
        if agent.returncode or not phase_gate["passed"]:
            break

    with (arm_root / "commands.jsonl").open("w", encoding="utf-8") as handle:
        for item in command_log:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"VERIFY {arm}: running release gates", flush=True)
    final_verification = project_verification(
        workspace,
        arm,
        kit_command,
        initial_commit,
    )
    final_verification.update(
        operational_verification(workspace, arm_root, checkpoints)
    )
    artifacts = artifact_inventory(workspace)
    artifacts_added = artifact_delta(initial_artifacts, artifacts)
    final_commit = git_output(workspace, "rev-parse", "HEAD")
    commit_count = int(git_output(workspace, "rev-list", "--count", "HEAD"))
    commit_delta = commit_count - setup_commit_count
    final_status = git_output(
        workspace,
        "status",
        "--porcelain",
        "--untracked-files=all",
    ).splitlines()
    final_verification["lifecycle_invariants"] = lifecycle_invariant_evidence(
        arm,
        workspace,
        all_arm_turns,
        artifacts_added,
        checkpoints,
        commit_delta,
        final_status,
    )
    final_verification_passed = verification_passed(final_verification, arm)
    print(
        f"VERIFIED {arm}: passed={final_verification_passed}",
        flush=True,
    )
    is_probe = (
        turn_limit is not None and len(arm_turns) < len(all_arm_turns)
    )
    execution_passed = (
        len(turn_reports) == len(arm_turns)
        and all(turn["agent_status"] == 0 for turn in turn_reports)
        and all(turn["harness_test_status"] == 0 for turn in turn_reports)
        and all(turn["phase_gate"]["passed"] for turn in turn_reports)
    )
    probe_observed_successful_command = any(
        command.get("status") == "completed" and command.get("exit_code") == 0
        for turn in turn_reports
        for command in turn["commands"]
    )
    probe_passed = execution_passed and probe_observed_successful_command
    full_lifecycle_completed = (
        not is_probe
        and len(turn_reports) == len(all_arm_turns)
        and execution_passed
    )
    passed = (
        probe_passed
        if is_probe
        else full_lifecycle_completed and final_verification_passed
    )
    usage: dict[str, int] = {}
    for turn in turn_reports:
        for key, value in turn["usage"].items():
            usage[key] = usage.get(key, 0) + value
    workflow_duration = round(time.monotonic() - workflow_started, 3)
    report = {
        "schema_version": 1,
        "scenario_id": scenario["id"],
        "arm": arm,
        "started_at_utc": started_at,
        "ended_at_utc": utc_now(),
        "duration_seconds": round(time.monotonic() - started_timer, 3),
        "setup_duration_seconds": setup_duration,
        "workflow_duration_seconds": workflow_duration,
        "isolation": {
            "workspace": "retained isolated Git repository",
            "assistant_session": "fresh ephemeral turn with transcript replay",
            "sandbox": sandbox,
            "host": platform.platform(),
            "container_image": isolation_image,
        },
        "runtime_versions": runtime_versions(),
        "simulation_inputs": {
            "runner_sha256": digest_file(Path(__file__)),
            "scenario_sha256": digest_file(SCENARIO_PATH),
            "oracle_sha256": digest_file(
                ROOT / "scripts" / "pantry_ledger_acceptance.mjs"
            ),
            "rollback_oracle_sha256": digest_file(
                ROOT / "scripts" / "pantry_ledger_rollback_acceptance.mjs"
            ),
            "repo_template_sha256": digest_tree(ROOT / "repo-template"),
        },
        "assistant": {
            "provider": "openai",
            "model": model,
            "codex_package_version": codex_package_version,
            "command_prefix": agent_command,
            "usage": usage,
        },
        "seed": {
            "path": scenario["seed"],
            "sha256": digest_tree(seed),
        },
        "setup": setup,
        "kit": (
            {
                "version": installed_kit_version(workspace),
                "source_commit": git_output(ROOT, "rev-parse", "HEAD"),
                "source_dirty": bool(
                    git_output(
                        ROOT,
                        "status",
                        "--porcelain",
                        "--untracked-files=all",
                    )
                ),
                "source_kind": kit_source_kind,
                "source_sha256": digest_file(kit_source),
                "adoption": adoption,
            }
            if arm == "with-kit"
            else None
        ),
        "seed_commit": seed_commit,
        "initial_commit": initial_commit,
        "final_commit": final_commit,
        "commit_count": commit_count,
        "commit_delta": commit_delta,
        "turns": turn_reports,
        "checkpoints": checkpoints,
        "initial_artifacts": initial_artifacts,
        "artifacts": artifacts,
        "artifacts_added": artifacts_added,
        "final_status": final_status,
        "final_verification": final_verification,
        "final_verification_passed": final_verification_passed,
        "probe_passed": probe_passed if is_probe else None,
        "full_lifecycle_completed": full_lifecycle_completed,
        "passed": passed,
    }
    (arm_root / "report.json").write_text(
        json.dumps(
            redact_value(report, [workspace, output_root, ROOT]),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def comparison(reports: list[dict[str, Any]], output_root: Path) -> None:
    by_arm = {report["arm"]: report for report in reports}
    metrics: dict[str, Any] = {}
    for arm, report in by_arm.items():
        test_files_added = len(report["artifacts_added"]["tests"])
        metrics[arm] = {
            "passed": report["passed"],
            "full_lifecycle_completed": report["full_lifecycle_completed"],
            "turns_completed": len(report["turns"]),
            "total_duration_seconds": report["duration_seconds"],
            "setup_duration_seconds": report.get("setup_duration_seconds"),
            "workflow_duration_seconds": report.get("workflow_duration_seconds"),
            "commands_observed": sum(
                sum(
                    command.get("exit_code") is not None
                    for command in turn["commands"]
                )
                for turn in report["turns"]
            ),
            "command_attempts": sum(
                len(turn["commands"]) for turn in report["turns"]
            ),
            "commands_interrupted": sum(
                command.get("status") == "interrupted"
                for turn in report["turns"]
                for command in turn["commands"]
            ),
            "commands_failed": sum(
                command.get("exit_code") not in (None, 0)
                for turn in report["turns"]
                for command in turn["commands"]
            ),
            "commit_delta": report.get("commit_delta", 0),
            "specifications": len(report["artifacts_added"]["specifications"]),
            "plans": len(report["artifacts_added"]["plans"]),
            "verification_artifacts": len(
                report["artifacts_added"]["verification"]
            ),
            "handoffs": len(report["artifacts_added"]["handoffs"]),
            "test_files_added": test_files_added,
            "tests": test_files_added,
            "final_test_status": report["final_verification"]
            .get("npm_test", {})
            .get("status"),
            "external_acceptance_status": report["final_verification"]
            .get("external_acceptance", {})
            .get("status"),
            "input_tokens": report.get("assistant", {})
            .get("usage", {})
            .get("input_tokens"),
            "output_tokens": report.get("assistant", {})
            .get("usage", {})
            .get("output_tokens"),
        }
    payload = {
        "schema_version": 1,
        "scenario_id": reports[0]["scenario_id"],
        "arms": metrics,
        "interpretation_note": (
            "Counts are descriptive evidence, not a causal quality verdict; the "
            "arms intentionally contain different numbers of workflow and approval "
            "turns. Test artifact counts are test files added, not test cases. "
            "Review each transcript, patch, and deterministic command result."
        ),
    }
    (output_root / "comparison.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Pantry Ledger paired comparison",
        "",
        "| Metric | Baseline | With AI SDLC |",
        "| --- | ---: | ---: |",
    ]
    ordered = [
        "passed",
        "full_lifecycle_completed",
        "turns_completed",
        "total_duration_seconds",
        "setup_duration_seconds",
        "workflow_duration_seconds",
        "commands_observed",
        "command_attempts",
        "commands_interrupted",
        "commands_failed",
        "commit_delta",
        "specifications",
        "plans",
        "verification_artifacts",
        "handoffs",
        "test_files_added",
        "final_test_status",
        "external_acceptance_status",
        "input_tokens",
        "output_tokens",
    ]
    for key in ordered:
        lines.append(
            f"| {key.replace('_', ' ')} | "
            f"{metrics.get('baseline', {}).get(key, 'n/a')} | "
            f"{metrics.get('with-kit', {}).get(key, 'n/a')} |"
        )
    lines.extend(
        [
            "",
            "These metrics are descriptive. Test artifact counts are test files "
            "added, not test cases. The transcripts and repository deltas remain "
            "the evidence for workflow quality and rework.",
            "",
        ]
    )
    (output_root / "comparison.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--arm",
        choices=("baseline", "with-kit", "both"),
        default="both",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-terra")
    parser.add_argument("--codex-package-version", default="0.145.0")
    parser.add_argument("--agent-command", nargs="+")
    kit_source_group = parser.add_mutually_exclusive_group()
    kit_source_group.add_argument(
        "--kit-cli",
        type=Path,
        default=ROOT / "dist" / "cli.js",
    )
    kit_source_group.add_argument("--kit-package", type=Path)
    parser.add_argument("--turn-limit", type=int)
    parser.add_argument(
        "--sandbox",
        choices=("read-only", "workspace-write", "danger-full-access"),
    )
    parser.add_argument("--isolation-image")
    args = parser.parse_args()
    if args.turn_limit is not None and args.turn_limit <= 0:
        parser.error("--turn-limit must be a positive integer")
    if args.sandbox is None:
        if args.turn_limit is None:
            parser.error(
                "a full lifecycle run requires an explicit --sandbox; use "
                "danger-full-access only inside the documented disposable "
                "container topology"
            )
        args.sandbox = "workspace-write"

    scenario = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    output_root = args.output_dir.resolve()
    if output_root.exists():
        parser.error(f"output directory already exists: {output_root}")
    output_root.mkdir(parents=True)
    if args.kit_package:
        kit_source = args.kit_package.resolve()
        kit_source_kind = "packed npm tarball"
        kit_command = [
            process_npm(),
            "exec",
            "--yes",
            "--package",
            str(kit_source),
            "--",
            "ai-sdlc",
        ]
    else:
        kit_source = args.kit_cli.resolve()
        kit_source_kind = "built CLI"
        kit_command = [process_node(), str(kit_source)]
    if args.arm in {"with-kit", "both"} and not kit_source.is_file():
        parser.error(f"adopter source not found: {kit_source}")

    agent_command = (
        args.agent_command
        if args.agent_command
        else default_agent_command(args.codex_package_version)
    )
    arms = ["baseline", "with-kit"] if args.arm == "both" else [args.arm]
    reports: list[dict[str, Any]] = []
    try:
        for arm in arms:
            reports.append(
                run_arm(
                    arm=arm,
                    output_root=output_root,
                    scenario=scenario,
                    agent_command=agent_command,
                    model=args.model,
                    turn_limit=args.turn_limit,
                    kit_command=kit_command,
                    kit_source=kit_source,
                    kit_source_kind=kit_source_kind,
                    codex_package_version=args.codex_package_version,
                    sandbox=args.sandbox,
                    isolation_image=args.isolation_image,
                )
            )
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    comparison(reports, output_root)
    if all(report["passed"] for report in reports):
        label = (
            "PROBE PASS"
            if all(report["probe_passed"] is not None for report in reports)
            else "PASS"
        )
        print(f"{label}: {scenario['id']} ({', '.join(arms)})")
        return 0
    print(f"FAIL: {scenario['id']} ({', '.join(arms)})", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
