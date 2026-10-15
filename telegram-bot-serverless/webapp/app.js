const tg = window.Telegram?.WebApp;
const form = document.querySelector('#add-form');
const input = document.querySelector('#note-body');
const status = document.querySelector('#status');
const list = document.querySelector('#notes');
let busy = false;
let pendingAdd;

function call(input) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('The request timed out. Please try again.')), 20000);
    tg.Serverless.call('notes', input, (error, result) => {
      clearTimeout(timer);
      error ? reject(error) : resolve(result);
    });
  });
}

function render(data) {
  document.querySelector('#open-count').textContent = data.stats.total - data.stats.completed;
  document.querySelector('#done-count').textContent = data.stats.completed;
  document.querySelector('#total-count').textContent = data.stats.total;
  list.replaceChildren();
  for (const note of data.notes) {
    const li = document.createElement('li');
    li.classList.toggle('completed', Boolean(note.done));
    const toggle = document.createElement('button');
    toggle.className = 'toggle';
    toggle.textContent = note.done ? '✓' : '○';
    toggle.setAttribute('aria-label', `${note.done ? 'Reopen' : 'Complete'} note: ${note.body}`);
    toggle.addEventListener('click', () => perform({ action: note.done ? 'open' : 'done', id: note.id }));
    const text = document.createElement('span');
    text.className = 'note-text';
    text.textContent = note.body;
    const remove = document.createElement('button');
    remove.className = 'delete';
    remove.textContent = 'Delete';
    remove.setAttribute('aria-label', `Delete note: ${note.body}`);
    remove.addEventListener('click', () => {
      const execute = (confirmed) => { if (confirmed) perform({ action: 'delete', id: note.id }); };
      if (tg.showConfirm) tg.showConfirm('Delete this note?', execute);
      else execute(window.confirm('Delete this note?'));
    });
    li.append(toggle, text, remove);
    list.append(li);
  }
  document.querySelector('#empty').hidden = data.notes.length > 0;
}

async function perform(payload) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('button').forEach(button => { button.disabled = true; });
  status.className = '';
  status.textContent = payload.action === 'list' ? 'Loading…' : 'Saving…';
  try {
    const result = await call(payload);
    render(result);
    if (payload.action === 'add') {
      if (input.value.trim() === payload.body) input.value = '';
      pendingAdd = undefined;
      updateCount();
    }
    status.textContent = '';
  } catch (error) {
    status.className = 'error';
    status.textContent = error.message || 'Could not load your notes. Try again.';
  } finally {
    busy = false;
    document.querySelectorAll('button').forEach(button => { button.disabled = false; });
  }
}

function updateCount() { document.querySelector('#char-count').textContent = `${input.value.length} / 200`; }
input.addEventListener('input', updateCount);
form.addEventListener('submit', event => {
  event.preventDefault();
  const body = input.value.trim();
  if (!body || busy) return;
  // Keep the same ID after a timeout: a retry must not insert a duplicate note.
  if (pendingAdd?.body !== body) pendingAdd = { action: 'add', body, requestId: crypto.randomUUID().replaceAll('-', '') };
  perform(pendingAdd);
});
document.querySelector('#refresh').addEventListener('click', () => perform({ action: 'list' }));

if (!tg?.initData || !tg?.Serverless?.call) {
  status.textContent = 'Open this app using the My notes menu in the Telegram bot. If you are already in Telegram, update your app and reopen it.';
  document.querySelectorAll('button, textarea').forEach(element => { element.disabled = true; });
} else {
  tg.ready();
  tg.expand();
  perform({ action: 'list' });
}
