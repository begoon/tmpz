import van from "https://deno.land/x/minivan@0.6.3/src/van-plate.js";

const { a, body, li, p, ul, style } = van.tags;

const port = 8000;

console.log(`running http://localhost:${port}/`);
Deno.serve(
    { port },
    (req) =>
        new Response(
            van.html(
                body(
                    p("Your user-agent is: ", req.headers.get("user-agent") ?? "Unknown"),
                    p("👋 Hello"),
                    ul(li("🗺️ World"), li(a({ href: "https://vanjs.org/" }, "🍦 VanJS")))
                ),
                style(`
                    body {
                        font-family: sans-serif;
                        background-color: #f0f0f0;
                        color: #333;
                    }
                    a {
                        color: #007bff;
                        text-decoration: none;
                    }
                    a:hover {
                        text-decoration: underline;
                    }
                `)
            ),
            {
                status: 200,
                headers: { "content-type": "text/html; charset=utf-8" },
            }
        )
);
