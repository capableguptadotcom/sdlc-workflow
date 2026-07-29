import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";

const cli = resolve("dist/cli.js");
const packageVersion = JSON.parse(
  await readFile(resolve("package.json"), "utf8"),
).version;

async function repository() {
  const root = await mkdtemp(join(tmpdir(), "ai-sdlc-adopt-"));
  execFileSync("git", ["init", "--quiet"], { cwd: root });
  execFileSync("git", ["config", "user.name", "AI SDLC Test"], { cwd: root });
  execFileSync("git", ["config", "user.email", "test@example.invalid"], {
    cwd: root,
  });
  await writeFile(join(root, "README.md"), "# Existing project\n");
  execFileSync("git", ["add", "-A"], { cwd: root });
  execFileSync("git", ["commit", "--quiet", "-m", "fixture baseline"], {
    cwd: root,
  });
  return root;
}

function run(root, input = "n\n", args = []) {
  return spawnSync(process.execPath, [cli, ...args], {
    cwd: root,
    input,
    encoding: "utf8",
  });
}

test("--help describes the CLI without requiring a Git repository", () => {
  const result = spawnSync(process.execPath, [cli, "--help"], {
    cwd: tmpdir(),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Usage: ai-sdlc/);
  assert.match(result.stdout, /--help/);
  assert.match(result.stdout, /--version/);
  assert.match(result.stdout, /--dry-run/);
  assert.match(result.stdout, /--yes/);
  assert.equal(result.stderr, "");
});

test("--version prints the package version without requiring a Git repository", () => {
  const result = spawnSync(process.execPath, [cli, "--version"], {
    cwd: tmpdir(),
    encoding: "utf8",
  });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout, `${packageVersion}\n`);
  assert.equal(result.stderr, "");
});

test("an unknown argument is rejected before repository discovery", () => {
  const result = spawnSync(process.execPath, [cli, "--surprise"], {
    cwd: tmpdir(),
    encoding: "utf8",
  });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /Unknown argument: --surprise/);
  assert.doesNotMatch(result.stderr, /inside a Git repository/);
});

test("a denied preview makes no changes", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));

  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /ADD\s+AGENTS\.md/);
  assert.match(result.stdout, /No files changed\./);
  assert.equal(existsSync(join(root, "AGENTS.md")), false);
  assert.equal(existsSync(join(root, ".ai", "kit.lock.json")), false);
});

test("--dry-run previews without prompting or changing files", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));

  const result = run(root, "", ["--dry-run"]);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Adoption preview:/);
  assert.match(result.stdout, /Dry run complete\. No files changed\./);
  assert.doesNotMatch(result.stdout, /Apply this adoption/);
  assert.equal(existsSync(join(root, "AGENTS.md")), false);
  assert.equal(existsSync(join(root, ".ai", "kit.lock.json")), false);
});

test("confirmation installs the reviewed payload and lock", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));

  const result = run(root, "yes\n");

  assert.equal(result.status, 0, result.stderr);
  assert.equal(existsSync(join(root, "AGENTS.md")), true);
  assert.equal(existsSync(join(root, "ai-sdlc.yaml")), true);
  assert.equal(
    existsSync(join(root, ".ai", "workflow-walkthrough.html")),
    true,
  );
  assert.equal(existsSync(join(root, ".ai", "ADOPTION.md")), true);
  assert.equal(existsSync(join(root, ".ai", "kit-version.json")), false);

  const lock = JSON.parse(
    await readFile(join(root, ".ai", "kit.lock.json"), "utf8"),
  );
  assert.equal(lock.schema_version, 1);
  assert.equal(lock.kit_version, packageVersion);
  assert.equal(lock.source.package, "@innovate-x/ai-sdlc");
  assert.match(lock.source.release_manifest_digest, /^[a-f0-9]{64}$/);
  assert.ok(
    lock.managed_units.some((unit) => unit.path === "AGENTS.md"),
    "lock should record installed workflow files",
  );
  assert.equal(
    lock.managed_units.find((unit) => unit.path === ".ai/ADOPTION.md").ownership,
    "project",
  );
  const agents = await readFile(join(root, "AGENTS.md"), "utf8");
  assert.match(agents, /<!-- ai-sdlc:workflow:start -->/);
  assert.match(agents, /<!-- ai-sdlc:workflow:end -->/);
  assert.equal(
    lock.managed_units.find((unit) => unit.path === "AGENTS.md").kind,
    "region",
  );
  assert.match(
    result.stdout,
    /No existing hook manager detected; no hook tooling was installed/,
  );
  assert.match(result.stdout, /Adoption installed and verified\./);
});

