import { table, integer, text, index } from 'sdk/db';

export const notes = table('notes', {
  // A Telegram message ID is unique within its chat. Stable IDs deduplicate retries.
  id: text('id').primaryKey(),
  chatId: integer('chat_id').notNull(),
  userId: integer('user_id').notNull(),
  body: text('body').notNull(),
  done: integer('done').notNull().default(0),
  createdAt: integer('created_at').notNull(),
}, (t) => ({ owner: index('notes_owner').on(t.chatId, t.userId) }));

export const files = table('files', {
  id: text('id').primaryKey(),
  chatId: integer('chat_id').notNull(),
  userId: integer('user_id').notNull(),
  fileId: text('file_id').notNull(),
  fileUniqueId: text('file_unique_id').notNull(),
  name: text('name').notNull(),
  mimeType: text('mime_type'),
  size: integer('size'),
  createdAt: integer('created_at').notNull(),
}, (t) => ({ owner: index('files_owner').on(t.chatId, t.userId) }));
