import { db } from 'sdk';

// SDK raw SQL uses bound parameters, never interpolated user text.
const owner = (chatId, userId) => ({ ':chat': chatId, ':user': userId });

export async function addNote(message, body) {
  const id = `${message.chat.id}:${message.message_id}`;
  await db.run(`INSERT INTO notes (id, chat_id, user_id, body, done, created_at)
    VALUES (:id, :chat, :user, :body, 0, :created)
    ON CONFLICT(id) DO NOTHING`, {
    ...owner(message.chat.id, message.from.id), ':id': id,
    ':body': body, ':created': message.date ?? Math.floor(Date.now() / 1000),
  });
  return id;
}

export function listNotes(chatId, userId) {
  return db.all(`SELECT * FROM notes WHERE chat_id = :chat AND user_id = :user
    ORDER BY created_at DESC, id DESC LIMIT 10`, owner(chatId, userId));
}

export function getStats(chatId, userId) {
  return db.get(`SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS completed
    FROM notes WHERE chat_id = :chat AND user_id = :user`, owner(chatId, userId));
}

export async function changeNote(action, id, chatId, userId) {
  const params = { ...owner(chatId, userId), ':id': id };
  // Ownership is part of the write itself, including for forged callback payloads.
  if (action === 'delete') {
    return db.run('DELETE FROM notes WHERE id = :id AND chat_id = :chat AND user_id = :user', params);
  }
  if (action !== 'done' && action !== 'open') throw new Error('Unknown note action');
  return db.run(`UPDATE notes SET done = :done
    WHERE id = :id AND chat_id = :chat AND user_id = :user`, {
    ...params, ':done': action === 'done' ? 1 : 0,
  });
}
