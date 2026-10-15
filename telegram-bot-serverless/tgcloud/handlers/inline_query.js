import { api } from 'sdk';
import { searchPrivateNotes } from '../lib/notes.js';

export default async function (query) {
  const rawOffset = query.offset ?? '';
  const offset = rawOffset === '' ? 0 : Number(rawOffset);
  const validOffset = /^\d{0,7}$/.test(rawOffset) && Number.isSafeInteger(offset) && offset <= 1000000;
  const userId = query.from?.id;
  const rows = validOffset && Number.isSafeInteger(userId) && userId > 0
    ? await searchPrivateNotes(userId, (query.query ?? '').trim(), offset)
    : [];

  await api.answerInlineQuery({
    inline_query_id: query.id,
    // Private notes must never be reused as results for another user.
    is_personal: true,
    cache_time: 0,
    next_offset: rows.length > 20 ? String(offset + 20) : '',
    button: { text: 'Manage your notes', start_parameter: 'inline_notes' },
    results: rows.slice(0, 20).map(note => ({
      type: 'article',
      id: note.id,
      title: Array.from(note.body.replace(/\s+/g, ' ')).slice(0, 80).join(''),
      description: `${note.done ? 'Completed' : 'To do'} · Tap to send this note to the current chat`,
      input_message_content: {
        message_text: note.body,
        link_preview_options: { is_disabled: true },
      },
      // Shared messages contain text only, without owner-only mutation buttons.
    })),
  });
}
