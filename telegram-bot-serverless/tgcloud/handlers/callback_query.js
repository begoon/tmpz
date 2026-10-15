import { api } from 'sdk';
import { changeNote } from '../lib/notes.js';
import { notesView, statsView } from '../lib/views.js';
import { getFile, deleteFile, filesView } from '../lib/files.js';

export default async function (query) {
  // Acknowledge promptly so the client's button spinner stops, even on invalid input.
  await api.answerCallbackQuery({ callback_query_id: query.id });
  if (!query.from || !query.message?.chat || query.message.date === 0) return;
  const chatId = query.message.chat.id;
  const userId = query.from.id;
  const fileAction = /^file:(get|delete):(-?\d+:\d+)$/.exec(query.data ?? '');
  if (fileAction || query.data === 'files') {
    if (fileAction?.[1] === 'get') {
      const file = await getFile(fileAction[2], chatId, userId);
      if (!file) {
        await api.sendMessage({ chat_id: chatId, text: 'File not found. It may have been removed, or belong to someone else.' });
      } else {
        await api.sendDocument({ chat_id: chatId, document: file.file_id });
      }
      return;
    }
    if (fileAction) await deleteFile(fileAction[2], chatId, userId);
    await api.sendMessage({ chat_id: chatId, ...await filesView(chatId, userId) });
    return;
  }
  const match = /^note:(done|open|delete):(-?\d+:\d+|w:\d+:[a-f0-9]{32})$/.exec(query.data ?? '');
  if (match) {
    await changeNote(match[1], match[2], chatId, userId);
  } else if (query.data !== 'notes' && query.data !== 'stats') {
    return;
  }
  const view = query.data === 'stats'
    ? await statsView(chatId, userId)
    : await notesView(chatId, userId);
  // Fresh replies avoid overwriting another user's shared group-chat panel and
  // avoid stale concurrent edits. Complete/reopen are explicit, retry-safe states.
  await api.sendMessage({ chat_id: chatId, ...view });
}
