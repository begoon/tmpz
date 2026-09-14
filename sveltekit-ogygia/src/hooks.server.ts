import { handle as ogygiaHandle } from 'ogygia/server';

// Serves the signed endpoint that `render: 'deferred'` (server) islands fetch their HTML from.
// Everything else falls through to SvelteKit's normal request handling.
export const handle = ogygiaHandle();
