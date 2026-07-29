import assert from "node:assert/strict";
import test from "node:test";

import {
  assertInventoryPresentation,
  assertPageHeading,
  assertUiRetryReusesRequest,
} from "../scripts/pantry_ledger_acceptance.mjs";

test("UI accepts a heading and content sections without a main element", () => {
  const markup = `
    <body>
      <h1>Pantry Ledger</h1>
      <section aria-labelledby="stock-title">
        <h2 id="stock-title">Current stock</h2>
        <div id="stock"></div>
      </section>
    </body>
  `;

  assert.doesNotThrow(() => {
    assertPageHeading(markup);
    assertInventoryPresentation(markup);
  });
});

test("UI accepts stock terminology for a named inventory presentation", () => {
  assert.doesNotThrow(() =>
    assertInventoryPresentation(`
      <section aria-labelledby="stock-title">
        <h2 id="stock-title">Current stock</h2>
        <table><tbody id="stock"></tbody></table>
      </section>
    `),
  );
});

test("UI retry reuses the request identity after an ambiguous failure", async () => {
  const script = `
    const form = document.querySelector('#movement-form');
    let pending;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const body = JSON.stringify(Object.fromEntries(new FormData(form)));
      const key = pending?.body === body
        ? pending.key
        : crypto.randomUUID();
      pending = { body, key };
      try {
        const response = await fetch('/api/movements', {
          method: 'POST',
          headers: { 'Idempotency-Key': key },
          body,
        });
        await response.json();
        pending = undefined;
      } catch {}
    });
  `;

  await assert.doesNotReject(assertUiRetryReusesRequest(script));
});

test("UI retry recognizes the rendered form's camelCase id", async () => {
  const script = `
    const form = document.querySelector('#movementForm');
    let pending;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const body = JSON.stringify(Object.fromEntries(new FormData(form)));
      const key = pending?.body === body
        ? pending.key
        : crypto.randomUUID();
      pending = { body, key };
      try {
        const response = await fetch('/api/movements', {
          method: 'POST',
          headers: { 'Idempotency-Key': key },
          body,
        });
        await response.json();
        pending = undefined;
      } catch {}
    });
  `;

  await assert.doesNotReject(
    assertUiRetryReusesRequest(script, '<form id="movementForm"></form>'),
  );
});

test("UI retry executes a simple exported function from a module script", async () => {
  const script = `
    export function createMovementSubmitter() {
      let pending;
      return async (form) => {
        const body = JSON.stringify(Object.fromEntries(new FormData(form)));
        const key = pending?.body === body
          ? pending.key
          : crypto.randomUUID();
        pending = { body, key };
        try {
          const response = await fetch('/api/movements', {
            method: 'POST',
            headers: { 'Idempotency-Key': key },
            body,
          });
          await response.json();
          pending = undefined;
        } catch {}
      };
    }

    const form = document.querySelector('#movement-form');
    const submitMovement = createMovementSubmitter();
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      await submitMovement(form);
    });
  `;

  await assert.doesNotReject(assertUiRetryReusesRequest(script));
});

test("UI retry explicitly rejects module imports", async () => {
  const script = `
    import { submitMovement } from './movement.js';
    const form = document.querySelector('#movement-form');
    form.addEventListener('submit', (event) => submitMovement(event));
  `;

  await assert.rejects(
    assertUiRetryReusesRequest(script),
    /does not support module imports/,
  );
});

test("UI retry supports standard element dataset state updates", async () => {
  const script = `
    const form = document.querySelector('#movement-form');
    const message = document.querySelector('#message');
    message.dataset.state = 'idle';
    let pending;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const body = JSON.stringify(Object.fromEntries(new FormData(form)));
      const key = pending?.body === body
        ? pending.key
        : crypto.randomUUID();
      pending = { body, key };
      try {
        const response = await fetch('/api/movements', {
          method: 'POST',
          headers: { 'Idempotency-Key': key },
          body,
        });
        await response.json();
        pending = undefined;
        message.dataset.state = response.ok ? 'success' : 'error';
      } catch {
        message.dataset.state = 'error';
      }
    });
  `;

  await assert.doesNotReject(assertUiRetryReusesRequest(script));
});

test("UI retry supports standard element attribute updates", async () => {
  const script = `
    const form = document.querySelector('#movement-form');
    const status = document.querySelector('#status');
    let pending;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const body = JSON.stringify(Object.fromEntries(new FormData(form)));
      const key = pending?.body === body
        ? pending.key
        : crypto.randomUUID();
      pending = { body, key };
      try {
        const response = await fetch('/api/movements', {
          method: 'POST',
          headers: { 'Idempotency-Key': key },
          body,
        });
        await response.json();
        pending = undefined;
        status.setAttribute('role', response.ok ? 'status' : 'alert');
      } catch {
        status.setAttribute('role', 'alert');
      }
    });
  `;

  await assert.doesNotReject(assertUiRetryReusesRequest(script));
});

test("UI retry rejects retaining the request identity after a definite response", async () => {
  const script = `
    const form = document.querySelector('#movement-form');
    let pending;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const body = JSON.stringify(Object.fromEntries(new FormData(form)));
      const key = pending?.body === body
        ? pending.key
        : crypto.randomUUID();
      pending = { body, key };
      try {
        const response = await fetch('/api/movements', {
          method: 'POST',
          headers: { 'Idempotency-Key': key },
          body,
        });
        await response.json();
        if (response.ok) pending = undefined;
      } catch {}
    });
  `;

  await assert.rejects(
    assertUiRetryReusesRequest(script),
    /use a new Idempotency-Key after a definite rejected HTTP response/,
  );
});

test("UI retry rejects a newly generated request identity", async () => {
  const script = `
    const form = document.querySelector('#movement-form');
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const body = JSON.stringify(Object.fromEntries(new FormData(form)));
      try {
        await fetch('/api/movements', {
          method: 'POST',
          headers: { 'Idempotency-Key': crypto.randomUUID() },
          body,
        });
      } catch {}
    });
  `;

  await assert.rejects(
    assertUiRetryReusesRequest(script),
    /reuse the same Idempotency-Key after an ambiguous network failure/,
  );
});

test("UI retry rejects a changed request body", async () => {
  const script = `
    const form = document.querySelector('#movement-form');
    const key = crypto.randomUUID();
    let attempt = 0;
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      attempt += 1;
      const body = JSON.stringify({
        ...Object.fromEntries(new FormData(form)),
        attempt,
      });
      try {
        await fetch('/api/movements', {
          method: 'POST',
          headers: { 'Idempotency-Key': key },
          body,
        });
      } catch {}
    });
  `;

  await assert.rejects(
    assertUiRetryReusesRequest(script),
    /send an identical request body after an ambiguous network failure/,
  );
});
