#!/usr/bin/env node

const [,, wsUrl, method, paramsJson = "{}"] = process.argv;

if (!wsUrl || !method) {
  console.error("usage: cdp_command.js <ws_url> <method> [params_json]");
  process.exit(2);
}

let params = {};
try {
  params = JSON.parse(paramsJson);
} catch (error) {
  console.error(`invalid params json: ${error}`);
  process.exit(2);
}

const ws = new WebSocket(wsUrl);

ws.addEventListener("open", () => {
  ws.send(JSON.stringify({ id: 1, method, params }));
});

ws.addEventListener("message", (event) => {
  const message = JSON.parse(event.data.toString());
  if (message.id !== 1) {
    return;
  }
  if (message.error) {
    console.error(JSON.stringify(message.error));
    process.exit(1);
  }
  console.log(JSON.stringify(message.result ?? {}));
  ws.close();
  process.exit(0);
});

ws.addEventListener("error", (event) => {
  console.error(String(event.message || event.error || event));
  process.exit(1);
});
