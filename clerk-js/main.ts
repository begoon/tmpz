import { createClerkClient, verifyToken } from "@clerk/backend";
import { serve } from "bun";
import process from "process";

const { CLERK_SECRET_KEY } = process.env;

if (!CLERK_SECRET_KEY) throw new Error("missing CLERK_SECRET_KEY");

const clerkClient = createClerkClient({
    secretKey: process.env.CLERK_SECRET_KEY,
    publishableKey: process.env.PUBLIC_CLERK_PUBLISHABLE_KEY,
});

serve({
    port: 3000,
    fetch: async (req) => {
        const url = new URL(req.url);
        // http://localhost:3000/.well-known/appspecific/com.chrome.devtools.json
        if (url.pathname === "/.well-known/appspecific/com.chrome.devtools.json") {
            return new Response(JSON.stringify({ name: "com.chrome.devtools" }));
        }
        // favicon.ico
        if (url.pathname === "/favicon.ico") {
            return new Response(null, { status: 204 });
        }
        console.log(`-> ${url.pathname}`);

        const sessionToken = await clerkClient.authenticateRequest(req);
        console.dir(sessionToken, { depth: Infinity });
        const { token } = sessionToken;
        if (token) {
            const data = await verifyToken(token, { secretKey: CLERK_SECRET_KEY });
            console.dir(data, { depth: Infinity });
            const user = await clerkClient.users.getUser(data.sub);
            console.dir(user, { depth: Infinity });
        }

        const filename = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
        const { PUBLIC_CLERK_PUBLISHABLE_KEY } = process.env;
        const html = (await Bun.file(filename).text()).replace(
            "PUBLIC_CLERK_PUBLISHABLE_KEY",
            PUBLIC_CLERK_PUBLISHABLE_KEY!
        );
        const contentType = filename.endsWith(".js") ? "application/javascript" : "text/html";
        return new Response(html, {
            headers: { "Content-Type": contentType },
        });
    },
});

console.log("server running on http://localhost:3000");
