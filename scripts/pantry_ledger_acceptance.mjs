#!/usr/bin/env node

import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

let workspace = "";

if (
  process.argv[1] &&
  resolve(process.argv[1]) === fileURLToPath(import.meta.url)
) {
  const cli = parseArguments(process.argv.slice(2));
  workspace = cli ? resolve(cli.workspace) : "";

  if (!cli) {
    console.error(
      "Usage: node scripts/pantry_ledger_acceptance.mjs <workspace> [--mode feature|full]",
    );
    process.exitCode = 2;
  } else {
    await main(cli.mode);
  }
}

function parseArguments(args) {
  if (args.length === 1) {
    return { workspace: args[0], mode: "full" };
  }
  if (
    args.length === 3 &&
    args[1] === "--mode" &&
    (args[2] === "feature" || args[2] === "full")
  ) {
    return { workspace: args[0], mode: args[2] };
  }
  return null;
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

async function startApplication(dataFile) {
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
  const baseUrl = `http://127.0.0.1:${port}`;
  const deadline = Date.now() + 8_000;
  while (Date.now() < deadline && child.exitCode === null) {
    try {
      const response = await fetch(`${baseUrl}/health`);
      if (response.ok) {
        return { baseUrl, child, stdout: () => stdout, stderr: () => stderr };
      }
    } catch {
      // The process may still be starting.
    }
    await new Promise((resolvePromise) => setTimeout(resolvePromise, 100));
  }
  return { baseUrl, child, stdout: () => stdout, stderr: () => stderr };
}

async function stopApplication(application) {
  if (application.child.exitCode !== null) {
    return;
  }
  application.child.kill();
  await Promise.race([
    new Promise((resolvePromise) =>
      application.child.once("exit", resolvePromise),
    ),
    new Promise((resolvePromise) => setTimeout(resolvePromise, 3_000)),
  ]);
  if (application.child.exitCode === null) {
    application.child.kill("SIGKILL");
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

function movement(item, kind, quantity, lowStockThreshold) {
  return JSON.stringify({
    item,
    kind,
    quantity,
    ...(lowStockThreshold === undefined ? {} : { lowStockThreshold }),
  });
}

function movementOptions(body, key) {
  const headers = {
    "content-type": "application/json",
  };
  if (key !== undefined) {
    headers["idempotency-key"] = key;
  }
  return {
    method: "POST",
    headers,
    body,
  };
}

function riceFrom(inventory) {
  assert.ok(inventory && Array.isArray(inventory.items), "inventory has items");
  const rice = inventory.items.find((item) => item.name === "Rice");
  assert.ok(rice, "inventory contains Rice");
  return rice;
}

function getAttribute(tag, name) {
  const match = tag.match(
    new RegExp(
      `(?:^|\\s)${name}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^\\s>]+))`,
      "i",
    ),
  );
  return match ? (match[1] ?? match[2] ?? match[3]) : undefined;
}

function hasAttribute(tag, name) {
  return new RegExp(`(?:^|\\s)${name}(?=\\s*=|[\\s/>])`, "i").test(tag);
}

function stripTags(value) {
  return value.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function hasAssociatedLabel(control, html) {
  const ariaLabel = getAttribute(control, "aria-label");
  if (ariaLabel?.trim()) {
    return true;
  }

  const labelledBy = getAttribute(control, "aria-labelledby");
  if (
    labelledBy
      ?.split(/\s+/)
      .some((id) =>
        [...html.matchAll(/<[^>]+\bid\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)[^>]*>/gi)]
          .map(([tag]) => getAttribute(tag, "id"))
          .includes(id),
      )
  ) {
    return true;
  }

  const id = getAttribute(control, "id");
  if (
    id &&
    [...html.matchAll(/<label\b[^>]*>/gi)].some(
      ([label]) => getAttribute(label, "for") === id,
    )
  ) {
    return true;
  }

  return [...html.matchAll(/<label\b[^>]*>[\s\S]*?<\/label>/gi)].some(
    ([label]) => label.includes(control),
  );
}

function assertAssociatedMovementControls(form, html) {
  const controls = [
    ...form.matchAll(/<(?:input|select|textarea)\b[^>]*>/gi),
  ].map(([control]) => control);
  const fields = [
    ["item", /item|name/i],
    ["kind", /kind|type/i],
    ["quantity", /quantity|amount/i],
  ];

  for (const [field, pattern] of fields) {
    const candidates = controls.filter((control) =>
      pattern.test(
        `${getAttribute(control, "name") ?? ""} ${
          getAttribute(control, "id") ?? ""
        }`,
      ),
    );
    assert.ok(candidates.length > 0, `UI has a ${field} form control`);
    assert.ok(
      candidates.some((control) => hasAssociatedLabel(control, html)),
      `UI associates a label with the ${field} control`,
    );
  }
}

function assertSubmitAffordance(form) {
  const buttons = [
    ...form.matchAll(/<button\b[^>]*>[\s\S]*?<\/button>/gi),
    ...form.matchAll(/<input\b[^>]*>/gi),
  ].map(([button]) => button);
  const submit = buttons.find((button) => {
    if (hasAttribute(button, "disabled")) {
      return false;
    }
    const type = getAttribute(button, "type")?.toLowerCase();
    const isButton = /^<button\b/i.test(button);
    return type === "submit" || (isButton && type === undefined);
  });
  assert.ok(submit, "UI has an enabled submit affordance");
  assert.ok(
    stripTags(submit).length > 0 ||
      Boolean(getAttribute(submit, "value")?.trim()) ||
      Boolean(getAttribute(submit, "aria-label")?.trim()),
    "submit affordance has an accessible name",
  );
}

async function collectClientScript(baseUrl, html) {
  const scripts = [];
  for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    const [, attributes, inline] = match;
    const src = getAttribute(attributes, "src");
    if (!src) {
      scripts.push(inline);
      continue;
    }

    const scriptUrl = new URL(src, `${baseUrl}/`);
    assert.equal(
      scriptUrl.origin,
      new URL(baseUrl).origin,
      "UI scripts must be served by the local application",
    );
    const response = await fetch(scriptUrl);
    assert.ok(response.ok, `UI script ${scriptUrl.pathname} is available`);
    scripts.push(await response.text());
  }
  return scripts.join("\n");
}

function stubElement() {
  return {
    children: [],
    className: "",
    colSpan: 0,
    dataset: {},
    disabled: false,
    innerHTML: "",
    textContent: "",
    value: "",
    append(...children) {
      this.children.push(...children);
    },
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    replaceChildren(...children) {
      this.children = children;
    },
    setAttribute() {},
  };
}

function responseJson(status, body) {
  return {
    ok: status >= 200 && status < 300,
    status,
    async json() {
      return body;
    },
  };
}

function headerValue(headers, name) {
  if (typeof headers?.get === "function") {
    return headers.get(name);
  }
  if (Array.isArray(headers)) {
    return headers.find(
      ([candidate]) => candidate.toLowerCase() === name.toLowerCase(),
    )?.[1];
  }
  return Object.entries(headers ?? {}).find(
    ([candidate]) => candidate.toLowerCase() === name.toLowerCase(),
  )?.[1];
}

function adaptClientScriptForVm(clientScript) {
  assert.doesNotMatch(
    clientScript,
    /(?:^|[;\n])\s*import(?=\s|[({*."'[\]])/m,
    "UI retry oracle does not support module imports",
  );
  assert.doesNotMatch(
    clientScript,
    /(?:^|[;\n])\s*export\s+(?!function\b)/m,
    "UI retry oracle only supports export function declarations",
  );
  return clientScript.replace(
    /(^|[;\n])(\s*)export\s+(?=function\b)/gm,
    "$1$2",
  );
}

async function settle(value, description) {
  let timeout;
  try {
    await Promise.race([
      Promise.resolve(value),
      new Promise((_, reject) => {
        timeout = setTimeout(
          () => reject(new Error(`Timed out while ${description}`)),
          2_000,
        );
      }),
    ]);
  } finally {
    clearTimeout(timeout);
  }
}

export async function assertUiRetryReusesRequest(
  clientScript,
  movementFormMarkup = "",
) {
  const formValues = new Map([
    ["item", "Rice"],
    ["kind", "donation"],
    ["quantity", "2"],
    ["lowStockThreshold", ""],
  ]);
  const listeners = new Map();
  const movementRequests = [];
  const elements = new Map();
  const submitButton = stubElement();
  const formSelectors = new Set(["#movement-form", "form"]);
  const formId = getAttribute(movementFormMarkup, "id");
  if (formId) {
    formSelectors.add(`#${formId}`);
  }
  const form = {
    ...stubElement(),
    lowStockThreshold: { value: "" },
    addEventListener(type, listener) {
      listeners.set(type, listener);
    },
    querySelector() {
      return submitButton;
    },
    reset() {},
  };

  class MinimalFormData {
    get(name) {
      return formValues.get(name) ?? null;
    }

    *[Symbol.iterator]() {
      yield* formValues;
    }
  }

  const document = {
    readyState: "complete",
    addEventListener(type, listener) {
      if (type === "DOMContentLoaded") {
        listener();
      }
    },
    createElement() {
      return stubElement();
    },
    getElementById(id) {
      return this.querySelector(`#${id}`);
    },
    querySelector(selector) {
      if (formSelectors.has(selector)) {
        return form;
      }
      if (!elements.has(selector)) {
        elements.set(selector, stubElement());
      }
      return elements.get(selector);
    },
  };
  let uuid = 0;
  let movementAttempt = 0;
  const sandbox = {
    console,
    crypto: {
      randomUUID() {
        uuid += 1;
        return `acceptance-retry-${uuid}`;
      },
    },
    document,
    FormData: MinimalFormData,
    setTimeout,
    clearTimeout,
    async fetch(input, options = {}) {
      const url = String(input);
      if (/\/api\/movements(?:[?#]|$)/.test(url)) {
        movementRequests.push(options);
        movementAttempt += 1;
        if (movementAttempt === 1) {
          throw new TypeError(
            "Network connection closed after the request may have been accepted",
          );
        }
        if (movementAttempt === 2) {
          return responseJson(422, { error: "Definite rejected movement" });
        }
        return responseJson(201, { saved: true });
      }
      if (/\/api\/inventory(?:[?#]|$)/.test(url)) {
        return responseJson(200, { items: [] });
      }
      return responseJson(404, { error: "not found" });
    },
  };
  sandbox.window = sandbox;
  sandbox.self = sandbox;

  const initialResult = vm.runInNewContext(
    adaptClientScriptForVm(clientScript),
    sandbox,
    {
      timeout: 1_000,
    },
  );
  if (initialResult && typeof initialResult.then === "function") {
    await settle(initialResult, "waiting for the UI to initialize");
  }

  const submit = listeners.get("submit") ?? form.onsubmit;
  assert.equal(
    typeof submit,
    "function",
    "UI exposes an executable movement submit handler",
  );
  const event = {
    currentTarget: form,
    target: form,
    preventDefault() {},
  };

  try {
    await settle(submit(event), "simulating an ambiguous movement failure");
  } catch {
    // Browser event handlers may surface the failed fetch instead of catching it.
  }
  const secondSubmissionStart = movementRequests.length;
  await settle(submit(event), "resubmitting the unchanged movement");

  assert.ok(
    secondSubmissionStart > 0,
    "UI sends a movement request before retrying",
  );
  assert.ok(
    movementRequests.length > secondSubmissionStart,
    "UI resubmits the movement after an ambiguous network failure",
  );
  const firstRequest = movementRequests[0];
  const retryRequest = movementRequests[secondSubmissionStart];
  const firstKey = headerValue(firstRequest.headers, "idempotency-key");
  const retryKey = headerValue(retryRequest.headers, "idempotency-key");
  assert.ok(firstKey, "UI sends an Idempotency-Key");
  assert.equal(
    retryKey,
    firstKey,
    "UI retry must reuse the same Idempotency-Key after an ambiguous network failure",
  );
  assert.equal(
    retryRequest.body,
    firstRequest.body,
    "UI retry must send an identical request body after an ambiguous network failure",
  );

  const afterRejectedResponseStart = movementRequests.length;
  await settle(
    submit(event),
    "resubmitting after a definite rejected HTTP response",
  );
  const afterRejectedResponse = movementRequests[afterRejectedResponseStart];
  assert.ok(
    afterRejectedResponse,
    "UI submits again after a definite rejected HTTP response",
  );
  assert.notEqual(
    headerValue(afterRejectedResponse.headers, "idempotency-key"),
    retryKey,
    "UI must use a new Idempotency-Key after a definite rejected HTTP response",
  );

  const afterSuccessfulResponseStart = movementRequests.length;
  await settle(
    submit(event),
    "resubmitting after a definite successful HTTP response",
  );
  const afterSuccessfulResponse = movementRequests[afterSuccessfulResponseStart];
  assert.ok(
    afterSuccessfulResponse,
    "UI submits again after a definite successful HTTP response",
  );
  assert.notEqual(
    headerValue(afterSuccessfulResponse.headers, "idempotency-key"),
    headerValue(afterRejectedResponse.headers, "idempotency-key"),
    "UI must use a new Idempotency-Key after a definite successful HTTP response",
  );
}

async function assertInteractiveUi(baseUrl, html, verifyAmbiguousRetry) {
  const forms = [...html.matchAll(/<form\b[^>]*>[\s\S]*?<\/form>/gi)].map(
    ([form]) => form,
  );
  assert.ok(forms.length > 0, "UI has a movement form");
  const movementForm =
    forms.find((form) => /item|quantity|movement/i.test(form)) ?? forms[0];
  assertAssociatedMovementControls(movementForm, html);
  assertSubmitAffordance(movementForm);

  const markup = html
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, "");
  assertInventoryPresentation(markup);

  const clientScript = await collectClientScript(baseUrl, html);
  assert.match(clientScript, /\bfetch\s*\(/i, "UI executes API requests");
  assert.match(clientScript, /\/api\/inventory\b/, "UI loads inventory");
  assert.match(clientScript, /\/api\/movements\b/, "UI records movements");
  assert.match(
    clientScript,
    /addEventListener\s*\(\s*["']submit["']|\.onsubmit\s*=/i,
    "UI wires movement submission",
  );
  assert.match(
    clientScript,
    /\.textContent\s*=|\.innerHTML\s*=|replaceChildren\s*\(|insertAdjacentHTML\s*\(|append(?:Child)?\s*\(/i,
    "UI renders API data",
  );
  assert.match(
    `${markup}\n${clientScript}`,
    /low[\s_-]*stock|lowStock/i,
    "UI presents low-stock state",
  );
  if (verifyAmbiguousRetry) {
    await assertUiRetryReusesRequest(clientScript, movementForm);
  }
}

export function assertInventoryPresentation(markup) {
  assert.match(
    markup,
    /\b(?:inventory|stock)\b/i,
    "UI names the inventory or stock",
  );
  const presentationElements = [
    ...markup.matchAll(
      /<(?:section|table|tbody|ul|ol|div|output)\b[^>]*>/gi,
    ),
  ].map(([element]) => element);
  assert.ok(
    presentationElements.some((element) =>
      /inventory|stock/i.test(
        `${getAttribute(element, "id") ?? ""} ${
          getAttribute(element, "class") ?? ""
        } ${getAttribute(element, "aria-label") ?? ""} ${
          getAttribute(element, "aria-labelledby") ?? ""
        }`,
      ),
    ),
    "UI has a named inventory or stock presentation region",
  );
}

export function assertPageHeading(markup) {
  assert.match(markup, /<h1[\s>]/i, "UI has a primary heading");
}

async function main(mode) {
  const runRoot = await mkdtemp(join(tmpdir(), "pantry-ledger-acceptance-"));
  const dataFile = join(runRoot, "pantry.json");
  const checks = [];
  let application;
  try {
    application = await startApplication(dataFile);
    assert.equal(application.child.exitCode, null, application.stderr());

    const page = await fetch(`${application.baseUrl}/`);
    const html = await page.text();
    assert.equal(page.status, 200);
    assert.match(page.headers.get("content-type") ?? "", /text\/html/i);
    assertPageHeading(html);
    await assertInteractiveUi(application.baseUrl, html, mode === "full");
    checks.push("accessible, interactive inventory UI");
    if (mode === "full") {
      checks.push(
        "ambiguous UI retry reuses its request identity and definite responses retire it",
      );
    }

    const donationBody = movement("Rice", "donation", 10);
    if (mode === "full") {
      const missingKey = await requestJson(
        application.baseUrl,
        "/api/movements",
        movementOptions(donationBody),
      );
      assert.ok(
        missingKey.response.status >= 400 && missingKey.response.status < 500,
        `missing Idempotency-Key was not rejected: ${missingKey.body}`,
      );
      const emptyInventory = await requestJson(
        application.baseUrl,
        "/api/inventory",
      );
      assert.equal(emptyInventory.response.status, 200, emptyInventory.body);
      assert.ok(
        Array.isArray(emptyInventory.json?.items),
        "inventory has an items array",
      );
      assert.equal(emptyInventory.json.items.length, 0);
      checks.push("missing Idempotency-Key is rejected without side effects");
    }

    const donation = await requestJson(
      application.baseUrl,
      "/api/movements",
      movementOptions(
        donationBody,
        mode === "full" ? "donation-1" : undefined,
      ),
    );
    assert.ok(
      donation.response.status >= 200 && donation.response.status < 300,
      donation.body,
    );

    let inventory = await requestJson(application.baseUrl, "/api/inventory");
    assert.equal(inventory.response.status, 200, inventory.body);
    assert.deepEqual(riceFrom(inventory.json), {
      name: "Rice",
      quantity: 10,
      lowStockThreshold: 5,
      lowStock: false,
    });
    checks.push("donation and inventory use the default threshold 5");

    if (mode === "full") {
      for (const threshold of [5, 6]) {
        const conflictingThreshold = await requestJson(
          application.baseUrl,
          "/api/movements",
          movementOptions(
            movement("Rice", "donation", 10, threshold),
            "donation-1",
          ),
        );
        assert.equal(
          conflictingThreshold.response.status,
          409,
          conflictingThreshold.body,
        );
      }
      checks.push(
        "optional threshold presence and value participate in canonical conflicts",
      );
    }

    const distributionBody = movement("Rice", "distribution", 7);
    const distribution = await requestJson(
      application.baseUrl,
      "/api/movements",
      movementOptions(
        distributionBody,
        mode === "full" ? "distribution-1" : undefined,
      ),
    );
    assert.ok(
      distribution.response.status >= 200 &&
        distribution.response.status < 300,
      distribution.body,
    );
    if (mode === "full") {
      const canonicalReplayBody = JSON.stringify({
        quantity: 7,
        item: "Rice",
        kind: "distribution",
      });
      const replay = await requestJson(
        application.baseUrl,
        "/api/movements",
        movementOptions(canonicalReplayBody, "distribution-1"),
      );
      assert.equal(replay.response.status, distribution.response.status);
      assert.equal(replay.body, distribution.body);
      checks.push("canonical same-key replay returns the original response");
    }

    inventory = await requestJson(application.baseUrl, "/api/inventory");
    assert.deepEqual(riceFrom(inventory.json), {
      name: "Rice",
      quantity: 3,
      lowStockThreshold: 5,
      lowStock: true,
    });

    if (mode === "full") {
      const conflicting = await requestJson(
        application.baseUrl,
        "/api/movements",
        movementOptions(
          movement("Rice", "distribution", 1),
          "distribution-1",
        ),
      );
      assert.equal(conflicting.response.status, 409, conflicting.body);
      checks.push("same key with a different payload conflicts");
    }

    const insufficient = await requestJson(
      application.baseUrl,
      "/api/movements",
      movementOptions(
        movement("Rice", "distribution", 4),
        mode === "full" ? "distribution-insufficient" : undefined,
      ),
    );
    assert.equal(insufficient.response.status, 409, insufficient.body);
    for (const [label, quantity] of [
      ["zero", 0],
      ["negative", -1],
      ["fractional", 1.5],
    ]) {
      const invalid = await requestJson(
        application.baseUrl,
        "/api/movements",
        movementOptions(
          movement("Rice", "donation", quantity),
          mode === "full" ? `invalid-${label}` : undefined,
        ),
      );
      assert.ok(
        invalid.response.status >= 400 && invalid.response.status < 500,
        `invalid ${label} quantity was not rejected: ${invalid.body}`,
      );
    }
    inventory = await requestJson(application.baseUrl, "/api/inventory");
    assert.equal(riceFrom(inventory.json).quantity, 3);
    checks.push(
      "zero, negative, fractional, and insufficient movements preserve stock",
    );

    await stopApplication(application);
    application = await startApplication(dataFile);
    assert.equal(application.child.exitCode, null, application.stderr());
    inventory = await requestJson(application.baseUrl, "/api/inventory");
    assert.equal(riceFrom(inventory.json).quantity, 3);
    if (mode === "full") {
      const restartReplay = await requestJson(
        application.baseUrl,
        "/api/movements",
        movementOptions(
          JSON.stringify({
            kind: "distribution",
            quantity: 7,
            item: "Rice",
          }),
          "distribution-1",
        ),
      );
      assert.equal(restartReplay.response.status, distribution.response.status);
      assert.equal(restartReplay.body, distribution.body);
      inventory = await requestJson(application.baseUrl, "/api/inventory");
      assert.equal(riceFrom(inventory.json).quantity, 3);
      checks.push("inventory and canonical replay persist across restart");
    } else {
      checks.push("inventory persists across restart");
    }

    await stopApplication(application);
    if (mode === "full") {
      const legacyDataFile = join(runRoot, "legacy-inventory.json");
      await writeFile(
        legacyDataFile,
        JSON.stringify({
          items: [
            {
              name: "Beans",
              quantity: 2,
              lowStockThreshold: 3,
            },
          ],
        }),
        "utf8",
      );
      application = await startApplication(legacyDataFile);
      const legacyInventory = await requestJson(
        application.baseUrl,
        "/api/inventory",
      );
      assert.equal(legacyInventory.response.status, 200, legacyInventory.body);
      assert.deepEqual(
        legacyInventory.json?.items,
        [
          {
            name: "Beans",
            quantity: 2,
            lowStockThreshold: 3,
            lowStock: true,
          },
        ],
      );
      await stopApplication(application);
      checks.push("inventory-only legacy data remains readable");
    }

    const corrupt = "{ this is not valid JSON\n";
    await writeFile(dataFile, corrupt, "utf8");
    application = await startApplication(dataFile);
    let corruptResponse;
    if (application.child.exitCode === null) {
      try {
        corruptResponse = await fetch(`${application.baseUrl}/api/inventory`);
      } catch {
        corruptResponse = null;
      }
    }
    assert.ok(
      application.child.exitCode !== null ||
        corruptResponse === null ||
        corruptResponse.status >= 500,
      "corrupt persistence must not serve inventory successfully",
    );
    assert.equal(await readFile(dataFile, "utf8"), corrupt);
    checks.push("corrupt data refuses service and is preserved");

    console.log(JSON.stringify({ passed: true, mode, checks }, null, 2));
  } catch (error) {
    console.error(
      JSON.stringify(
        {
          passed: false,
          mode,
          checks,
          error: error instanceof Error ? error.message : String(error),
          application_stdout: application?.stdout() ?? "",
          application_stderr: application?.stderr() ?? "",
        },
        null,
        2,
      ),
    );
    process.exitCode = 1;
  } finally {
    if (application) {
      await stopApplication(application);
    }
    await rm(runRoot, { recursive: true, force: true });
  }
}
