import { type JSX } from "preact";

export const User = ({ name }: { name: string }) => (
  <div>
    <h1  hx-get="/tsx?q=1" hx-trigger="click">user: {name}</h1>
  </div>
);

export const UserDetails = ({ initial } = {initial: "default" }) => (
  <>
    <h1 className="text-4xl">details</h1>
    <div className="text-yellow-500">
      <User name={initial}/>
    </div>
  </>
);

export const App = function (child: JSX.Element) {
  return (
    <html>
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>htmx</title>
        <script src="https://unpkg.com/htmx.org"></script>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
      </head>
      <body>
        <UserDetails initial="initial/name" />
        <hr />
        {child}
      </body>
    </html>
  )
}
