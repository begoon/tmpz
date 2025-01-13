Bun.serve({
    port: 8000,
    async fetch(req) {
        return new Response(
            async function* () {
                yield html;
                for (let i = 0; i < 10; i++) {
                    await new Promise((r) => setTimeout(r, 400));
                    yield `<script>id.innerText = ${i} + 1;</script>`;
                }
                yield "<script>id.innerText = 'DONE';</script>";
            },
            { headers: { "Content-Type": "text/html" } }
        );
    },
});

const html = `
<h1 id="counter" style="display: grid; place-items: center; min-height: 100vh; font-size: 20em;">
    0
</h1>
<script>const id = document.getElementById("counter");</script>
`;
