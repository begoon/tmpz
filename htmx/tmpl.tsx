import { type JSX } from "preact";

export const User = function ({ name, q }: { name: string, q: number }) {
  console.log({ name, q }); 
  return (
    <div>
      <h1 hx-get={`/tsx?q=${q}`} hx-trigger="click" hx-swap="outerHTML">user: {name}</h1>
      {q > 0 ? <output id="tracker" hx-swap-oob="beforeend">, {q}</output> : null}
      {q > 5 ? <output id="error" hx-swap-oob="innerHTML">{q}</output> : null}
    </div>
  )
};

export const UserDetails = ({ initial } = {initial: "default" }) => (
  <>
    <h1 className="text-4xl">details</h1>
    <div className="text-yellow-500">
      <User name={initial} q={0} />
    </div>
  </>
);

export const Application = function (child: JSX.Element) {
  return (
    <html>
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>htmx/tsx</title>
        <script src="https://unpkg.com/htmx.org"></script>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
      </head>
      <body>
        {child}
        <output id="tracker">-</output>
        <output id="error" className="fixed top-0 right-0 bg-red-500 text-white text-4xl"></output>
      </body>
    </html>
  )
}
