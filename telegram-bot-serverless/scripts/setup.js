// Local-only utility. The deployed handlers use sdk.api and need no token.
const commands = [
  { command: 'start', description: 'Welcome and examples' },
  { command: 'help', description: 'Show available commands' },
  { command: 'add', description: 'Save a note: /add Buy milk' },
  { command: 'notes', description: 'List notes and action buttons' },
  { command: 'stats', description: 'Count saved and completed notes' },
  { command: 'app', description: 'Open the notes Mini App' },
];

async function call(method, params = {}) {
  const response = await fetch(`https://api.telegram.org/bot${process.env.BOT_TOKEN}/${method}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params), signal: AbortSignal.timeout(15000),
  });
  const body = await response.json();
  if (!response.ok || !body.ok) throw new Error(`Bot API ${method} failed (${body.error_code ?? response.status})`);
  return body.result;
}

try {
  if (!process.env.BOT_TOKEN) throw new Error('Set BOT_TOKEN in .env first');
  const me = await call('getMe');
  if (process.argv.includes('--check')) {
    console.log(`Bot token works: @${me.username}`);
  } else {
    const appId = /^app(\d+):/.exec(process.env.TGCLOUD_TOKEN ?? '')?.[1];
    const appUrl = process.env.MINI_APP_URL || (appId ? `https://app${appId}.tgcloud.ai/` : null);
    if (!appUrl || new URL(appUrl).protocol !== 'https:') {
      throw new Error('Set BOT_TOKEN and TGCLOUD_TOKEN (or MINI_APP_URL) in .env first');
    }
    await call('setMyCommands', { commands });
    await call('setChatMenuButton', { menu_button: {
      type: 'web_app', text: 'My notes', web_app: { url: appUrl },
    } });
    console.log(`Registered commands for @${me.username}`);
    console.log(`Configured Mini App menu: ${appUrl}`);
  }
} catch (error) {
  // Do not print fetch error objects: their nested URL may contain the token.
  console.error(error.message.startsWith('Bot API') || error.message.startsWith('Set BOT_TOKEN')
    ? error.message : 'Bot API request failed. Check connectivity and BOT_TOKEN.');
  process.exitCode = 1;
}
