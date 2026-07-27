#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import {
  lstat,
  mkdir,
  readFile,
  readdir,
  rmdir,
  unlink,
  writeFile,
} from "node:fs/promises";
import { dirname, join, relative, resolve, sep } from "node:path";
import { stdin, stdout } from "node:process";
import { createInterface } from "node:readline/promises";
import { fileURLToPath } from "node:url";

type PayloadFile = {
  path: string;
  content: Buffer;
  hash: string;
};

type PlannedChange = {
  file: PayloadFile;
  action: "ADD" | "UPDATE";
  content: Buffer;
  previous: Buffer | null;
};

type AppliedFile = {
  path: string;
  previous: Buffer | null;
};

type PackageMetadata = {
  name: string;
  version: string;
};

type CommandRole =
  | "format"
  | "lint"
  | "typecheck"
  | "unit_test"
  | "integration_test"
  | "build"
  | "security"
  | "pre_commit";

type ProjectCommands = Partial<Record<CommandRole, string[]>>;

type ManagedRegionTarget = {
  path: string;
  content: Buffer;
  startMarker: string;
  endMarker: string;
  regionId: string;
  atomicGroup: string;
};

type HookIntegration = {
  regions: ManagedRegionTarget[];
  message: string;
};

const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const templateRoot = join(packageRoot, "repo-template");
const excludedPaths = new Set([".ai/ADOPTION.md", ".ai/kit-version.json"]);
const regionStart = "<!-- ai-sdlc:workflow:start -->";
const regionEnd = "<!-- ai-sdlc:workflow:end -->";
const hookRegionStart = "# ai-sdlc:pre-commit:start";
const hookRegionEnd = "# ai-sdlc:pre-commit:end";
const sharedPaths = new Set([
  ".github/copilot-instructions.md",
  "AGENTS.md",
  "CLAUDE.md",
]);
const commandCandidates: Array<[CommandRole, string[]]> = [
  ["format", ["format:check", "format"]],
  ["lint", ["lint"]],
  ["typecheck", ["typecheck", "type-check"]],
  ["unit_test", ["test:unit", "test"]],
  ["integration_test", ["test:integration", "test:e2e"]],
  ["build", ["build"]],
  ["security", ["security"]],
  ["pre_commit", ["precommit", "pre-commit", "lint:staged"]],
];

function hash(content: Buffer | string): string {
  return createHash("sha256").update(content).digest("hex");
}

function portablePath(path: string): string {
  return path.split(sep).join("/");
}

function occurrences(content: string, marker: string): number {
  return content.split(marker).length - 1;
}

function managedRegion(
  content: Buffer,
  startMarker = regionStart,
  endMarker = regionEnd,
): Buffer | null {
  const text = content.toString("utf8");
  if (
    occurrences(text, startMarker) !== 1 ||
    occurrences(text, endMarker) !== 1
  ) {
    return null;
  }
  const start = text.indexOf(startMarker);
  const end = text.indexOf(endMarker, start);
  if (end < start) {
    return null;
  }
  return Buffer.from(text.slice(start, end + endMarker.length));
}

function mergeManagedRegion(
  current: Buffer,
  target: Buffer,
  startMarker = regionStart,
  endMarker = regionEnd,
): Buffer | null {
  const text = current.toString("utf8");
  const hasMarker = text.includes(startMarker) || text.includes(endMarker);
  if (!hasMarker) {
    const targetRegion = managedRegion(target, startMarker, endMarker);
    if (targetRegion === null) {
      throw new Error("Shared template is missing its managed region.");
    }
    let separator = "";
    if (current.length > 0) {
      separator = current[current.length - 1] === 10 ? "\n" : "\n\n";
    }
    return Buffer.concat([
      current,
      Buffer.from(separator),
      targetRegion,
      Buffer.from("\n"),
    ]);
  }

  const currentRegion = managedRegion(current, startMarker, endMarker);
  const targetRegion = managedRegion(target, startMarker, endMarker);
  if (
    currentRegion !== null &&
    targetRegion !== null &&
    currentRegion.equals(targetRegion)
  ) {
    return current;
  }
  return null;
}

