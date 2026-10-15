import { api } from 'sdk';
import { addNote } from '../lib/notes.js';
import { HELP, notesView, statsView } from '../lib/views.js';
import { saveFile, filesView } from '../lib/files.js';

// Telegram passes update.message, not the whole update envelope.
export default async function (message) {
  if (!message.from || message.from.is_bot || !message.chat) return;
  if (message.document) {
    await saveFile(message);
    await api.sendMessage({
      chat_id: message.chat.id,
      text: 'File saved. Use /files to download it later or remove it from your list.',
      reply_markup: { inline_keyboard: [[{ text: 'My files', callback_data: 'files' }]] },
    });
    return;
  }
  if (typeof message.text !== 'string') return;
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
    case 'files': view = await filesView(chatId, message.from.id); break;
    case 'share': {
      const me = await api.getMe();
      view = me.supports_inline_queries ? {
        text: 'Choose a chat, search your private notes, then tap a result to send it. The selected note will be visible in that chat.',
        reply_markup: { inline_keyboard: [[{ text: 'Choose chat and share a note', switch_inline_query: '' }]] },
      } : { text: 'Inline sharing is not enabled yet. The bot owner needs to enable /setinline in BotFather.' };
      break;
    }
    case 'app': {
      if (message.chat.type !== 'private') {
        view = { text: 'Open our private chat and use /app to see your personal notes.' };
        break;
      }
      const menu = await api.getChatMenuButton();
      view = menu.web_app ? {
        text: 'Open your notes app:',
        reply_markup: { inline_keyboard: [[{ text: 'Open notes', web_app: menu.web_app }]] },
      } : { text: 'The Mini App has not been configured yet.' };
      break;
    }
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
