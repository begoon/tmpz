import process from "node:process";

const env = process.env;

const AWS_LAMBDA_RUNTIME_API = env.AWS_LAMBDA_RUNTIME_API || "?";
console.log("AWS_LAMBDA_RUNTIME_API", AWS_LAMBDA_RUNTIME_API);

const API = `http://${AWS_LAMBDA_RUNTIME_API}/2018-06-01/runtime/invocation`;

while (true) {
    const event = await fetch(API + "/next");

    const REQUEST_ID = event.headers.get("Lambda-Runtime-Aws-Request-Id");
    console.log("REQUEST_ID", REQUEST_ID);

    const response = await handler(await event.json());

    await fetch(API + `/${REQUEST_ID}/response`, {
        method: "POST",
        body: JSON.stringify(response),
    });
}

// This is a simplified version of the AWS Lambda runtime API.
// The full specification can be found at:
// https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html

type APIGatewayProxyEvent = {
    queryStringParameters?: Record<string, string>;
    requestContext: { http: { method: string; path: string } };
    body?: string;
};

async function handler(event: APIGatewayProxyEvent) {
    const { method, path } = event.requestContext.http;

    const echo = {
        method,
        path,
        status: "200",
        queryStringParameters: {},
        runtime: runtime(),
        env: {
            ...env,
            AWS_SESSION_TOKEN: "REDACTED",
            AWS_SECRET_ACCESS_KEY: "REDACTED",
        },
        format: "",
        body: "",
    };

    if (event.queryStringParameters) {
        echo.queryStringParameters = event.queryStringParameters;
        echo.status = event.queryStringParameters.status || "200";
    }

    if (event.body) {
        try {
            echo.body = JSON.parse(event.body);
            echo.format = "json";
        } catch {
            echo.body = event.body;
            echo.format = "text";
        }
    }

    return {
        statusCode: echo.status,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(echo),
    };
}

function runtime() {
    return typeof Deno !== "undefined"
        ? "deno " + Deno.version.deno
        : // @ts-ignore deno-ts(2867)
        typeof Bun !== "undefined"
        ? // @ts-ignore deno-ts(2867)
          "bun " + Bun.version
        : "maybe node";
}
