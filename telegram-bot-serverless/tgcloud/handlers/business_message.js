import { api } from 'sdk';
import { NOTICE, matchesSender, saveConnection, claimReply } from '../lib/secretary.js';

export default async function (message) {
  if (!message.business_connection_id || message.chat?.type !== 'private'
      || !message.from || message.from.is_bot || message.sender_business_bot
      || !Number.isSafeInteger(message.message_id) || message.message_id <= 0
      || !matchesSender(message.from)) return;

  // Fetch current rights even if the connection predates our deployment or
  // a permission-change update is delayed. Fail closed on API errors.
  const connection = await api.getBusinessConnection({ business_connection_id: message.business_connection_id });
  await saveConnection(connection);
  if (!connection.is_enabled || !connection.rights?.can_reply
      || message.from.id === connection.user.id) return;

  // Incoming private messages have the sender's ID as the chat ID.
  if (message.chat.id !== message.from.id) return;
  if (typeof message.date !== 'number' || Date.now() / 1000 - message.date >= 86400) return;

  // Claim before sending: concurrent/retried updates cannot send two notices.
  // An ambiguous API failure can lose a notice; we do not risk sending it twice.
  if (!await claimReply(message)) return;
  await api.sendMessage({
    business_connection_id: connection.id,
    chat_id: message.chat.id,
    text: NOTICE,
    reply_parameters: { message_id: message.message_id },
  });
}