test("--yes installs without prompting when safeguards pass", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));

  const result = run(root, "", ["--yes"]);

  assert.equal(result.status, 0, result.stderr);
  assert.doesNotMatch(result.stdout, /Apply this adoption/);
  assert.match(result.stdout, /Adoption installed and verified\./);
  assert.equal(existsSync(join(root, ".ai", "kit.lock.json")), true);
});

test("a same-version rerun validates the installation and ignores project-owned configuration", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));

  const installed = run(root, "yes\n");
  assert.equal(installed.status, 0, installed.stderr);
  const kitFile = join(root, ".agents", "skills", "develop", "SKILL.md");
  const kitContent = await readFile(kitFile, "utf8");
  const projectConfig = "# Project-owned AI SDLC configuration\n";
  await writeFile(join(root, "ai-sdlc.yaml"), projectConfig);
  const sharedPath = join(root, "AGENTS.md");
  const managedInstructions = await readFile(sharedPath, "utf8");
  const sharedWithProjectContent =
    `# Project instructions\n\n${managedInstructions}\nProject footer\n`;
  await writeFile(sharedPath, sharedWithProjectContent);

  const result = run(root);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /already installed/i);
  assert.match(result.stdout, /validated/i);
  assert.match(result.stdout, /no changes/i);
  assert.doesNotMatch(result.stdout, /Apply this adoption/);
  assert.equal(await readFile(kitFile, "utf8"), kitContent);
  assert.equal(await readFile(join(root, "ai-sdlc.yaml"), "utf8"), projectConfig);
  assert.equal(await readFile(sharedPath, "utf8"), sharedWithProjectContent);
});

test("a lock cannot self-authenticate coordinated kit tampering", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));

  const installed = run(root, "yes\n");
  assert.equal(installed.status, 0, installed.stderr);
  const kitRelativePath = ".agents/skills/develop/SKILL.md";
  const kitPath = join(root, ...kitRelativePath.split("/"));
  const tamperedKit = "# Coordinated kit tampering\n";
  await writeFile(kitPath, tamperedKit);
  const lockPath = join(root, ".ai", "kit.lock.json");
  const lock = JSON.parse(await readFile(lockPath, "utf8"));
  const unit = lock.managed_units.find(
    (candidate) => candidate.path === kitRelativePath,
  );
  unit.baseline_hash =
    "4ea998ddb51c7a36f59de9e531f977ea89b22359f87df4d74693ee0725265da0";
  const tamperedLock = `${JSON.stringify(lock, null, 2)}\n`;
  await writeFile(lockPath, tamperedLock);

  const result = run(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /\.agents\/skills\/develop\/SKILL\.md/);
  assert.match(result.stderr, /no files were changed/i);
  assert.equal(await readFile(kitPath, "utf8"), tamperedKit);
  assert.equal(await readFile(lockPath, "utf8"), tamperedLock);
});

test("a lock cannot omit required release units", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));

  const installed = run(root, "yes\n");
  assert.equal(installed.status, 0, installed.stderr);
  const lockPath = join(root, ".ai", "kit.lock.json");
  const lock = JSON.parse(await readFile(lockPath, "utf8"));
  lock.managed_units = [];
  const emptyLock = `${JSON.stringify(lock, null, 2)}\n`;
  await writeFile(lockPath, emptyLock);
  const kitPath = join(root, ".agents", "skills", "develop", "SKILL.md");
  const kitContent = await readFile(kitPath, "utf8");

  const result = run(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /\.agents\/skills\/develop\/SKILL\.md/);
  assert.match(result.stderr, /AGENTS\.md/);
  assert.match(result.stderr, /no files were changed/i);
  assert.equal(await readFile(lockPath, "utf8"), emptyLock);
  assert.equal(await readFile(kitPath, "utf8"), kitContent);
});

