import { GoogleAuth } from "google-auth-library";
import { join } from "path";
import util from "util";

const serviceURL = "http://localhost:9000";

const project = process.env.GCP_PROJECT;
const region = process.env.VERTEX_LOCATION;
const model = process.env.GEMINI_MODEL;

const port = Number.parseInt(process.env.PORT || "8000", 10);

// Function calling tools (OpenAPI-ish schema)
const tools = [
    {
        functionDeclarations: [
            {
                name: "getweather",
                description: "get weather for a given location",
                parameters: {
                    type: "object",
                    properties: {
                        location: { type: "string" },
                    },
                    required: ["location"],
                },
            },
        ],
    },
] as const;

const auth = new GoogleAuth({
    scopes: ["https://www.googleapis.com/auth/cloud-platform"],
});

function vertexBaseUrl(location: string) {
    if (location === "global") return "https://aiplatform.googleapis.com";
    return `https://${location}-aiplatform.googleapis.com`;
}

async function vertexGenerateContent({ contents, tools }: { contents: Contents[]; tools: any }) {
    const client = await auth.getClient();
    const accessTokenResponse: any = await client.getAccessToken();
    const accessToken = typeof accessTokenResponse === "string" ? accessTokenResponse : accessTokenResponse?.token;

    if (!accessToken) {
        throw new Error("Access token not found. Check ADC / GOOGLE_APPLICATION_CREDENTIALS.");
    }

    const base = vertexBaseUrl(region);

    // Note: the resource location must match (global vs region)
    const url = `${base}/v1/projects/${project}/locations/${region}/publishers/google/models/${model}:generateContent`;

    const response = await fetch(url, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ contents, tools }),
    });

    const text = await response.text();

    let response_json: any;
    try {
        response_json = JSON.parse(text);
    } catch {
        const snippet = text.slice(0, 400);
        throw new Error(`Vertex returned non-JSON (HTTP ${response.status}). First 400 chars:\n${snippet}`);
    }

    if (!response.ok) {
        throw new Error(`Vertex error HTTP ${response.status}: ${JSON.stringify(response_json)}`);
    }

    return response_json;
}

function firstPart(response: Record<string, any>) {
    return response?.candidates?.[0]?.content?.parts?.[0];
}

