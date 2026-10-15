import { db, EndpointError } from 'sdk';
import { listNotes, getStats, changeNote } from '../lib/notes.js';

export default async function (input, ctx) {
  // Never accept user IDs or chat IDs from the browser. The app shares the
  // caller's private-chat notes; group notes remain scoped to their groups.
  const userId = ctx?.initData?.user?.id;
  if (!Number.isSafeInteger(userId) || userId <= 0) {
    throw new EndpointError('Open this app from Telegram.', { code: 'UNAUTHORIZED' });
  }
  const action = input?.action ?? 'list';
  if (action === 'add') {
    const body = typeof input.body === 'string' ? input.body.trim() : '';
    if (!body || body.length > 200 || !/^[a-f0-9]{32}$/.test(input.requestId ?? '')) {
      throw new EndpointError('Enter a note of 1–200 characters.', { code: 'INVALID_INPUT' });
    }
    await db.run(`INSERT INTO notes (id, chat_id, user_id, body, done, created_at)
      VALUES (:id, :user, :user, :body, 0, :created) ON CONFLICT(id) DO NOTHING`, {
      ':id': `w:${userId}:${input.requestId}`, ':user': userId,
      ':body': body, ':created': Math.floor(Date.now() / 1000),
    });
  } else if (['done', 'open', 'delete'].includes(action)) {
    if (typeof input.id !== 'string' || input.id.length > 64) {
      throw new EndpointError('Invalid note.', { code: 'INVALID_INPUT' });
    }
    await changeNote(action, input.id, userId, userId);
  } else if (action !== 'list') {
    throw new EndpointError('Unknown action.', { code: 'INVALID_INPUT' });
  }
  return { notes: await listNotes(userId, userId), stats: await getStats(userId, userId) };
}