test("a same-version rerun reports every drifted, missing, or malformed managed unit without changing files", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));

  const installed = run(root, "yes\n");
  assert.equal(installed.status, 0, installed.stderr);
  const driftedPath = join(
    root,
    ".agents",
    "skills",
    "develop",
    "SKILL.md",
  );
  const missingPath = join(
    root,
    ".agents",
    "skills",
    "review-change",
    "SKILL.md",
  );
  const sharedPath = join(root, "AGENTS.md");
  const drifted = "# Locally drifted kit file\n";
  const malformed =
    "# Project instructions\n\n<!-- ai-sdlc:workflow:start -->\nIncomplete\n";
  await writeFile(driftedPath, drifted);
  await rm(missingPath);
  await writeFile(sharedPath, malformed);
  const lock = await readFile(join(root, ".ai", "kit.lock.json"), "utf8");

  const result = run(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /\.agents\/skills\/develop\/SKILL\.md/);
  assert.match(result.stderr, /\.agents\/skills\/review-change\/SKILL\.md/);
  assert.match(result.stderr, /AGENTS\.md/);
  assert.match(result.stderr, /no files were changed/i);
  assert.doesNotMatch(result.stdout, /Apply this adoption/);
  assert.equal(await readFile(driftedPath, "utf8"), drifted);
  assert.equal(existsSync(missingPath), false);
  assert.equal(await readFile(sharedPath, "utf8"), malformed);
  assert.equal(
    await readFile(join(root, ".ai", "kit.lock.json"), "utf8"),
    lock,
  );
});

test("a malformed installation lock is named and leaves the repository unchanged", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));
  const lockPath = join(root, ".ai", "kit.lock.json");
  await mkdir(join(root, ".ai"), { recursive: true });
  const malformed = "{ definitely not valid JSON\n";
  await writeFile(lockPath, malformed);

  const result = run(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /\.ai\/kit\.lock\.json/);
  assert.match(result.stderr, /no files were changed/i);
  assert.equal(await readFile(lockPath, "utf8"), malformed);
  assert.equal(existsSync(join(root, "AGENTS.md")), false);
});

test("a malformed shared-unit lock record names the managed path", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));

  const installed = run(root, "yes\n");
  assert.equal(installed.status, 0, installed.stderr);
  const lockPath = join(root, ".ai", "kit.lock.json");
  const lock = JSON.parse(await readFile(lockPath, "utf8"));
  const agents = lock.managed_units.find((unit) => unit.path === "AGENTS.md");
  delete agents.start_marker;
  const malformed = `${JSON.stringify(lock, null, 2)}\n`;
  await writeFile(lockPath, malformed);

  const result = run(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /AGENTS\.md/);
  assert.match(result.stderr, /no files were changed/i);
  assert.equal(await readFile(lockPath, "utf8"), malformed);
});

test("a different installed kit version is an explicit unsupported update", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));

  const installed = run(root, "yes\n");
  assert.equal(installed.status, 0, installed.stderr);
  const lockPath = join(root, ".ai", "kit.lock.json");
  const lock = JSON.parse(await readFile(lockPath, "utf8"));
  lock.kit_version = "0.0.9";
  const olderLock = `${JSON.stringify(lock, null, 2)}\n`;
  await writeFile(lockPath, olderLock);
  const kitPath = join(root, ".agents", "skills", "develop", "SKILL.md");
  const kitContent = await readFile(kitPath, "utf8");

  const result = run(root);

  assert.equal(result.status, 1);
  assert.match(result.stderr, /unsupported update/i);
  assert.match(result.stderr, /0\.0\.9/);
  assert.ok(result.stderr.includes(packageVersion));
  assert.doesNotMatch(result.stdout, /Apply this adoption/);
  assert.equal(await readFile(lockPath, "utf8"), olderLock);
  assert.equal(await readFile(kitPath, "utf8"), kitContent);
});

