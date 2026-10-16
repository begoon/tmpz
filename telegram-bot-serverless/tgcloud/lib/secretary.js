import { db } from 'sdk';

export const NOTICE = 'The message may be recorded for the AI training purposes :-)';

export function matchesSender(user) {
  return [user?.first_name, user?.last_name]
    .some(name => typeof name === 'string' && name.toLowerCase().includes('evgeny'));
}

export async function saveConnection(connection) {
  await db.run(`INSERT INTO business_connections (id, owner_id, enabled, can_reply)
    VALUES (:id, :owner, :enabled, :reply)
    ON CONFLICT(id) DO UPDATE SET owner_id = excluded.owner_id,
      enabled = excluded.enabled, can_reply = excluded.can_reply`, {
    ':id': connection.id, ':owner': connection.user.id,
    ':enabled': connection.is_enabled ? 1 : 0,
    ':reply': connection.rights?.can_reply ? 1 : 0,
  });
}

export async function claimReply(message) {
  const result = await db.run(`INSERT INTO secretary_replies (id, created_at)
    VALUES (:id, :created) ON CONFLICT(id) DO NOTHING`, {
    ':id': JSON.stringify([message.business_connection_id, message.chat.id, message.message_id]),
    ':created': Math.floor(Date.now() / 1000),
  });
  return result.rowsAffected === 1;
}
