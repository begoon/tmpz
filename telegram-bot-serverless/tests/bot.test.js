import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { SourceTextModule, SyntheticModule, createContext } from 'node:vm';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';

// Execute the actual platform modules with a local SQLite database and recorded
// Bot API calls. Only the SDK boundary is replaced; handlers and SQL are real.
async function harness(t) {
  const sqlite = new DatabaseSync(':memory:');
  t.after(() => sqlite.close());
  const calls = [];
  const context = createContext({ console });
  const db = Object.fromEntries(['run', 'all', 'get'].map((method) => [method,
    async (sql, params = {}) => {
      const result = sqlite.prepare(sql)[method](params);
      return method === 'run' ? { rowsAffected: result.changes, rows: [] } : result;
    },
  ]));
  const api = {
    async getMe() { return { username: 'ExampleBot' }; },
    async sendMessage(params) { calls.push({ method: 'sendMessage', ...params }); },
    async answerCallbackQuery(params) { calls.push({ method: 'answerCallbackQuery', ...params }); },
  };
  const column = (type) => (name) => ({
    name, definition: `${name} ${type}`,
    primaryKey() { this.definition += ' PRIMARY KEY'; return this; },
    notNull() { this.definition += ' NOT NULL'; return this; },
    default(value) { this.definition += ` DEFAULT ${Number(value)}`; return this; },
  });
  const schemaSDK = {
    integer: column('INTEGER'), text: column('TEXT'),
    index: (name) => ({ on: (...cols) => ({ name, cols }) }),
    table(name, columns, extras) {
      sqlite.exec(`CREATE TABLE ${name} (${Object.values(columns).map(c => c.definition).join(', ')})`);
      for (const idx of Object.values(extras?.(columns) ?? {})) {
        sqlite.exec(`CREATE INDEX ${idx.name} ON ${name} (${idx.cols.map(c => c.name).join(', ')})`);
      }
      return columns;
    },
  };
  const synthetic = (exports) => new SyntheticModule(Object.keys(exports), function () {
    for (const [name, value] of Object.entries(exports)) this.setExport(name, value);
  }, { context });
  const cache = new Map([['sdk', synthetic({ api, db })], ['sdk/db', synthetic(schemaSDK)]]);
  function moduleFor(id) {
    if (!cache.has(id)) cache.set(id, new SourceTextModule(readFileSync(id, 'utf8'), { context, identifier: id }));
    return cache.get(id);
  }
  async function load(file) {
    const mod = moduleFor(resolve(file));
    await mod.link((id, parent) => moduleFor(id.startsWith('sdk') ? id : resolve(dirname(parent.identifier), id)));
    await mod.evaluate();
    return mod.namespace;
  }
  await load('tgcloud/schema.js');
  const message = (await load('tgcloud/handlers/message.js')).default;
  const callback = (await load('tgcloud/handlers/callback_query.js')).default;
  return { sqlite, calls, message, callback };
}

const msg = (text, extra = {}) => ({
  message_id: 1, chat: { id: 100 }, from: { id: 7 }, date: 1000, text, ...extra,
});
const cb = (data, extra = {}) => ({
  id: 'callback-1', from: { id: 7 }, message: { chat: { id: 100 }, date: 1000 }, data, ...extra,
});

test('commands, addressed commands, invalid input and non-text updates', async (t) => {
  const h = await harness(t);
  await h.message(msg('/start'));
  assert.match(h.calls.at(-1).text, /Serverless notes bot/);
  await h.message(msg('/help@ExampleBot'));
  assert.equal(h.calls.length, 2);
  await h.message(msg('/help@OtherBot'));
  await h.message(msg(undefined));
  assert.equal(h.calls.length, 2);
  await h.message(msg('/add'));
  assert.match(h.calls.at(-1).text, /1–200/);
  await h.message(msg('/add ' + 'x'.repeat(201)));
  assert.match(h.calls.at(-1).text, /1–200/);
  await h.message(msg('/unknown'));
  assert.match(h.calls.at(-1).text, /Unknown command/);
});

test('create, list, complete, reopen, stats and delete persist in SQLite', async (t) => {
  const h = await harness(t);
  await h.message(msg('/add Buy milk'));
  await h.message(msg('/notes'));
  assert.match(h.calls.at(-1).text, /○ Buy milk/);
  await h.callback(cb('note:done:100:1'));
  assert.match(h.calls.at(-1).text, /✓ Buy milk/);
  assert.equal(h.calls.at(-2).method, 'answerCallbackQuery');
  await h.callback(cb('stats'));
  assert.match(h.calls.at(-1).text, /Completed: 1\nOpen: 0/);
  await h.callback(cb('note:open:100:1'));
  assert.match(h.calls.at(-1).text, /○ Buy milk/);
  await h.callback(cb('note:delete:100:1'));
  assert.match(h.calls.at(-1).text, /No notes yet/);
  await h.message(msg('/stats'));
  assert.match(h.calls.at(-1).text, /Completed: 0\nOpen: 0/);
});

test('message retries and repeated complete/delete callbacks are idempotent', async (t) => {
  const h = await harness(t);
  await h.message(msg('/add first'));
  await h.message(msg('/add first'));
  assert.equal(h.sqlite.prepare('SELECT count(*) AS n FROM notes').get().n, 1);
  await h.callback(cb('note:done:100:1'));
  await h.callback(cb('note:done:100:1'));
  assert.equal(h.sqlite.prepare('SELECT done FROM notes').get().done, 1);
  await h.callback(cb('note:delete:100:1'));
  await h.callback(cb('note:delete:100:1'));
  assert.equal(h.sqlite.prepare('SELECT count(*) AS n FROM notes').get().n, 0);
});

test('other users and chats cannot list or mutate someone else’s notes', async (t) => {
  const h = await harness(t);
  await h.message(msg('/add secret'));
  await h.callback(cb('note:delete:100:1', { from: { id: 8 } }));
  assert.match(h.calls.at(-1).text, /No notes yet/);
  await h.callback(cb('note:done:100:1', { message: { chat: { id: 200 }, date: 1000 } }));
  const row = h.sqlite.prepare('SELECT * FROM notes').get();
  assert.equal(row.body, 'secret');
  assert.equal(row.done, 0);
});

test('SQL-like content is stored literally and list output stays bounded', async (t) => {
  const h = await harness(t);
  const body = "'); DROP TABLE notes; -- <b>plain text</b>";
  await h.message(msg('/add ' + body));
  assert.equal(h.sqlite.prepare('SELECT body FROM notes').get().body, body);
  for (let i = 2; i <= 12; i++) await h.message(msg('/add ' + 'x'.repeat(200), { message_id: i }));
  await h.message(msg('/notes'));
  const view = h.calls.at(-1);
  assert.equal(view.reply_markup.inline_keyboard.length, 11);
  assert.ok(view.text.length < 4096);
  for (const row of view.reply_markup.inline_keyboard) {
    for (const button of row) assert.ok(Buffer.byteLength(button.callback_data) <= 64);
  }
});

test('unknown, inline and inaccessible callbacks are acknowledged safely', async (t) => {
  const h = await harness(t);
  for (const query of [cb('invalid'), cb('notes', { message: undefined }), cb('notes', {
    message: { chat: { id: 100 }, date: 0 },
  })]) await h.callback(query);
  assert.equal(h.calls.length, 3);
  assert.ok(h.calls.every(call => call.method === 'answerCallbackQuery'));
});
