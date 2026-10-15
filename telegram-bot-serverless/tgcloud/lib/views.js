import { listNotes, getStats } from './notes.js';

export const HELP = `Serverless notes bot

/add Buy milk — save a note (up to 200 characters)
/notes — show your 10 newest notes with action buttons
/stats — count your saved and completed notes
/app — open the Mini App in our private chat
/help — show this help

Notes are personal to you within this chat. In groups, your replies are visible to the group. Data is stored in Telegram's built-in database.`;

export async function notesView(chatId, userId) {
  const rows = await listNotes(chatId, userId);
  return {
    text: rows.length
      ? `Your newest notes:\n\n${rows.map((n, i) => `${i + 1}. ${n.done ? '✓' : '○'} ${n.body}`).join('\n')}`
      : 'No notes yet. Try /add Buy milk',
    reply_markup: { inline_keyboard: [
      ...rows.map((n, i) => [
        { text: `${i + 1}. ${n.done ? 'Reopen' : 'Complete'}`, callback_data: `note:${n.done ? 'open' : 'done'}:${n.id}` },
        { text: `${i + 1}. Delete`, callback_data: `note:delete:${n.id}` },
      ]),
      [{ text: 'Refresh', callback_data: 'notes' }, { text: 'Stats', callback_data: 'stats' }],
    ] },
  };
}

export async function statsView(chatId, userId) {
  const { total, completed } = await getStats(chatId, userId);
  return {
    text: `Your notes in this chat: ${total}\nCompleted: ${completed}\nOpen: ${total - completed}`,
    reply_markup: { inline_keyboard: [[{ text: 'My notes', callback_data: 'notes' }]] },
  };
}
