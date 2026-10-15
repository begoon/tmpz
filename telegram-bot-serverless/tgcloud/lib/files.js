import { db } from 'sdk';

const owner = (chatId, userId) => ({ ':chat': chatId, ':user': userId });

export async function saveFile(message) {
  const document = message.document;
  const id = `${message.chat.id}:${message.message_id}`;
  await db.run(`INSERT INTO files
    (id, chat_id, user_id, file_id, file_unique_id, name, mime_type, size, created_at)
    VALUES (:id, :chat, :user, :file, :unique, :name, :mime, :size, :created)
    ON CONFLICT(id) DO NOTHING`, {
    ...owner(message.chat.id, message.from.id), ':id': id,
    ':file': document.file_id, ':unique': document.file_unique_id,
    ':name': (document.file_name || 'document').slice(0, 255),
    ':mime': document.mime_type ?? null, ':size': document.file_size ?? null,
    ':created': message.date ?? Math.floor(Date.now() / 1000),
  });
  return id;
}

export function listFiles(chatId, userId) {
  return db.all(`SELECT id, name, size FROM files
    WHERE chat_id = :chat AND user_id = :user
    ORDER BY created_at DESC, id DESC LIMIT 10`, owner(chatId, userId));
}

export function getFile(id, chatId, userId) {
  return db.get('SELECT * FROM files WHERE id = :id AND chat_id = :chat AND user_id = :user', {
    ...owner(chatId, userId), ':id': id,
  });
}

export function deleteFile(id, chatId, userId) {
  return db.run('DELETE FROM files WHERE id = :id AND chat_id = :chat AND user_id = :user', {
    ...owner(chatId, userId), ':id': id,
  });
}

export async function filesView(chatId, userId) {
  const rows = await listFiles(chatId, userId);
  return {
    text: rows.length ? `Your newest files:\n\n${rows.map((file, i) =>
      `${i + 1}. ${file.name.replace(/\s+/g, ' ').slice(0, 160)} (${file.size == null ? 'unknown size' : `${file.size} bytes`})`
    ).join('\n')}` : 'No files yet. Attach a document to a message in our private chat.',
    reply_markup: { inline_keyboard: [
      ...rows.map((file, i) => [
        { text: `${i + 1}. Download`, callback_data: `file:get:${file.id}` },
        { text: `${i + 1}. Remove`, callback_data: `file:delete:${file.id}` },
      ]),
      [{ text: 'Refresh files', callback_data: 'files' }],
    ] },
  };
}