async function collectPayload(
  directory = templateRoot,
): Promise<PayloadFile[]> {
  const files: PayloadFile[] = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.name === "__pycache__") {
      continue;
    }
    const source = join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await collectPayload(source)));
      continue;
    }
    if (!entry.isFile() || entry.name.endsWith(".pyc")) {
      continue;
    }
    const path = portablePath(relative(templateRoot, source));
    if (excludedPaths.has(path)) {
      continue;
    }
    const content = await readFile(source);
    files.push({ path, content, hash: hash(content) });
  }
  return files.sort((left, right) => left.path.localeCompare(right.path));
}

function repositoryRoot(): string {
  try {
    return execFileSync("git", ["rev-parse", "--show-toplevel"], {
      cwd: process.cwd(),
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    throw new Error("Run this command inside a Git repository.");
  }
}

function worktreeStatus(root: string): string {
  return execFileSync(
    "git",
    ["status", "--porcelain", "--untracked-files=all"],
    { cwd: root, encoding: "utf8" },
  ).trim();
}

async function existingContent(path: string): Promise<Buffer | null | false> {
  try {
    const metadata = await lstat(path);
    if (!metadata.isFile()) {
      return false;
    }
    return await readFile(path);
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    if (code === "ENOENT") {
      return null;
    }
    if (code === "ENOTDIR") {
      return false;
    }
    throw error;
  }
}

async function packageManager(root: string, declared?: string): Promise<string> {
  const name = declared?.split("@")[0];
  if (name === "pnpm" || name === "yarn" || name === "bun" || name === "npm") {
    return name;
  }
  const lockfiles: Array<[string, string]> = [
    ["pnpm-lock.yaml", "pnpm"],
    ["yarn.lock", "yarn"],
    ["bun.lock", "bun"],
    ["bun.lockb", "bun"],
  ];
  for (const [lockfile, manager] of lockfiles) {
    if ((await existingContent(join(root, lockfile))) !== null) {
      return manager;
    }
  }
  return "npm";
}

function addCommand(
  commands: ProjectCommands,
  role: CommandRole,
  command: string,
): void {
  const existing = commands[role] ?? [];
  if (!existing.includes(command)) {
    commands[role] = [...existing, command];
  }
}

async function detectPackageCommands(root: string): Promise<ProjectCommands> {
  const packageFile = await existingContent(join(root, "package.json"));
  if (!(packageFile instanceof Buffer)) {
    return {};
  }
  const project = JSON.parse(packageFile.toString("utf8")) as {
    packageManager?: string;
    scripts?: Record<string, unknown>;
  };
  const manager = await packageManager(root, project.packageManager);
  const commands: ProjectCommands = {};
  for (const [role, candidates] of commandCandidates) {
    const script = candidates.find(
      (candidate) => typeof project.scripts?.[candidate] === "string",
    );
    if (script !== undefined) {
      addCommand(commands, role, `${manager} run ${script}`);
    }
  }
  return commands;
}

async function detectPythonCommands(root: string): Promise<ProjectCommands> {
  const pyproject = await existingContent(join(root, "pyproject.toml"));
  if (!(pyproject instanceof Buffer)) {
    return {};
  }
  const content = pyproject.toString("utf8");
  const hasSection = (name: string): boolean =>
    new RegExp(`^\\[tool\\.${name}(?:\\.|\\])`, "m").test(content);
  const commands: ProjectCommands = {};
  if (hasSection("ruff\\.format")) {
    addCommand(commands, "format", "python -m ruff format --check .");
  } else if (hasSection("black")) {
    addCommand(commands, "format", "python -m black --check .");
  }
  if (hasSection("ruff")) {
    addCommand(commands, "lint", "python -m ruff check .");
  }
  if (hasSection("mypy")) {
    addCommand(commands, "typecheck", "python -m mypy .");
  }
  if (hasSection("pytest")) {
    addCommand(commands, "unit_test", "python -m pytest");
  }
  if (hasSection("bandit")) {
    addCommand(commands, "security", "python -m bandit -r .");
  }
  return commands;
}

async function detectProjectCommands(root: string): Promise<ProjectCommands> {
  const commands: ProjectCommands = {};
  for (const detected of [
    await detectPackageCommands(root),
    await detectPythonCommands(root),
  ]) {
    for (const [role, values] of Object.entries(detected)) {
      for (const command of values) {
        addCommand(commands, role as CommandRole, command);
      }
    }
  }
  return commands;
}

function configureProjectCommands(
  files: PayloadFile[],
  commands: ProjectCommands,
): PayloadFile[] {
  if (Object.keys(commands).length === 0) {
    return files;
  }
  return files.map((file) => {
    if (file.path !== "ai-sdlc.yaml") {
      return file;
    }
    let config = file.content.toString("utf8");
    for (const [role, roleCommands] of Object.entries(commands)) {
      config = config.replace(
        `  ${role}: []`,
        `  ${role}: ${JSON.stringify(roleCommands)}`,
      );
    }
    const content = Buffer.from(config);
    return { ...file, content, hash: hash(content) };
  });
}

function huskyRegion(commands: ProjectCommands): ManagedRegionTarget {
  const lines = commands.pre_commit ?? [];
  return {
    path: ".husky/pre-commit",
    content: Buffer.from(
      [hookRegionStart, ...lines, hookRegionEnd].join("\n"),
    ),
    startMarker: hookRegionStart,
    endMarker: hookRegionEnd,
    regionId: "ai-sdlc-pre-commit",
    atomicGroup: "local-quality",
  };
}

async function detectHookIntegration(
  root: string,
  commands: ProjectCommands,
): Promise<HookIntegration> {
  const husky = await existingContent(join(root, ".husky", "pre-commit"));
  const pythonPreCommit = await existingContent(
    join(root, ".pre-commit-config.yaml"),
  );
  const hasHusky = husky instanceof Buffer;
  const hasPythonPreCommit = pythonPreCommit instanceof Buffer;
  if (hasHusky && hasPythonPreCommit) {
    return {
      regions: [],
      message:
        "Both Husky and Python pre-commit are present; hook composition was skipped to avoid duplicate checks.",
    };
  }
  if (hasPythonPreCommit) {
    return {
      regions: [],
      message:
        "Existing Python pre-commit configuration was preserved as the hook source of truth.",
    };
  }
  if (hasHusky && (commands.pre_commit?.length ?? 0) > 0) {
    return {
      regions: [huskyRegion(commands)],
      message: "Existing Husky hook and explicit pre-commit script detected.",
    };
  }
  if (hasHusky) {
    return {
      regions: [],
      message:
        "Existing Husky hook was preserved; no explicit pre-commit script was found.",
    };
  }
  return {
    regions: [],
    message: "No existing hook manager detected; no hook tooling was installed.",
  };
}

function ownership(path: string): "kit" | "project" | "shared" {
  if (path === "ai-sdlc.yaml") {
    return "project";
  }
  if (sharedPaths.has(path)) {
    return "shared";
  }
  return "kit";
}

function releaseDigest(files: PayloadFile[]): string {
  const manifest = files
    .map((file) => `${file.path}\0${file.hash}`)
    .join("\n");
  return hash(manifest);
}

function managedUnit(file: PayloadFile): Record<string, unknown> {
  const common = {
    path: file.path,
    ownership: ownership(file.path),
    atomic_group: "workflow-core",
  };
  if (!sharedPaths.has(file.path)) {
    return {
      ...common,
      kind: "file",
      baseline_hash: file.hash,
    };
  }

  const region = managedRegion(file.content);
  if (region === null) {
    throw new Error(`Shared template is missing markers: ${file.path}`);
  }
  return {
    ...common,
    kind: "region",
    region_id: "ai-sdlc-workflow",
    start_marker: regionStart,
    end_marker: regionEnd,
    baseline_hash: hash(region),
  };
}

function managedProjectRegionUnit(
  target: ManagedRegionTarget,
): Record<string, unknown> {
  const region = managedRegion(
    target.content,
    target.startMarker,
    target.endMarker,
  );
  if (region === null) {
    throw new Error(`Project region is missing markers: ${target.path}`);
  }
  return {
    path: target.path,
    kind: "region",
    region_id: target.regionId,
    start_marker: target.startMarker,
    end_marker: target.endMarker,
    baseline_hash: hash(region),
    ownership: "shared",
    atomic_group: target.atomicGroup,
  };
}

function installationLock(
  metadata: PackageMetadata,
  files: PayloadFile[],
  releaseManifestDigest: string,
  projectRegions: ManagedRegionTarget[],
): string {
  return `${JSON.stringify(
    {
      schema_version: 1,
      kit_version: metadata.version,
      source: {
        package: metadata.name,
        cli_version: metadata.version,
        release_manifest_digest: releaseManifestDigest,
      },
      adapters: ["codex", "claude", "copilot"],
      migrations: ["0001-initial-layout"],
      managed_units: [
        ...files.map(managedUnit),
        ...projectRegions.map(managedProjectRegionUnit),
      ],
    },
    null,
    2,
  )}\n`;
}

async function ensureParent(
  path: string,
  root: string,
  createdDirectories: string[],
): Promise<void> {
  const missing: string[] = [];
  let current = dirname(path);
  while (current !== root) {
    try {
      const metadata = await lstat(current);
      if (!metadata.isDirectory()) {
        const path = portablePath(relative(root, current));
        throw new Error(`${path} is not a directory`);
      }
      break;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
        throw error;
      }
      missing.push(current);
      current = dirname(current);
    }
  }
  for (const directory of missing.reverse()) {
    await mkdir(directory);
    createdDirectories.push(directory);
  }
}

async function rollback(
  files: AppliedFile[],
  directories: string[],
): Promise<void> {
  for (const file of files.reverse()) {
    if (file.previous === null) {
      await unlink(file.path).catch(() => undefined);
    } else {
      await writeFile(file.path, file.previous).catch(() => undefined);
    }
  }
  for (const directory of directories.reverse()) {
    await rmdir(directory).catch(() => undefined);
  }
}

async function confirmed(): Promise<boolean> {
  const prompt = createInterface({ input: stdin, output: stdout });
  try {
    const answer = (await prompt.question("Apply this adoption? [y/N] "))
      .trim()
      .toLowerCase();
    return answer === "y" || answer === "yes";
  } finally {
    prompt.close();
  }
}

async function main(): Promise<number> {
  const metadata = JSON.parse(
    await readFile(join(packageRoot, "package.json"), "utf8"),
  ) as PackageMetadata;
  const root = repositoryRoot();
  const lockPath = join(root, ".ai", "kit.lock.json");

  if ((await existingContent(lockPath)) !== null) {
    console.error(
      "This repository already has an AI SDLC lock. Update handling is not part of this alpha slice.",
    );
    return 1;
  }

  const releasePayload = await collectPayload();
  const commands = await detectProjectCommands(root);
  const payload = configureProjectCommands(releasePayload, commands);
  const hookIntegration = await detectHookIntegration(root, commands);
  const changes: PlannedChange[] = [];
  const unchanged: PayloadFile[] = [];
  const conflicts: PayloadFile[] = [];

  for (const file of payload) {
    const current = await existingContent(join(root, file.path));
    if (current === null) {
      changes.push({
        file,
        action: "ADD",
        content: file.content,
        previous: null,
      });
    } else if (current === false) {
      conflicts.push(file);
    } else if (sharedPaths.has(file.path)) {
      const merged = mergeManagedRegion(current, file.content);
      if (merged === null) {
        conflicts.push(file);
      } else if (merged.equals(current)) {
        unchanged.push(file);
      } else {
        changes.push({
          file,
          action: "UPDATE",
          content: merged,
          previous: current,
        });
      }
    } else if (current.equals(file.content)) {
      unchanged.push(file);
    } else {
      conflicts.push(file);
    }
  }
  for (const target of hookIntegration.regions) {
    const file = {
      path: target.path,
      content: target.content,
      hash: hash(target.content),
    };
    const current = await existingContent(join(root, target.path));
    if (!(current instanceof Buffer)) {
      conflicts.push(file);
      continue;
    }
    const merged = mergeManagedRegion(
      current,
      target.content,
      target.startMarker,
      target.endMarker,
    );
    if (merged === null) {
      conflicts.push(file);
    } else if (merged.equals(current)) {
      unchanged.push(file);
    } else {
      changes.push({
        file,
        action: "UPDATE",
        content: merged,
        previous: current,
      });
    }
  }

  console.log(`AI SDLC ${metadata.version}`);
  console.log(`Repository: ${root}`);
  const detectedRoles = Object.keys(commands);
  if (detectedRoles.length > 0) {
    console.log(`Detected project commands: ${detectedRoles.join(", ")}`);
  }
  console.log(`Hook integration: ${hookIntegration.message}`);
  console.log("Adoption preview:");
  for (const change of changes) {
    console.log(`  ${change.action.padEnd(9)} ${change.file.path}`);
  }
  for (const file of unchanged) {
    console.log(`  UNCHANGED ${file.path}`);
  }
  for (const file of conflicts) {
    console.log(`  CONFLICT  ${file.path}`);
  }
  console.log("  ADD       .ai/kit.lock.json");

  if (conflicts.length > 0) {
    console.error(
      "\nNo files were changed. Resolve the listed same-path collisions and rerun.",
    );
    return 1;
  }

  if (worktreeStatus(root)) {
    console.log("\nWorktree has uncommitted changes; preview remains read-only.");
    console.error("Apply blocked. Commit or stash the existing work, then rerun.");
    return 1;
  }

  if (!(await confirmed())) {
    console.log("\nNo files changed.");
    return 0;
  }

  const lock = Buffer.from(
    installationLock(
      metadata,
      payload,
      releaseDigest(releasePayload),
      hookIntegration.regions,
    ),
  );
  const writtenFiles: AppliedFile[] = [];
  const createdDirectories: string[] = [];
  try {
    for (const change of changes) {
      const destination = join(root, change.file.path);
      await ensureParent(destination, root, createdDirectories);
      if (change.previous === null) {
        await writeFile(destination, change.content, { flag: "wx" });
        writtenFiles.push({ path: destination, previous: null });
      } else {
        const current = await readFile(destination);
        if (!current.equals(change.previous)) {
          throw new Error(
            `File changed after preview: ${change.file.path}`,
          );
        }
        writtenFiles.push({ path: destination, previous: change.previous });
        await writeFile(destination, change.content);
      }
    }
    await ensureParent(lockPath, root, createdDirectories);
    await writeFile(lockPath, lock, { flag: "wx" });
    writtenFiles.push({ path: lockPath, previous: null });

    for (const file of payload) {
      const installed = await readFile(join(root, file.path));
      const expected = sharedPaths.has(file.path)
        ? managedRegion(file.content)
        : file.content;
      const observed = sharedPaths.has(file.path)
        ? managedRegion(installed)
        : installed;
      if (
        expected === null ||
        observed === null ||
        hash(observed) !== hash(expected)
      ) {
        throw new Error(`Installed content failed validation: ${file.path}`);
      }
    }
    for (const target of hookIntegration.regions) {
      const installed = await readFile(join(root, target.path));
      const expected = managedRegion(
        target.content,
        target.startMarker,
        target.endMarker,
      );
      const observed = managedRegion(
        installed,
        target.startMarker,
        target.endMarker,
      );
      if (
        expected === null ||
        observed === null ||
        hash(observed) !== hash(expected)
      ) {
        throw new Error(
          `Installed content failed validation: ${target.path}`,
        );
      }
    }
    JSON.parse(await readFile(lockPath, "utf8"));
  } catch (error) {
    await rollback(writtenFiles, createdDirectories);
    console.error(
      `Adoption failed and written files were restored: ${(error as Error).message}`,
    );
    return 1;
  }

  console.log("\nAdoption installed and verified.");
  console.log(
    "Next: review the Git diff and detected commands in ai-sdlc.yaml.",
  );
  return 0;
}

main()
  .then((status) => {
    process.exitCode = status;
  })
  .catch((error: unknown) => {
    console.error((error as Error).message);
    process.exitCode = 1;
  });
