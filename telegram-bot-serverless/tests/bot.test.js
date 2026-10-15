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
    async getMe() { return { username: 'ExampleBot', supports_inline_queries: true }; },
    async getChatMenuButton() { return { web_app: { url: 'https://app123.tgcloud.ai/' } }; },
    async sendMessage(params) { calls.push({ method: 'sendMessage', ...params }); },
    async answerCallbackQuery(params) { calls.push({ method: 'answerCallbackQuery', ...params }); },
    async answerInlineQuery(params) { calls.push({ method: 'answerInlineQuery', ...params }); },
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
  class EndpointError extends Error {}
  const cache = new Map([['sdk', synthetic({ api, db, EndpointError })], ['sdk/db', synthetic(schemaSDK)]]);
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
  const endpoint = (await load('tgcloud/endpoints/notes.js')).default;
  const inline = (await load('tgcloud/handlers/inline_query.js')).default;
  return { sqlite, calls, message, callback, endpoint, inline, api };
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

test('Mini App CRUD shares private-chat notes and deduplicates retries', async (t) => {
  const h = await harness(t);
  const ctx = { initData: { user: { id: 7 } } };
  await h.message(msg('/add from chat', { chat: { id: 7 } }));
  const add = { action: 'add', body: 'from app', requestId: 'a'.repeat(32) };
  let result = await h.endpoint(add, ctx);
  result = await h.endpoint(add, ctx);
  assert.equal(result.stats.total, 2);
  const id = result.notes.find(n => n.body === 'from app').id;
  result = await h.endpoint({ action: 'done', id }, ctx);
  assert.equal(result.stats.completed, 1);
  await h.callback(cb(`note:open:${id}`, { message: { chat: { id: 7 }, date: 1000 } }));
  result = await h.endpoint({}, ctx);
  assert.equal(result.stats.completed, 0);
  result = await h.endpoint({ action: 'delete', id }, ctx);
  assert.equal(result.stats.total, 1);
});

test('Mini App trusts only verified identity, rejects bad input, and isolates group data', async (t) => {
  const h = await harness(t);
  const ctx = { initData: { user: { id: 7 } } };
  await h.message(msg('/add group note'));
  await h.message(msg('/add other user', { chat: { id: 8 }, from: { id: 8 } }));
  const result = await h.endpoint({ action: 'list', userId: 8, chatId: 100 }, ctx);
  assert.equal(result.notes.length, 0);
  await h.endpoint({ action: 'delete', id: '8:1', userId: 8 }, ctx);
  await h.endpoint({ action: 'done', id: '100:1', chatId: 100 }, ctx);
  assert.equal(h.sqlite.prepare('SELECT COUNT(*) AS n FROM notes WHERE done = 0').get().n, 2);
  await assert.rejects(h.endpoint({}, {}), /Open this app/);
  for (const input of [
    { action: 'add', body: 'a', requestId: 'invalid' },
    { action: 'add', body: ' '.repeat(10), requestId: 'a'.repeat(32) },
    { action: 'add', body: 'a'.repeat(201), requestId: 'a'.repeat(32) },
    { action: 'delete' }, { action: 'unsupported' },
  ]) await assert.rejects(h.endpoint(input, ctx));
});

test('/app opens the configured Mini App only in private chats', async (t) => {
  const h = await harness(t);
  await h.message(msg('/app', { chat: { id: 7, type: 'private' } }));
  assert.equal(h.calls.at(-1).reply_markup.inline_keyboard[0][0].web_app.url, 'https://app123.tgcloud.ai/');
  await h.message(msg('/app', { chat: { id: -100, type: 'group' } }));
  assert.match(h.calls.at(-1).text, /private chat/);
  assert.equal(h.calls.at(-1).reply_markup, undefined);
});

test('inline search shares only the caller’s private notes as literal text', async (t) => {
  const h = await harness(t);
  await h.message(msg('/add group coffee'));
  await h.message(msg('/add other coffee', { chat: { id: 8 }, from: { id: 8 } }));
  await h.message(msg('/add <b>Coffee</b> & 50%_off', { chat: { id: 7 } }));
  await h.endpoint({ action: 'add', body: 'Mini App coffee', requestId: 'a'.repeat(32) }, { initData: { user: { id: 7 } } });
  const query = { id: 'inline-1', from: { id: 7 }, query: '  COFFEE ', offset: '' };
  await h.inline(query);
  let answer = h.calls.at(-1);
  assert.equal(answer.method, 'answerInlineQuery');
  assert.equal(answer.inline_query_id, query.id);
  assert.equal(answer.is_personal, true);
  assert.equal(answer.cache_time, 0);
  assert.equal(answer.results.length, 2);
  assert.equal(answer.next_offset, '');
  assert.ok(answer.results.every(r => !r.reply_markup && !r.input_message_content.parse_mode));
  const literal = answer.results.find(r => r.id === '7:1');
  assert.equal(literal.input_message_content.message_text, '<b>Coffee</b> & 50%_off');
  assert.equal(literal.input_message_content.link_preview_options.is_disabled, true);
  for (const term of ['%', '_', "' OR 1=1 --", 'not found']) {
    await h.inline({ ...query, query: term });
    assert.equal(h.calls.at(-1).results.length, ['%', '_'].includes(term) ? 1 : 0);
  }
  await h.inline({ ...query, from: { id: 9 } });
  assert.equal(h.calls.at(-1).results.length, 0);
});

test('inline empty search paginates, and invalid offsets/identity return no results', async (t) => {
  const h = await harness(t);
  for (let i = 1; i <= 23; i++) {
    await h.message(msg(`/add Note ${i}`, { chat: { id: 7 }, message_id: i, date: i }));
  }
  const query = { id: 'inline-2', from: { id: 7 }, query: '', offset: '' };
  await h.inline(query);
  const first = h.calls.at(-1);
  assert.equal(first.results.length, 20);
  assert.equal(first.next_offset, '20');
  assert.equal(first.results[0].input_message_content.message_text, 'Note 23');
  await h.inline({ ...query, offset: first.next_offset });
  const second = h.calls.at(-1);
  assert.equal(second.results.length, 3);
  assert.equal(second.next_offset, '');
  assert.equal(new Set([...first.results, ...second.results].map(r => r.id)).size, 23);
  for (const offset of ['-1', '1.5', 'NaN', '1000001', '0 OR 1=1']) {
    await h.inline({ ...query, offset });
    assert.equal(h.calls.at(-1).results.length, 0);
  }
  await h.inline({ ...query, from: undefined });
  assert.equal(h.calls.at(-1).results.length, 0);
  assert.equal(h.calls.at(-1).button.start_parameter, 'inline_notes');
});

test('/share offers a chat picker only when inline mode is enabled', async (t) => {
  const h = await harness(t);
  await h.message(msg('/share'));
  assert.equal(h.calls.at(-1).reply_markup.inline_keyboard[0][0].switch_inline_query, '');
  h.api.getMe = async () => ({ username: 'ExampleBot' });
  await h.message(msg('/share'));
  assert.match(h.calls.at(-1).text, /not enabled/);
  assert.equal(h.calls.at(-1).reply_markup, undefined);
});
