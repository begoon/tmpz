import { describe, expect, test } from "bun:test";
import { generateKeyPairSync, sign } from "node:crypto";
import { createHandler } from "../src/interactions";

const { publicKey, privateKey } = generateKeyPairSync("ed25519");
const handler = createHandler({
  publicKey: publicKey.export({ format: "der", type: "spki" }).subarray(-32).toString("hex"),
  applicationId: "reactor", guildId: "operations",
});
function request(payload: unknown, timestamp = String(Math.floor(Date.now() / 1000))) {
  const body = JSON.stringify(payload);
  return new Request("http://localhost/interactions", { method: "POST", body, headers: {
    "x-signature-timestamp": timestamp,
    "x-signature-ed25519": sign(null, Buffer.from(timestamp + body), privateKey).toString("hex"),
  } });
}
const info = { type: 2, application_id: "reactor", guild_id: "operations", data: { name: "info" } };

describe("Discord HTTP interactions", () => {
  test("answers a signed endpoint verification", async () => {
    expect(await (await handler(request({ type: 1 }))).json()).toEqual({ type: 1 });
  });
  test("returns Bun version and current UTC time", async () => {
    const before = Date.now();
    const response = await handler(request(info));
    expect(response.status).toBe(200);
    const result = await response.json();
    expect(result.type).toBe(4);
    expect(result.data.content).toStartWith(`Bun version: ${Bun.version}\nDate/time (UTC): `);
    const time = Date.parse(result.data.content.split("Date/time (UTC): ")[1]);
    expect(time).toBeGreaterThanOrEqual(before);
    expect(time).toBeLessThanOrEqual(Date.now());
  });
  test("rejects a tampered body", async () => {
    const signed = request(info);
    const tampered = new Request(signed.url, { method: "POST", headers: signed.headers, body: '{"type":1}' });
    expect((await handler(tampered)).status).toBe(401);
  });
  test("rejects unsigned and expired requests", async () => {
    expect((await handler(new Request("http://localhost/interactions", { method: "POST", body: "{}" }))).status).toBe(401);
    expect((await handler(request(info, "1"))).status).toBe(401);
  });
  test("restricts commands to configured app and guild", async () => {
    expect((await handler(request({ ...info, guild_id: "other" }))).status).toBe(403);
    expect((await handler(request({ ...info, application_id: "other" }))).status).toBe(403);
  });
  test("fails closed without configuration", async () => {
    expect((await createHandler({})(request(info))).status).toBe(503);
  });
});