test("an existing same-path file stops the complete adoption", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));
  const skill = join(root, ".agents", "skills", "develop", "SKILL.md");
  await mkdir(join(root, ".agents", "skills", "develop"), { recursive: true });
  await writeFile(skill, "# Project-owned develop skill\n");
  execFileSync("git", ["add", "-A"], { cwd: root });
  execFileSync("git", ["commit", "--quiet", "-m", "project skill"], {
    cwd: root,
  });

  const result = run(root, "", ["--yes"]);

  assert.equal(result.status, 1);
  assert.match(result.stdout, /CONFLICT\s+\.agents\/skills\/develop\/SKILL\.md/);
  assert.doesNotMatch(result.stdout, /Apply this adoption/);
  assert.match(result.stderr, /No files were changed/);
  assert.equal(
    await readFile(skill, "utf8"),
    "# Project-owned develop skill\n",
  );
  assert.equal(existsSync(join(root, "ai-sdlc.yaml")), false);
});

test("existing assistant instructions are preserved around one managed region", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));
  await mkdir(join(root, ".github"), { recursive: true });
  const existing = new Map([
    ["AGENTS.md", "# Project instructions\n\nUse the existing build command.\n"],
    ["CLAUDE.md", "# Claude project notes\n\nKeep responses concise.\n"],
    [
      ".github/copilot-instructions.md",
      "# Copilot project notes\n\nUse the repository test helpers.\n",
    ],
  ]);
  for (const [path, content] of existing) {
    await writeFile(join(root, path), content);
  }
  execFileSync("git", ["add", "-A"], { cwd: root });
  execFileSync("git", ["commit", "--quiet", "-m", "assistant instructions"], {
    cwd: root,
  });

  const result = run(root, "yes\n");

  assert.equal(result.status, 0, result.stderr);
  for (const [path, content] of existing) {
    const installed = await readFile(join(root, path), "utf8");
    assert.ok(installed.startsWith(content), `${path} project content changed`);
    assert.equal(
      installed.match(/<!-- ai-sdlc:workflow:start -->/g)?.length,
      1,
    );
    assert.equal(
      installed.match(/<!-- ai-sdlc:workflow:end -->/g)?.length,
      1,
    );
    assert.ok(result.stdout.includes(`UPDATE    ${path}`));
  }

  const lock = JSON.parse(
    await readFile(join(root, ".ai", "kit.lock.json"), "utf8"),
  );
  for (const path of existing.keys()) {
    const unit = lock.managed_units.find((candidate) => candidate.path === path);
    assert.equal(unit.kind, "region");
    assert.equal(unit.ownership, "shared");
    assert.equal(unit.region_id, "ai-sdlc-workflow");
    assert.match(unit.baseline_hash, /^[a-f0-9]{64}$/);
  }
});

