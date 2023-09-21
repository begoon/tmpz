import { Hono } from "hono";
import { serveStatic } from 'hono/bun';
import { html } from 'hono/html';

const app = new Hono();

interface MeData {
    state: string
}

app.use("/public/*", serveStatic({ root: "./" }));

const Layout = (data: MeData) => html`
  <html>
    <head>
      <link rel="stylesheet" href="/public/styles.css" />
      <meta name="view-transition" content="same-origin" />
    </head>
    <body>
      <h1>@@@</h1>
      <h1 class="text-red-500">[${data.state}].</h1>
    </body>
  </html>
`

app.get('/me', (c) => {
    const data = {
        state: 'at home'
    }
  return c.html(Layout(data))
})

export default app;