function sleep(ms: number) {
    return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

type Contents = {
    role: "user" | "model";
    parts: Array<
        | { text: string }
        | {
              functionCall: {
                  name: string;
                  args: Record<string, any>;
              };
          }
        | {
              functionResponse: {
                  name: string;
                  response: {
                      name: string;
                      content: {
                          jsonReturned: any;
                      };
                  };
              };
          }
    >;
};

function escapeHTML(s: unknown) {
    return String(s)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function asMessageText(data: string | Buffer) {
    if (typeof data === "string") return data;
    // Bun WS message may be Buffer/Uint8Array; Buffer is fine in Node compat.
    return Buffer.from(data).toString("utf8");
}

const PUBLIC_DIR = join(process.cwd(), "public");

async function serveStatic(req: Request): Promise<Response | null> {
    const url = new URL(req.url);

    // map "/" -> "/index.html"
    let pathname = url.pathname === "/" ? "/index.html" : url.pathname;

    // prevent path traversal
    pathname = pathname.replaceAll("\\", "/");
    if (pathname.includes("..")) return new Response("Not found", { status: 404 });

    const filePath = join(PUBLIC_DIR, pathname);
    const file = Bun.file(filePath);

    if (!(await file.exists())) return null;

    return new Response(file, { headers: { "Cache-Control": "no-cache" } });
}

// Per-socket conversation history
type SocketState = {
    contents: Contents[];
};

Bun.serve<SocketState>({
    port,
    // Upgrade HTTP -> WS for /sendMessage
    fetch: async (req, server) => {
        const url = new URL(req.url);

        if (url.pathname === "/sendMessage") {
            const ok = server.upgrade(req, { data: { contents: [] } });
            return ok ? new Response(null) : new Response("WebSocket upgrade failed", { status: 400 });
        }

        const staticResponse = await serveStatic(req);
        if (staticResponse) return staticResponse;

        return new Response("Not found", { status: 404 });
    },

    websocket: {
        open(ws) {
            // nothing special; ws.data.contents already initialized
            console.log("websocket opened");
        },

        async message(ws, raw) {
            const message = asMessageText(raw);

            let question: string;
            try {
                question = JSON.parse(message)?.message;
            } catch {
                ws.send(
                    `` +
                        `<div hx-swap-oob="beforeend:#toupdate"><div>` +
                        escapeHTML("Invalid JSON message") +
                        `</div></div>`
                );
                return;
            }

            console.log("websocket message:", question);

            ws.send(`<div hx-swap-oob="beforeend:#toupdate"><div>${escapeHTML(question)}</div></div>`);

            await sleep(300);

            const now = "fromGemini-" + Date.now();
            ws.send(`<div hx-swap-oob="beforeend:#toupdate"><div id="${now}">thinking...</div></div>`);

            const contents = ws.data.contents;
            contents.push({ role: "user", parts: [{ text: question }] });

            let response1;
            try {
                response1 = await vertexGenerateContent({ contents, tools });
            } catch (error) {
                const e = error as Error;
                ws.send(
                    `` +
                        `<div id="${now}" hx-swap-oob="true" hx-swap="outerHTML">` +
                        `Model call failed: ${escapeHTML(e.message || e)}` +
                        `</div>`
                );
                return;
            }

            const part1 = firstPart(response1);
            const functionCall = part1?.functionCall;

            // Plain text answer
            if (!functionCall) {
                const text = part1?.text ?? "(no text returned)";
                ws.send(`<div id="${now}" hx-swap-oob="true" hx-swap="outerHTML">${escapeHTML(text)}</div>`);
                contents.push({ role: "model", parts: [{ text }] });
                return;
            }

            console.log("gemini wants to call:", functionCall.name, "args:", functionCall.args);

            // Push model functionCall into history
            contents.push({
                role: "model",
                parts: [{ functionCall }],
            });

            // Execute tool
            let serviceResult: Record<string, any>;
            try {
                const url = new URL(`${serviceURL}/${functionCall.name}`);
                url.searchParams.set("location", functionCall.args.location);

                const response = await fetch(url, {
                    method: "GET",
                    headers: { Accept: "application/json" },
                });

                if (!response.ok) {
                    let errorBody: any;
                    try {
                        errorBody = await response.json();
                    } catch {
                        errorBody = await response.text();
                    }
                    throw { response: { data: errorBody }, status: response.status };
                }

                serviceResult = await response.json();
            } catch (error) {
                const e: any = error;
                serviceResult = e?.response?.data ?? { error: String(e?.message || e) };
            }

            console.log("function returned:", util.inspect(serviceResult, { depth: null }));

            // push functionResponse into history
            contents.push({
                role: "user",
                parts: [
                    {
                        functionResponse: {
                            name: functionCall.name,
                            response: {
                                name: functionCall.name,
                                content: { jsonReturned: serviceResult },
                            },
                        },
                    },
                ],
            });

            // Ask model again with function result
            let response2: any;
            try {
                response2 = await vertexGenerateContent({ contents, tools });
            } catch (e) {
                const error = e as Error;
                ws.send(
                    `<div id="${now}" hx-swap-oob="true" hx-swap="outerHTML">` +
                        `Model call failed (after function): ${escapeHTML(error.message || error)}` +
                        `</div>`
                );
                return;
            }

            const part2 = firstPart(response2);
            const answer = part2?.text ?? "(no text returned)";
            contents.push({ role: "model", parts: [{ text: answer }] });

            ws.send(`<div id="${now}" hx-swap-oob="true" hx-swap="outerHTML">${escapeHTML(answer)}</div>`);
        },

        close() {
            console.log("websocket was closed");
        },
    },
});

console.log(`frontend listening on port ${port}`);
