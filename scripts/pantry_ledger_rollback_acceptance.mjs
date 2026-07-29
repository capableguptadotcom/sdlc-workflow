#!/usr/bin/env node

import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
if (args.length !== 2) {
  console.error(
    "Usage: node scripts/pantry_ledger_rollback_acceptance.mjs <current-workspace> <previous-workspace>",
  );
  process.exitCode = 2;
} else {
  await main(resolve(args[0]), resolve(args[1]));
}

async function availablePort() {
  const probe = createServer();
  await new Promise((resolvePromise, reject) => {
    probe.once("error", reject);
    probe.listen(0, "127.0.0.1", resolvePromise);
  });
  const { port } = probe.address();
  await new Promise((resolvePromise, reject) => {
    probe.close((error) => (error ? reject(error) : resolvePromise()));
  });
  return port;
}

async function startApplication(workspace, dataFile, label) {
  const port = await availablePort();
  const child = spawn(process.execPath, ["src/server.js"], {
    cwd: workspace,
    env: {
      ...process.env,
      PANTRY_DATA_FILE: dataFile,
      PORT: String(port),
    },
    stdio: ["ignore", "pipe", "pipe"],
  });
  let stdout = "";
  let stderr = "";
  child.stdout.on("data", (chunk) => {
    stdout += chunk.toString();
  });
  child.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });
  const application = {
    baseUrl: `http://127.0.0.1:${port}`,
    child,
    label,
    stdout: () => stdout,
    stderr: () => stderr,
  };
  const deadline = Date.now() + 8_000;
  while (Date.now() < deadline && child.exitCode === null) {
    try {
      const response = await fetch(`${application.baseUrl}/health`);
      if (response.ok) {
        return application;
      }
    } catch {
      // The process may still be starting.
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));
  }
  await stopApplication(application);
  throw new Error(
    `${label} failed to become healthy (exit=${child.exitCode}): ${stderr}`,
  );
}

async function stopApplication(application) {
  if (!application || application.child.exitCode !== null) {
    return;
  }
  const exited = new Promise((resolvePromise) =>
    application.child.once("exit", resolvePromise),
  );
  application.child.kill();
  await Promise.race([
    exited,
    new Promise((resolvePromise) => setTimeout(resolvePromise, 3_000)),
  ]);
  if (application.child.exitCode === null) {
    const killed = new Promise((resolvePromise) =>
      application.child.once("exit", resolvePromise),
    );
    application.child.kill("SIGKILL");
    await Promise.race([
      killed,
      new Promise((resolvePromise) => setTimeout(resolvePromise, 3_000)),
    ]);
  }
}

async function requestJson(baseUrl, path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, options);
  const body = await response.text();
  let json;
  try {
    json = JSON.parse(body);
  } catch {
    json = null;
  }
  return { response, body, json };
}

function movementOptions(body, key) {
  return {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "idempotency-key": key,
    },
    body,
  };
}

function itemFrom(inventory, name) {
  assert.ok(inventory && Array.isArray(inventory.items), "inventory has items");
  const item = inventory.items.find((candidate) => candidate.name === name);
  assert.ok(item, `inventory contains ${name}`);
  return item;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

async function assertReadableRelease(application) {
  const health = await fetch(`${application.baseUrl}/health`);
  assert.equal(
    health.status,
    200,
    `${application.label} health is not readable`,
  );
  const inventory = await requestJson(application.baseUrl, "/api/inventory");
  assert.equal(
    inventory.response.status,
    200,
    `${application.label} inventory is not readable: ${inventory.body}`,
  );
  assert.equal(itemFrom(inventory.json, "Rice").quantity, 10);
}

async function main(currentWorkspace, previousWorkspace) {
  const runRoot = await mkdtemp(join(tmpdir(), "pantry-ledger-rollback-"));
  const dataFile = join(runRoot, "pantry.json");
  const key = "rollback-durable-donation-1";
  const body = JSON.stringify({
    item: "Rice",
    kind: "donation",
    quantity: 10,
  });
  const checks = [];
  let rollbackDataSha256;
  let application;
  try {
    application = await startApplication(
      currentWorkspace,
      dataFile,
      "current release",
    );
    const created = await requestJson(
      application.baseUrl,
      "/api/movements",
      movementOptions(body, key),
    );
    assert.ok(
      created.response.status >= 200 && created.response.status < 300,
      created.body,
    );
    await assertReadableRelease(application);
    await stopApplication(application);
    application = undefined;
    const beforeRollback = await readFile(dataFile);
    rollbackDataSha256 = sha256(beforeRollback);
    checks.push("current release persisted inventory and idempotency state");

    application = await startApplication(
      previousWorkspace,
      dataFile,
      "previous release",
    );
    await assertReadableRelease(application);
    await stopApplication(application);
    application = undefined;
    const afterRollback = await readFile(dataFile);
    assert.deepEqual(
      afterRollback,
      beforeRollback,
      "previous release changed the current release data file",
    );
    assert.equal(sha256(afterRollback), rollbackDataSha256);
    checks.push(
      "previous release read health and inventory without changing data bytes",
    );

    application = await startApplication(
      currentWorkspace,
      dataFile,
      "restarted current release",
    );
    const replay = await requestJson(
      application.baseUrl,
      "/api/movements",
      movementOptions(body, key),
    );
    assert.equal(replay.response.status, created.response.status, replay.body);
    assert.deepEqual(replay.json, created.json);
    const inventory = await requestJson(
      application.baseUrl,
      "/api/inventory",
    );
    assert.equal(inventory.response.status, 200, inventory.body);
    assert.equal(itemFrom(inventory.json, "Rice").quantity, 10);
    checks.push(
      "current release replayed the durable key without duplicating stock",
    );

    console.log(
      JSON.stringify(
        {
          passed: true,
          rollback_data_sha256: rollbackDataSha256,
          checks,
        },
        null,
        2,
      ),
    );
  } catch (error) {
    console.error(
      JSON.stringify(
        {
          passed: false,
          checks,
          error: error instanceof Error ? error.message : String(error),
          application: application?.label,
          application_stdout: application?.stdout() ?? "",
          application_stderr: application?.stderr() ?? "",
        },
        null,
        2,
      ),
    );
    process.exitCode = 1;
  } finally {
    await stopApplication(application);
    await rm(runRoot, { recursive: true, force: true });
  }
}
