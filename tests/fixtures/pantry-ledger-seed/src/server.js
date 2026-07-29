import { createServer } from "node:http";
import { fileURLToPath } from "node:url";

export function createPantryServer() {
  return createServer((request, response) => {
    if (request.method === "GET" && request.url === "/health") {
      response.writeHead(200, { "content-type": "application/json" });
      response.end(JSON.stringify({ status: "ok" }));
      return;
    }

    response.writeHead(404, { "content-type": "application/json" });
    response.end(JSON.stringify({ error: "not found" }));
  });
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT ?? 3000);
  createPantryServer().listen(port, "127.0.0.1", () => {
    console.log(`Pantry Ledger listening on http://127.0.0.1:${port}`);
  });
}
