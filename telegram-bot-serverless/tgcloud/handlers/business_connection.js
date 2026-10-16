import { saveConnection } from '../lib/secretary.js';

// Telegram sends this when an account connects, changes rights, or disconnects.
export default async function (connection) {
  await saveConnection(connection);
}
