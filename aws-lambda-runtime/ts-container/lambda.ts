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

// https://docs.aws.amazon.com/lambda/latest/dg/services-apigateway.html

type APIGatewayProxyEvent = {
    queryStringParameters?: Record<string, string>;
    requestContext: { http: { method: string; path: string } };
    body?: string;
};

async function handler(event: APIGatewayProxyEvent) {
    const { method, path } = event.requestContext.http;

    const echo = { method, path, status: 200 };
    if (event.queryStringParameters) {
        echo.queryStringParameters = event.queryStringParameters;
        echo.status = event.queryStringParameters.status || 200;
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