test("existing package scripts populate project command roles", async (t) => {
  const root = await repository();
  const plainRoot = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));
  t.after(() => rm(plainRoot, { recursive: true, force: true }));
  await writeFile(
    join(root, "package.json"),
    `${JSON.stringify(
      {
        scripts: {
          "format:check": "prettier --check .",
          lint: "eslint .",
          typecheck: "tsc --noEmit",
          "test:unit": "vitest run",
          "test:integration": "playwright test",
          build: "vite build",
          precommit: "lint-staged",
          check: "a project-specific command with no workflow role",
        },
      },
      null,
      2,
    )}\n`,
  );
  await writeFile(join(root, "package-lock.json"), "{}\n");
  await writeFile(
    join(root, "pyproject.toml"),
    [
      "[tool.ruff]",
      'line-length = 88',
      "",
      "[tool.ruff.format]",
      'quote-style = "double"',
      "",
      "[tool.mypy]",
      "strict = true",
      "",
      "[tool.pytest.ini_options]",
      'testpaths = ["tests"]',
      "",
    ].join("\n"),
  );
  execFileSync("git", ["add", "-A"], { cwd: root });
  execFileSync("git", ["commit", "--quiet", "-m", "project commands"], {
    cwd: root,
  });

  const result = run(root, "yes\n");

  assert.equal(result.status, 0, result.stderr);
  const config = await readFile(join(root, "ai-sdlc.yaml"), "utf8");
  assert.match(
    config,
    /format: \["npm run format:check","python -m ruff format --check \."\]/,
  );
  assert.match(config, /lint: \["npm run lint","python -m ruff check \."\]/);
  assert.match(
    config,
    /typecheck: \["npm run typecheck","python -m mypy \."\]/,
  );
  assert.match(
    config,
    /unit_test: \["npm run test:unit","python -m pytest"\]/,
  );
  assert.match(config, /integration_test: \["npm run test:integration"\]/);
  assert.match(config, /build: \["npm run build"\]/);
  assert.match(config, /security: \[\]/);
  assert.match(config, /pre_commit: \["npm run precommit"\]/);
  assert.doesNotMatch(config, /npm run check/);
  assert.match(
    result.stdout,
    /Detected project commands: format, lint, typecheck, unit_test, integration_test, build, pre_commit/,
  );

  const plainResult = run(plainRoot, "yes\n");
  assert.equal(plainResult.status, 0, plainResult.stderr);
  const configuredLock = JSON.parse(
    await readFile(join(root, ".ai", "kit.lock.json"), "utf8"),
  );
  const plainLock = JSON.parse(
    await readFile(join(plainRoot, ".ai", "kit.lock.json"), "utf8"),
  );
  assert.equal(
    configuredLock.source.release_manifest_digest,
    plainLock.source.release_manifest_digest,
  );
  assert.notEqual(
    configuredLock.managed_units.find(
      (unit) => unit.path === "ai-sdlc.yaml",
    ).baseline_hash,
    plainLock.managed_units.find((unit) => unit.path === "ai-sdlc.yaml")
      .baseline_hash,
  );
});

test("an existing Husky hook receives only cheap mapped checks", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(
    join(root, "package.json"),
    `${JSON.stringify(
      {
        scripts: {
          "format:check": "prettier --check .",
          lint: "eslint .",
          typecheck: "tsc --noEmit",
          test: "vitest run",
          build: "vite build",
          precommit: "lint-staged",
        },
      },
      null,
      2,
    )}\n`,
  );
  await mkdir(join(root, ".husky"), { recursive: true });
  const original = "#!/usr/bin/env sh\n\necho existing-hook\n";
  await writeFile(join(root, ".husky", "pre-commit"), original);
  execFileSync("git", ["add", "-A"], { cwd: root });
  execFileSync("git", ["commit", "--quiet", "-m", "husky hook"], {
    cwd: root,
  });

  const result = run(root, "yes\n");

  assert.equal(result.status, 0, result.stderr);
  const hook = await readFile(join(root, ".husky", "pre-commit"), "utf8");
  assert.ok(hook.startsWith(original));
  assert.match(hook, /# ai-sdlc:pre-commit:start/);
  assert.match(hook, /npm run precommit/);
  assert.doesNotMatch(
    hook,
    /npm run format:check|npm run lint|typecheck|vitest|build/,
  );
  assert.match(result.stdout, /UPDATE\s+\.husky\/pre-commit/);

  const lock = JSON.parse(
    await readFile(join(root, ".ai", "kit.lock.json"), "utf8"),
  );
  const unit = lock.managed_units.find(
    (candidate) => candidate.path === ".husky/pre-commit",
  );
  assert.equal(unit.kind, "region");
  assert.equal(unit.region_id, "ai-sdlc-pre-commit");

  const rerun = run(root);
  assert.equal(rerun.status, 0, rerun.stderr);
  assert.match(rerun.stdout, /already installed/i);
  assert.match(rerun.stdout, /validated/i);
});

