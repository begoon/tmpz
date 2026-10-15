import { api } from 'sdk';
import { addNote } from '../lib/notes.js';
import { HELP, notesView, statsView } from '../lib/views.js';

// Telegram passes update.message, not the whole update envelope.
export default async function (message) {
  if (!message.from || message.from.is_bot || !message.chat || typeof message.text !== 'string') return;
  const match = /^\/([a-zA-Z0-9_]+)(?:@([a-zA-Z0-9_]+))?(?:\s+([\s\S]*))?$/.exec(message.text.trim());
  if (!match) return;
  if (match[2]) {
    const me = await api.getMe();
    if (match[2].toLowerCase() !== me.username.toLowerCase()) return;
  }
  const command = match[1].toLowerCase();
  const chatId = message.chat.id;
  let view;
  switch (command) {
    case 'start':
    case 'help':
      view = { text: HELP, reply_markup: { inline_keyboard: [[
        { text: 'My notes', callback_data: 'notes' }, { text: 'Stats', callback_data: 'stats' },
      ]] } };
      break;
    case 'add': {
      const body = (match[3] ?? '').trim();
      if (!body || body.length > 200) {
        view = { text: 'Use /add followed by 1–200 characters. Example: /add Buy milk' };
        break;
      }
      await addNote(message, body);
      view = { text: 'Note saved.', reply_markup: { inline_keyboard: [[{ text: 'My notes', callback_data: 'notes' }]] } };
      break;
    }
    case 'notes': view = await notesView(chatId, message.from.id); break;
    case 'stats': view = await statsView(chatId, message.from.id); break;
    default: view = { text: 'Unknown command. Use /help for examples.' };
  }
  await api.sendMessage({ chat_id: chatId, ...view });
}
