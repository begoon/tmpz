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