test("an existing Python pre-commit config remains the hook source of truth", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(
    join(root, "pyproject.toml"),
    [
      "[tool.ruff]",
      'line-length = 88',
      "",
      "[tool.ruff.format]",
      'quote-style = "double"',
      "",
      "[tool.mypy]",
      "strict = true",
      "",
      "[tool.pytest.ini_options]",
      'testpaths = ["tests"]',
      "",
    ].join("\n"),
  );
  const original =
    "repos:\n  - repo: local\n    hooks:\n      - id: existing\n        name: Existing hook\n        entry: python -m compileall src\n        language: system\n";
  await writeFile(join(root, ".pre-commit-config.yaml"), original);
  execFileSync("git", ["add", "-A"], { cwd: root });
  execFileSync("git", ["commit", "--quiet", "-m", "python pre-commit"], {
    cwd: root,
  });

  const result = run(root, "yes\n");

  assert.equal(result.status, 0, result.stderr);
  const config = await readFile(
    join(root, ".pre-commit-config.yaml"),
    "utf8",
  );
  assert.equal(config, original);
  assert.doesNotMatch(config, /# ai-sdlc:pre-commit:start/);
  assert.match(
    result.stdout,
    /Existing Python pre-commit configuration was preserved as the hook source of truth/,
  );
});

test("multiple existing hook managers are preserved without duplicate checks", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(
    join(root, "package.json"),
    `${JSON.stringify({ scripts: { precommit: "lint-staged" } }, null, 2)}\n`,
  );
  await mkdir(join(root, ".husky"), { recursive: true });
  const husky = "#!/usr/bin/env sh\n\necho husky\n";
  const python = "repos:\n  - repo: local\n    hooks: []\n";
  await writeFile(join(root, ".husky", "pre-commit"), husky);
  await writeFile(join(root, ".pre-commit-config.yaml"), python);
  execFileSync("git", ["add", "-A"], { cwd: root });
  execFileSync("git", ["commit", "--quiet", "-m", "multiple hook managers"], {
    cwd: root,
  });

  const result = run(root, "yes\n");

  assert.equal(result.status, 0, result.stderr);
  assert.equal(
    await readFile(join(root, ".husky", "pre-commit"), "utf8"),
    husky,
  );
  assert.equal(
    await readFile(join(root, ".pre-commit-config.yaml"), "utf8"),
    python,
  );
  assert.match(
    result.stdout,
    /hook composition was skipped to avoid duplicate checks/,
  );
  const lock = JSON.parse(
    await readFile(join(root, ".ai", "kit.lock.json"), "utf8"),
  );
  assert.equal(
    lock.managed_units.some(
      (unit) =>
        unit.path === ".husky/pre-commit" ||
        unit.path === ".pre-commit-config.yaml",
    ),
    false,
  );
});

test("a malformed managed region stops without changing other files", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));
  const agents =
    "# Project instructions\n\n<!-- ai-sdlc:workflow:start -->\nIncomplete\n";
  await writeFile(join(root, "AGENTS.md"), agents);
  execFileSync("git", ["add", "AGENTS.md"], { cwd: root });
  execFileSync("git", ["commit", "--quiet", "-m", "malformed managed region"], {
    cwd: root,
  });

  const result = run(root, "yes\n");

  assert.equal(result.status, 1);
  assert.match(result.stdout, /CONFLICT\s+AGENTS\.md/);
  assert.equal(await readFile(join(root, "AGENTS.md"), "utf8"), agents);
  assert.equal(existsSync(join(root, "ai-sdlc.yaml")), false);
  assert.equal(existsSync(join(root, ".ai", "kit.lock.json")), false);
});

test("a dirty worktree can be previewed but not changed", async (t) => {
  const root = await repository();
  t.after(() => rm(root, { recursive: true, force: true }));
  await writeFile(join(root, "local-work.txt"), "keep me\n");

  const result = run(root, "", ["--yes"]);

  assert.equal(result.status, 1);
  assert.match(result.stdout, /Worktree has uncommitted changes/);
  assert.doesNotMatch(result.stdout, /Apply this adoption/);
  assert.match(result.stderr, /Apply blocked/);
  assert.equal(existsSync(join(root, "AGENTS.md")), false);
  assert.equal(await readFile(join(root, "local-work.txt"), "utf8"), "keep me\n");
});
