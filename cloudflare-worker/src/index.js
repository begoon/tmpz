import html from './index.html';

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);

    if (pathname === '/health') {
      return Response.json({ status: 'ok' });
    }

    if (pathname === '/reset') {
      if (request.method !== 'POST') {
        return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'POST' } });
      }
      const origin = request.headers.get('Origin');
      if (origin && origin !== new URL(request.url).origin) {
        return new Response('Forbidden', { status: 403 });
      }
      try {
        if (!await env.FLAGS.getBooleanValue('reset-button', false)) {
          return new Response('Not Found', { status: 404, headers: { 'Cache-Control': 'no-store' } });
        }
        await env.COUNTER.delete('page-loads');
        return new Response(null, {
          status: 303,
          headers: { Location: '/', 'Cache-Control': 'no-store' },
        });
      } catch (error) {
        console.error('Counter reset failed', error);
        return new Response('Counter reset failed. Please try again.', {
          status: 503,
          headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' },
        });
      }
    }

    if (pathname === '/') {
      if (request.method !== 'GET' && request.method !== 'HEAD') {
        return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'GET, HEAD' } });
      }
      const headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-store',
      };
      if (request.method === 'HEAD') return new Response(null, { headers });
      try {
        const resetEnabled = await env.FLAGS.getBooleanValue('reset-button', false);
        // KV increments are best-effort: concurrent requests may read the same value.
        const count = Number(await env.COUNTER.get('page-loads') || 0) + 1;
        await env.COUNTER.put('page-loads', String(count));
        const page = html.replace('{{count}}', String(count)).replace(
          '{{resetButton}}',
          resetEnabled ? '<form action="/reset" method="post" style="display: inline"><button type="submit">Reset</button></form>' : '',
        );
        return new Response(page, { headers });
      } catch (error) {
        console.error('Counter update failed', error);
        return new Response('Counter unavailable. Please try again.', {
          status: 503,
          headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store' },
        });
      }
    }

    return new Response('Not Found', { status: 404 });
  },
};
