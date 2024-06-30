import process from "node:process";
import { handler } from "./handler.ts";

const env = process.env;

const AWS_LAMBDA_RUNTIME_API = env.AWS_LAMBDA_RUNTIME_API || "?";
console.log("AWS_LAMBDA_RUNTIME_API", AWS_LAMBDA_RUNTIME_API);

const runtime = `http://${AWS_LAMBDA_RUNTIME_API}/2018-06-01/runtime/invocation`;

while (true) {
    const event = await fetch(runtime + "/next");

    const REQUEST_ID = event.headers.get("Lambda-Runtime-Aws-Request-Id");
    console.log("REQUEST_ID", REQUEST_ID);

    const result = await handler(event);

    await fetch(runtime + `/${REQUEST_ID}/response`, {
        method: "POST",
        body: result,
    });
}
