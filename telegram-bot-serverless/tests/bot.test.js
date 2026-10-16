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
    async getBusinessConnection({ business_connection_id }) {
      return { id: business_connection_id, user: { id: 42 }, is_enabled: true, rights: { can_reply: true } };
    },
    async getChatMenuButton() { return { web_app: { url: 'https://app123.tgcloud.ai/' } }; },
    async sendMessage(params) { calls.push({ method: 'sendMessage', ...params }); },
    async sendDocument(params) { calls.push({ method: 'sendDocument', ...params }); },
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
  const businessConnection = (await load('tgcloud/handlers/business_connection.js')).default;
  const businessMessage = (await load('tgcloud/handlers/business_message.js')).default;
  return { sqlite, calls, message, callback, endpoint, inline, businessConnection, businessMessage, api };
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

const upload = (extra = {}) => msg(undefined, {
  document: { file_id: 'telegram-file-id', file_unique_id: 'stable-id',
    file_name: "report's <final>.pdf", mime_type: 'application/pdf', file_size: 1234 },
  ...extra,
});

test('document upload stores metadata once and can be listed, downloaded and removed', async (t) => {
  const h = await harness(t);
  await h.message(upload());
  await h.message(upload());
  const rows = h.sqlite.prepare('SELECT * FROM files').all();
  assert.equal(rows.length, 1);
  assert.equal(rows[0].file_id, 'telegram-file-id');
  assert.equal(rows[0].name, "report's <final>.pdf");
  assert.equal(rows[0].size, 1234);
  assert.equal(rows[0].mime_type, 'application/pdf');
  await h.message(msg('/files'));
  assert.match(h.calls.at(-1).text, /report's <final>.pdf \(1234 bytes\)/);
  assert.equal(h.calls.at(-1).reply_markup.inline_keyboard[0][0].callback_data, 'file:get:100:1');
  await h.callback(cb('file:get:100:1'));
  assert.equal(h.calls.at(-2).method, 'answerCallbackQuery');
  assert.equal(h.calls.at(-1).method, 'sendDocument');
  assert.equal(h.calls.at(-1).document, 'telegram-file-id');
  await h.callback(cb('file:delete:100:1'));
  await h.callback(cb('file:delete:100:1'));
  assert.equal(h.sqlite.prepare('SELECT COUNT(*) AS n FROM files').get().n, 0);
  await h.callback(cb('file:get:100:1'));
  assert.match(h.calls.at(-1).text, /File not found/);
});

test('file lists and callbacks cannot access another user or chat’s upload', async (t) => {
  const h = await harness(t);
  await h.message(upload());
  for (const extra of [{ from: { id: 8 } }, { message: { chat: { id: 200 }, date: 1000 } }]) {
    await h.callback(cb('files', extra));
    assert.match(h.calls.at(-1).text, /No files yet/);
    await h.callback(cb('file:get:100:1', extra));
    assert.match(h.calls.at(-1).text, /File not found/);
    await h.callback(cb('file:delete:100:1', extra));
  }
  assert.equal(h.calls.filter(c => c.method === 'sendDocument').length, 0);
  assert.equal(h.sqlite.prepare('SELECT COUNT(*) AS n FROM files').get().n, 1);
});

test('documents with missing optional fields work; long file lists remain bounded', async (t) => {
  const h = await harness(t);
  await h.message(upload({ document: { file_id: 'id', file_unique_id: 'unique' } }));
  await h.message(msg('/files'));
  assert.match(h.calls.at(-1).text, /document \(unknown size\)/);
  for (let i = 2; i <= 12; i++) {
    await h.message(upload({ message_id: i, document: {
      file_id: `id-${i}`, file_unique_id: `unique-${i}`, file_name: 'x'.repeat(1000),
    } }));
  }
  await h.message(msg('/files'));
  const view = h.calls.at(-1);
  assert.equal(view.reply_markup.inline_keyboard.length, 11);
  assert.ok(view.text.length < 4096);
  assert.ok(h.sqlite.prepare('SELECT name FROM files').all().every(r => r.name.length <= 255));
});

const businessMessage = (extra = {}) => ({
  business_connection_id: 'connection-1', message_id: 12,
  date: Math.floor(Date.now() / 1000), chat: { id: 7, type: 'private' },
  from: { id: 7, first_name: 'Evgeny', is_bot: false }, text: 'Hello', ...extra,
});

test('secretary replies with exact notice for matching first/last names and media', async (t) => {
  const h = await harness(t);
  for (const [index, from] of [
    { id: 7, first_name: 'Evgeny' },
    { id: 7, first_name: 'Alex', last_name: 'EVGENY' },
    { id: 7, first_name: 'Dr. Evgeny' },
  ].entries()) {
    await h.businessMessage(businessMessage({ from, message_id: index + 1, text: undefined, document: {} }));
    const sent = h.calls.at(-1);
    assert.equal(sent.business_connection_id, 'connection-1');
    assert.equal(sent.chat_id, 7);
    assert.equal(sent.text, 'The message may be recorded for the AI training purposes :-)');
    assert.equal(sent.reply_parameters.message_id, index + 1);
  }
  assert.equal(h.calls.length, 3);
  assert.equal(h.sqlite.prepare('SELECT owner_id FROM business_connections').get().owner_id, 42);
});

test('secretary ignores nonmatching names, outgoing messages, bots, groups and expired messages', async (t) => {
  const h = await harness(t);
  for (const extra of [
    { from: { id: 7, first_name: 'Alex', username: 'Evgeny' } },
    { from: { id: 7, first_name: 'Евгений' } },
    { from: undefined },
    { from: { id: 42, first_name: 'Evgeny' } },
    { from: { id: 7, first_name: 'Evgeny', is_bot: true } },
    { sender_business_bot: { id: 100 } },
    { chat: { id: -100, type: 'group' } },
    { chat: { id: 88, type: 'private' } },
    { business_connection_id: undefined },
    { date: Math.floor(Date.now() / 1000) - 86401 },
    { message_id: 0 },
  ]) await h.businessMessage(businessMessage(extra));
  assert.equal(h.calls.length, 0);
  assert.equal(h.sqlite.prepare('SELECT COUNT(*) AS n FROM secretary_replies').get().n, 0);
});

test('secretary handles connection changes and requires current reply permission', async (t) => {
  const h = await harness(t);
  const connection = { id: 'connection-1', user: { id: 42 }, is_enabled: true, rights: { can_reply: true } };
  await h.businessConnection(connection);
  await h.businessConnection({ ...connection, is_enabled: false, rights: {} });
  const stored = h.sqlite.prepare('SELECT * FROM business_connections').get();
  assert.equal(stored.enabled, 0);
  assert.equal(stored.can_reply, 0);
  for (const changed of [
    { ...connection, is_enabled: false },
    { ...connection, rights: {} },
    { ...connection, rights: undefined },
  ]) {
    h.api.getBusinessConnection = async () => changed;
    await h.businessMessage(businessMessage());
  }
  assert.equal(h.calls.length, 0);
  h.api.getBusinessConnection = async () => { throw new Error('Permission lookup failed'); };
  await assert.rejects(h.businessMessage(businessMessage()), /Permission lookup failed/);
  assert.equal(h.calls.length, 0);
});

test('secretary deduplicates concurrent delivery and does not retry ambiguous sends', async (t) => {
  const h = await harness(t);
  await Promise.all([h.businessMessage(businessMessage()), h.businessMessage(businessMessage())]);
  assert.equal(h.calls.length, 1);
  await h.businessMessage(businessMessage({ message_id: 13 }));
  assert.equal(h.calls.length, 2);
  let attempts = 0;
  h.api.sendMessage = async () => { attempts++; throw new Error('Response lost'); };
  await assert.rejects(h.businessMessage(businessMessage({ message_id: 14 })), /Response lost/);
  await h.businessMessage(businessMessage({ message_id: 14 }));
  assert.equal(attempts, 1);
});
