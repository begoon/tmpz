import assert from "node:assert/strict";

const base = process.argv[2] ?? "http://localhost:3000";
const health = await fetch(new URL("/health", base));
assert.equal(health.status, 200);
assert.match(health.headers.get("content-type") ?? "", /text\/plain/);
assert.equal(await health.text(), "ok");
const page = await fetch(base);
assert.equal(page.status, 200);
assert.match(page.headers.get("content-type") ?? "", /text\/html/);
const html = await page.text();
assert.match(html, /<textarea/);
assert.ok(html.includes('placeholder="enter message..."'));
assert.equal((await fetch(new URL("/missing", base))).status, 404);
assert.equal((await fetch(new URL("/ws", base))).status, 426);

const url = new URL("/ws", base);
url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
await new Promise<void>((resolve, reject) => {
  const socket = new WebSocket(url);
  const messages = ["ping", "hello", "Ping", "A😀你", "", " ping "];
  const expected = ["pong", "olleh", "gniP", "你😀A", "", " gnip "];
  let received = 0;
  const timer = setTimeout(() => {
    socket.close();
    reject(new Error("WebSocket verification timed out"));
  }, 15000);
  socket.onopen = () => messages.forEach(message => socket.send(message));
  socket.onerror = () => {
    clearTimeout(timer);
    reject(new Error("WebSocket connection failed"));
  };
  socket.onmessage = event => {
    try {
      assert.equal(event.data, expected[received++]);
      if (received === messages.length) {
        clearTimeout(timer);
        socket.close();
        resolve();
      }
    } catch (error) {
      clearTimeout(timer);
      socket.close();
      reject(error);
    }
  };
});
console.log(`Verified HTTP routes and WebSocket replies: ${base}`);
